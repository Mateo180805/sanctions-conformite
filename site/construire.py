"""
Fabrication du site public (GitHub Pages).

Ce programme lit les données du dépôt et écrit des pages HTML toutes prêtes dans
le dossier _site/. Il ne télécharge rien et n'analyse rien : il met en page.

Il lit :
  - donnees/decisions.json      la base des décisions (une ligne par décision) ;
  - donnees/fiches/*/*.json     les fiches d'analyse (la fiche fait foi) ;
  - donnees/glossaire.json      le glossaire commun (page Lexique et lexique des fiches) ;
  - site/pages/*.html           les textes fixes (Méthode, Analyse) ;
  - site/textes/*.txt           les textes écrits par Matéo (introduction, À propos).

Il ne lit JAMAIS donnees/textes/ (le texte intégral des décisions) : certains textes
anonymisés laissent passer des noms. Le site s'appuie uniquement sur les fiches.

Garde-fous :
  - aucun nom de personne physique n'est affiché (voir nom_affiche) ;
  - si l'ACPR a anonymisé une décision mais que la fiche contient encore un nom,
    la fiche n'est PAS publiée, et le programme écrit une alerte dans _alertes.txt.
    La tâche GitHub publie quand même le site (sans la fiche) puis se met en rouge
    pour prévenir Matéo par e-mail.

Lancement :  python site/construire.py      (puis ouvrir _site/index.html)
"""

import html
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "analyse"))
from fiches import CATEGORIES, date_en_clair, lexique  # noqa: E402  (on réutilise le code des fiches)

DONNEES = RACINE / "donnees"
ICI = Path(__file__).resolve().parent
SORTIE = RACINE / "_site"
ALERTES = RACINE / "_alertes.txt"
LIEN_DEPOT = "https://github.com/Mateo180805/sanctions-conformite"
NOM_SITE = "Sanctions Conformité"

MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août",
               "sept.", "oct.", "nov.", "déc."]

# Regroupement des types d'établissement pour le filtre de la base (question 4 du journal).
# La fiche garde le terme exact de la décision ; ce tableau ne sert qu'au filtre.
TYPES = {
    "banque": "Banque",
    "établissement de crédit": "Banque",
    "établissement de crédit spécialisé": "Banque",
    "établissement de paiement": "Paiement et monnaie électronique",
    "établissement de monnaie électronique": "Paiement et monnaie électronique",
    "prestataire de services de paiement (office des postes)": "Paiement et monnaie électronique",
    "assureur": "Assurance",
    "changeur manuel": "Change manuel",
    "intermédiaire en financement participatif": "Financement participatif",
}
NON_RENSEIGNE = "Non renseigné (fiche à venir)"

# Tranches de montant pour le filtre de la base.
TRANCHES = [
    ("0", "Sans sanction pécuniaire", lambda m: not m),
    ("1", "Moins de 100 000 €", lambda m: m and m < 100_000),
    ("2", "De 100 000 € à 1 million", lambda m: m and 100_000 <= m < 1_000_000),
    ("3", "De 1 à 10 millions", lambda m: m and 1_000_000 <= m < 10_000_000),
    ("4", "10 millions ou plus", lambda m: m and m >= 10_000_000),
]

# Mots cherchés dans l'en-tête officiel pour nommer la sanction quand il n'y a pas encore de fiche.
NATURES = [
    ("mise hors de cause", "mise hors de cause"),
    ("abandon des poursuites", "abandon des poursuites"),
    ("renvoi", "renvoi (instruction poursuivie)"),
    ("avertissement", "avertissement"),
    ("blâme", "blâme"),
    ("interdiction", "interdiction d'exercer"),
    ("radiation", "radiation"),
    ("retrait d", "retrait d'agrément"),
    ("pécuniaire", "sanction pécuniaire"),
    ("sanction financière", "sanction pécuniaire"),
]

ISSUES = [("retenu", "r", "retenu", "retenus"),
          ("retenu en partie", "p", "retenu en partie", "retenus en partie"),
          ("écarté", "e", "écarté", "écartés")]

alertes = []


# --------------------------------------------------------------------------
# Petits outils de mise en forme
# --------------------------------------------------------------------------

def e(x):
    """Échappe un texte pour l'insérer dans du HTML (évite qu'un « < » casse la page)."""
    return html.escape(str(x), quote=True)


def sans_accents(texte):
    """« Établissement » -> « etablissement » : sert à la recherche dans la base."""
    t = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def euros(n):
    """1200000 -> « 1 200 000 € » (espaces fines insécables)."""
    return f"{n:,}".replace(",", " ") + " €" if n else "—"


def date_courte(iso):
    if not iso:
        return "date non lue"
    a, m, j = iso.split("-")
    return f"{int(j)} {MOIS_COURTS[int(m) - 1]} {a}"


def majuscule(t):
    return t[:1].upper() + t[1:] if t else t


def pluriel(n, un, plusieurs):
    return f"{n} {un if n == 1 else plusieurs}"


def nom_affiche(d):
    """Nom d'établissement affiché pour une décision sans fiche.

    On retire les noms de personnes physiques (« et de M. X, son gérant »),
    le mot « société » en tête et les mentions « procédure n° ... ».
    """
    nom = (d.get("etablissement") or "").strip()
    if not nom or nom.startswith("anonymisé") or d.get("publication") == "anonymisée":
        return "Établissement anonymisé"
    if re.match(r"(M\.|Mme|Mlle|Monsieur|Madame)\s", nom):
        return "Personne physique (nom non affiché)"
    nom = re.split(r",?\s+(?:et\s+)?de\s+(?:M\.|Mme|Mlle)\s", nom)[0]
    nom = re.sub(r",\s*procédure n°.*$", "", nom)
    # « société AXA » -> « AXA » (seulement si le mot suivant commence par une majuscule)
    nom = re.sub(r"^(?:la )?société (?=[A-ZÀ-Ý])", "", nom)
    return majuscule(adoucir_capitales(nom.strip(" ,")))


# Sigles laissés en capitales quand un nom écrit TOUT EN CAPITALES est remis en minuscules.
SIGLES = {"SA", "SAS", "SARL", "AG", "EP", "BNP", "UBS", "AXA", "ACMN", "CREPA", "CNP", "SGP",
          "GFC", "BPA", "BRED", "MGEN", "BMW", "IARD", "LCL", "SFPMEI", "OPT-NC", "W-HA"}
PETITS_MOTS = {"DE", "DU", "DES", "LA", "LE", "LES", "ET", "EN", "OF", "D", "L", "AU", "AUX"}


def adoucir_capitales(nom):
    """« CAISSE DE CREDIT MUNICIPAL DE TOULON » -> « Caisse de Credit Municipal de Toulon ».

    Ne touche que les mots écrits entièrement en capitales ; les sigles connus restent tels quels.
    """
    def mot(m):
        w = m.group(0)
        if w in PETITS_MOTS and m.start() > 0:
            return w.lower()
        if w in SIGLES or len(w) < 2 or not w.isupper() or ("." in w and len(w) <= 4):
            return w
        return w[0] + w[1:].lower()
    return re.sub(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ.]*", mot, nom)


def nature_depuis_texte(texte):
    t = (texte or "").lower()
    trouves = []
    for mot, libelle in NATURES:
        if mot in t and libelle not in trouves:
            trouves.append(libelle)
    return trouves


def nature_courte(natures, montant):
    """Texte de la colonne « Sanction » : la sanction pécuniaire a sa propre colonne."""
    autres = [n for n in natures if n != "sanction pécuniaire"]
    if not autres:
        return "Sanction pécuniaire" if natures else "Voir la décision"
    return majuscule(", ".join(autres))


def lien_pages(pages, url_pdf):
    """[3, 13] -> « p. 3, 13 », chaque numéro ouvrant le PDF officiel à la bonne page."""
    if not pages:
        return ""
    liens = ", ".join(f'<a href="{e(url_pdf)}#page={p}">{p}</a>' for p in pages)
    return f' <span class="pages">p. {liens}</span>'


def paragraphes(texte):
    """Texte simple (lignes vides = nouveaux paragraphes) -> HTML ; les adresses web deviennent des liens."""
    blocs = [b.strip() for b in texte.strip().split("\n\n") if b.strip()]
    sortie = []
    for b in blocs:
        b = e(b).replace("\n", " ")
        b = re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', b)
        sortie.append(f"<p>{b}</p>")
    return "\n".join(sortie)


def texte_de_mateo(nom, consigne):
    """Lit site/textes/<nom>.txt. Tant qu'il est vide, affiche un emplacement réservé bien visible."""
    chemin = ICI / "textes" / f"{nom}.txt"
    contenu = chemin.read_text(encoding="utf-8") if chemin.exists() else ""
    lignes = [l for l in contenu.splitlines() if not l.startswith("#")]
    contenu = "\n".join(lignes).strip()
    if contenu:
        return paragraphes(contenu)
    return (f'<div class="reserve"><p><strong>Emplacement réservé.</strong> {e(consigne)}</p>'
            f'<p>À écrire dans le fichier <code>site/textes/{nom}.txt</code>.</p></div>')


def decompte(issues):
    """La petite frise des griefs : une barre par grief, pleine = retenu,
    hachurée = retenu en partie, vide = écarté."""
    if not issues:
        return ""
    n = {code: sum(1 for i in issues if i == nom) for nom, code, _, _ in ISSUES}
    marques = "".join(f'<i class="{code}"></i>' * n[code] for _, code, _, _ in ISSUES)
    return f'<span class="decompte" role="img" aria-label="{e(bilan(issues))}">{marques}</span>'


def bilan(issues):
    parts = []
    for nom, _, un, plusieurs in ISSUES:
        k = sum(1 for i in issues if i == nom)
        if k:
            parts.append(pluriel(k, un, plusieurs))
    return f"{pluriel(len(issues), 'grief', 'griefs')} : " + ", ".join(parts)


# --------------------------------------------------------------------------
# Lecture des données
# --------------------------------------------------------------------------

def charger():
    decisions = json.loads((DONNEES / "decisions.json").read_text(encoding="utf-8"))
    fiches = {}
    for chemin in sorted((DONNEES / "fiches").glob("*/*.json")):
        f = json.loads(chemin.read_text(encoding="utf-8"))
        fiches[f["id"]] = f
    glossaire = json.loads((DONNEES / "glossaire.json").read_text(encoding="utf-8"))
    collecte = json.loads((DONNEES / "derniere_collecte.json").read_text(encoding="utf-8"))
    return decisions, fiches, glossaire, collecte


def preparer(decisions, fiches):
    """Fabrique une ligne par décision avec tout ce dont les pages ont besoin."""
    lignes = []
    for d in decisions:
        f = fiches.get(d["id"])
        # Garde-fou : l'ACPR a retiré le nom, la fiche doit le retirer aussi.
        if f and d.get("publication") == "anonymisée" \
                and not f["identite"]["etablissement"].startswith("anonymisé"):
            alertes.append(
                f"{d['id']} : l'ACPR publie désormais cette décision sous forme anonymisée, "
                f"mais la fiche contient encore le nom « {f['identite']['etablissement']} ». "
                "La fiche n'est pas publiée sur le site tant qu'elle n'a pas été anonymisée.")
            f = None
            retenue = True
        else:
            retenue = False

        if f:
            natures = f["sanction"]["nature"]
            montant = f["sanction"]["montant_euros"]
            etab = etablissement_fiche(f)[0]
            type_exact = f["identite"]["type_etablissement"]
            groupe = TYPES.get(type_exact)
            if not groupe:
                groupe = "Autre"
                print(f"Attention {d['id']} : type « {type_exact} » absent du regroupement, rangé dans « Autre ».")
            issues = [g["issue"] for g in f.get("griefs", [])]
            cats = sorted({g["categorie"] for g in f.get("griefs", []) if g["issue"] != "écarté"},
                          key=CATEGORIES.index)
            lcbft = f["perimetre"] != "hors LCB-FT"
        else:
            natures = nature_depuis_texte(d.get("sanction_texte"))
            montant = d.get("montant_euros")
            etab = nom_affiche(d)
            type_exact, groupe, issues, cats = "", NON_RENSEIGNE, [], []
            lcbft = bool(d.get("lcbft_indice"))

        if f:
            etat = "fiche"
        elif retenue:
            etat = "Fiche en cours de mise à jour"
        elif lcbft:
            etat = "Fiche à venir"
        else:
            etat = "Fiche courte à venir (hors LCB-FT)"

        recherche = [d["numero_procedure"], etab, type_exact, " ".join(natures)]
        if f:
            recherche += [f["resume_court"], " ".join(f["pour_moi"].get("mots_cles", [])),
                          " ".join(g["titre"] for g in f.get("griefs", [])), " ".join(cats),
                          f["identite"].get("groupe", ""), f["identite"].get("pays", "")]
        lignes.append({
            "id": d["id"], "slug": d["id"].lower(), "regulateur": d["regulateur"],
            "procedure": d["numero_procedure"], "date": d.get("date_decision") or "",
            "annee": (d.get("date_decision") or "")[:4], "etab": etab, "type": type_exact,
            "groupe": groupe, "natures": natures, "montant": montant, "lcbft": lcbft,
            "issues": issues, "categories": cats, "fiche": f, "etat": etat,
            "url_pdf": d.get("url_pdf") or "", "url_page": d.get("url_page") or "",
            "decision": d, "recherche": sans_accents(" ".join(x for x in recherche if x)),
        })
    lignes.sort(key=lambda l: l["date"], reverse=True)
    return lignes


def etablissement_fiche(f):
    """Titre de la fiche et précision : le nom, ou « Établissement de crédit anonymisé »."""
    ident = f["identite"]
    nom = ident["etablissement"]
    if nom.startswith("anonymisé"):
        alias = re.search(r"«\s*(.+?)\s*»", nom)
        titre = f"{majuscule(ident['type_etablissement'])} anonymisé"
        if ident["type_etablissement"] in ("banque",):
            titre = "Banque anonymisée"
        precision = f"Dans la décision : « {alias.group(1)} »" if alias else ""
        return titre, precision
    return nom, ""


# --------------------------------------------------------------------------
# Gabarit commun à toutes les pages
# --------------------------------------------------------------------------

MENU = [("index.html", "Accueil"), ("base.html", "Base"), ("analyse.html", "Analyse"),
        ("methode.html", "Méthode"), ("lexique.html", "Lexique"), ("a-propos.html", "À propos")]


def page(chemin, titre, contenu, description, collecte, actif=None, scripts=""):
    """Écrit une page complète (en-tête, menu, contenu, pied de page) dans _site/."""
    profondeur = chemin.count("/")
    r = "../" * profondeur
    menu = "".join(
        f'<li><a href="{r}{lien}"{" aria-current=\"page\"" if lien == actif else ""}>{nom}</a></li>'
        for lien, nom in MENU)
    date_maj = date_en_clair(collecte["ACPR"]["date"])
    titre_complet = NOM_SITE if chemin == "index.html" else f"{titre} – {NOM_SITE}"
    texte = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titre_complet)}</title>
<meta name="description" content="{e(description)}">
<link rel="preload" href="{r}statique/polices/public-sans.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}statique/style.css">
<link rel="icon" href="{r}statique/icone.svg" type="image/svg+xml">
</head>
<body>
<a class="evitement" href="#contenu">Aller au contenu</a>
<header class="entete">
  <div class="cadre entete-cadre">
    <a class="marque" href="{r}index.html">Sanctions <span>Conformité</span></a>
    <nav aria-label="Menu principal"><ul>{menu}</ul></nav>
  </div>
</header>
<main id="contenu" class="cadre">
{contenu}
</main>
<footer class="pied">
  <div class="cadre">
    <p>Site personnel de Matéo Bonnesoeur, sans lien avec l'ACPR. Les décisions sont publiées par la
    Commission des sanctions de l'ACPR : seul leur texte officiel fait foi.</p>
    <p>Base mise à jour le {date_maj}. Code et données ouverts sur <a href="{LIEN_DEPOT}">GitHub</a>.</p>
  </div>
</footer>
{scripts}
</body>
</html>
"""
    sortie = SORTIE / chemin
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(texte, encoding="utf-8")


def gabarit(nom, valeurs):
    """Lit un texte fixe de site/pages/ et remplace les {{repères}} par des chiffres."""
    t = (ICI / "pages" / nom).read_text(encoding="utf-8")
    for k, v in valeurs.items():
        t = t.replace("{{" + k + "}}", str(v))
    return t


# --------------------------------------------------------------------------
# Les pages
# --------------------------------------------------------------------------

def cellule_fiche(l, r):
    if l["fiche"]:
        return f'<a href="{r}decisions/{l["slug"]}.html">Lire la fiche</a>'
    return f'<span class="attente">{e(l["etat"])}</span>'


def liste_recente(lignes, r=""):
    items = []
    for l in lignes:
        nom = e(l["etab"])
        if l["fiche"]:
            nom = f'<a href="{r}decisions/{l["slug"]}.html">{nom}</a>'
        sanction = nature_courte(l["natures"], l["montant"])
        if l["montant"]:
            sanction += f", {euros(l['montant'])}"
        suite = decompte(l["issues"]) if l["fiche"] else f'<span class="attente">{e(l["etat"])}</span>'
        items.append(f"""<li>
  <time datetime="{l['date']}">{date_courte(l['date'])}</time>
  <div><p class="recent-nom">{nom}</p><p class="recent-sanction">{e(sanction)}</p></div>
  <div class="recent-suite">{suite}</div>
</li>""")
    return f'<ol class="recentes">{"".join(items)}</ol>'


def accueil(lignes, collecte):
    avec_fiche = [l for l in lignes if l["fiche"]]
    lcbft = [l for l in lignes if l["lcbft"]]
    annees = sorted(l["annee"] for l in lignes if l["annee"])
    griefs = [i for l in avec_fiche for i in l["issues"]]
    dates_fiches = sorted(l["date"] for l in avec_fiche)
    debut, fin = dates_fiches[0], dates_fiches[-1]
    mois = lambda iso: date_en_clair(iso).split(" ", 1)[1]  # « 10 janvier 2019 » -> « janvier 2019 »
    retenus = sum(1 for i in griefs if i != "écarté")
    contenu = f"""
<section class="ouverture">
  <h1>Ce que l'ACPR reproche aux établissements qu'elle sanctionne</h1>
  <div class="intro">{texte_de_mateo("introduction", "Deux ou trois phrases de Matéo : ce qu'est ce site et pourquoi il l'a construit.")}</div>
  <p class="chiffres">La base réunit <strong>{len(lignes)} décisions</strong> de la Commission des sanctions
  de l'Autorité de contrôle prudentiel et de résolution, rendues de {annees[0]} à {annees[-1]}.
  <strong>{len(lcbft)}</strong> portent sur la lutte contre le blanchiment et le financement du terrorisme
  ou sur le gel des avoirs. <strong>{len(avec_fiche)}</strong> d'entre elles, rendues entre {mois(debut)}
  et {mois(fin)}, ont une fiche d'analyse : {len(griefs)} griefs examinés, dont {retenus} retenus
  en tout ou en partie.</p>
  <p class="actions"><a class="bouton" href="base.html">Parcourir la base</a>
  <a href="methode.html">Comment les fiches sont faites</a></p>
</section>
<div class="accueil-suite">
<section class="bloc">
  <h2>Décisions récentes</h2>
  {liste_recente(lignes[:8])}
  <p><a href="base.html">Toutes les décisions</a></p>
</section>
<section class="bloc legende-bloc">
  <h2>Lire la frise des griefs</h2>
  <p>Chaque barre est un grief, c'est-à-dire un reproche examiné par la Commission.</p>
  {legende()}
</section>
</div>
"""
    page("index.html", NOM_SITE, contenu,
         "Base des décisions de sanction de l'ACPR en matière de lutte contre le blanchiment, "
         "avec une fiche d'analyse par décision.", collecte, actif="index.html")


def legende():
    return """<ul class="legende">
  <li><span class="decompte" aria-hidden="true"><i class="r"></i></span> retenu</li>
  <li><span class="decompte" aria-hidden="true"><i class="p"></i></span> retenu en partie</li>
  <li><span class="decompte" aria-hidden="true"><i class="e"></i></span> écarté</li>
</ul>"""


def base(lignes, collecte):
    annees = sorted({l["annee"] for l in lignes if l["annee"]}, reverse=True)
    groupes = sorted({l["groupe"] for l in lignes}, key=lambda g: (g == NON_RENSEIGNE, g))
    regulateurs = sorted({l["regulateur"] for l in lignes})
    opt = lambda pairs: "".join(f'<option value="{e(v)}">{e(t)}</option>' for v, t in pairs)

    rangs = []
    for l in lignes:
        tranche = next(c for c, _, test in TRANCHES if test(l["montant"]))
        nom = e(l["etab"])
        if l["fiche"]:
            nom = f'<a href="decisions/{l["slug"]}.html">{nom}</a>'
        type_txt = f'<span class="type">{e(majuscule(l["type"]))}</span>' if l["type"] else ""
        source = f'<a class="source" href="{e(l["url_pdf"] or l["url_page"])}">Source officielle</a>'
        rangs.append(f"""<tr data-annee="{l['annee']}" data-groupe="{e(l['groupe'])}" data-regulateur="{e(l['regulateur'])}"
 data-tranche="{tranche}" data-montant="{l['montant'] or 0}" data-date="{l['date']}" data-lcbft="{'1' if l['lcbft'] else '0'}"
 data-fiche="{'1' if l['fiche'] else '0'}" data-categories="{e('|'.join(l['categories']))}" data-recherche="{e(l['recherche'])}">
  <td class="c-date" data-titre="Décision"><time datetime="{l['date']}">{date_courte(l['date'])}</time><span class="proc">{e(l['regulateur'])} n°&nbsp;{e(l['procedure'])}</span></td>
  <td class="c-nom" data-titre="Établissement">{nom}{type_txt}</td>
  <td class="c-sanction" data-titre="Sanction">{e(nature_courte(l['natures'], l['montant']))}</td>
  <td class="c-montant" data-titre="Montant">{euros(l['montant'])}</td>
  <td class="c-griefs" data-titre="Griefs">{decompte(l['issues']) or '<span class="attente">—</span>'}</td>
  <td class="c-fiche" data-titre="Fiche">{cellule_fiche(l, '')}{source}</td>
</tr>""")

    contenu = f"""
<div class="titre-page">
  <h1>La base des décisions</h1>
  <p class="chapo">Toutes les décisions de la Commission des sanctions de l'ACPR publiées dans son recueil
  officiel. Les fiches d'analyse couvrent pour l'instant les décisions sur la lutte contre le blanchiment
  rendues depuis 2019.</p>
</div>
<form class="filtres" id="filtres" role="search" hidden>
  <div class="champ champ-large">
    <label for="f-recherche">Rechercher</label>
    <input type="search" id="f-recherche" name="q" placeholder="Établissement, mot-clé, n° de procédure" autocomplete="off">
  </div>
  <details class="plus-filtres" id="plus-filtres" open>
  <summary>Filtres <span id="nb-filtres"></span></summary>
  <div class="grille-filtres">
  <div class="champ"><label for="f-regulateur">Régulateur</label>
    <select id="f-regulateur" name="regulateur"><option value="">Tous</option>{opt((x, x) for x in regulateurs)}</select></div>
  <div class="champ"><label for="f-annee">Année de la décision</label>
    <select id="f-annee" name="annee"><option value="">Toutes</option>{opt((a, a) for a in annees)}</select></div>
  <div class="champ"><label for="f-groupe">Type d'établissement</label>
    <select id="f-groupe" name="type"><option value="">Tous</option>{opt((g, g) for g in groupes)}</select></div>
  <div class="champ"><label for="f-categorie">Manquement retenu</label>
    <select id="f-categorie" name="categorie"><option value="">Tous</option>{opt((c, majuscule(c)) for c in CATEGORIES)}</select></div>
  <div class="champ"><label for="f-tranche">Montant</label>
    <select id="f-tranche" name="montant"><option value="">Tous</option>{opt((c, t) for c, t, _ in TRANCHES)}</select></div>
  <div class="champ"><label for="f-theme">Thème</label>
    <select id="f-theme" name="theme"><option value="">Tous</option><option value="1">Blanchiment et gel des avoirs</option><option value="0">Autres thèmes</option></select></div>
  <div class="champ champ-case"><input type="checkbox" id="f-fiche" name="fiche" value="1">
    <label for="f-fiche">Seulement les décisions analysées</label></div>
  <div class="champ champ-case"><button type="button" id="f-effacer" class="lien-bouton">Effacer les filtres</button></div>
  </div>
  </details>
</form>
<div class="resultat">
  <p id="compte" aria-live="polite">{len(lignes)} décisions</p>
  {legende()}
</div>
<table class="base" id="base">
  <caption class="visuellement-cache">Décisions de sanction, de la plus récente à la plus ancienne</caption>
  <thead><tr>
    <th scope="col" aria-sort="descending"><button type="button" data-tri="date">Décision</button></th>
    <th scope="col">Établissement</th>
    <th scope="col">Sanction</th>
    <th scope="col" class="c-montant"><button type="button" data-tri="montant">Montant</button></th>
    <th scope="col">Griefs</th>
    <th scope="col">Fiche</th>
  </tr></thead>
  <tbody>
{''.join(rangs)}
  </tbody>
</table>
<p id="aucun" class="aucun" hidden>Aucune décision ne correspond à ces filtres. <button type="button" class="lien-bouton" data-effacer>Effacer les filtres</button></p>
"""
    page("base.html", "La base des décisions", contenu,
         "Toutes les décisions de sanction de l'ACPR, avec recherche et filtres.", collecte,
         actif="base.html", scripts='<script src="statique/base.js" defer></script>')


def fiche_page(l, glossaire, collecte):
    f, d = l["fiche"], l["decision"]
    pdf = l["url_pdf"]
    P = lambda pages: lien_pages(pages, pdf)
    titre, precision = etablissement_fiche(f)
    s, ident = f["sanction"], f["identite"]
    morceaux = [n for n in s["nature"] if n != "sanction pécuniaire"]
    if s["montant_euros"]:
        morceaux.append("sanction pécuniaire de " + euros(s["montant_euros"]))
    elif "sanction pécuniaire" in s["nature"]:
        morceaux.append("sanction pécuniaire (montant masqué ou non lu)")
    sanction_txt = majuscule(" et ".join([", ".join(morceaux[:-1]), morceaux[-1]]) if len(morceaux) > 1
                             else (morceaux[0] if morceaux else "non précisé"))
    red = f["redaction"]
    relue = red.get("relue_par_mateo") or f["suivi"]["statut"] == "lue"

    sommaire = [("en-bref", "En bref"), ("manquements", "Manquements"),
                ("sanction", "Sanction et procédure"), ("etablissement", "L'établissement"),
                ("contexte", "Contexte"), ("lecons", "Ce qui aurait dû être fait"),
                ("lexique", "Lexique"), ("source", "Source et rédaction")]

    # --- Manquements
    blocs = []
    for g in f.get("griefs", []):
        code = next(c for nom, c, _, _ in ISSUES if nom == g["issue"])
        hors = "hors LCB-FT" in (g.get("categorie_precision") or "")
        cat = majuscule(g["categorie"])
        lien_cat = f'<a href="../base.html?categorie={e(g["categorie"])}">{e(cat)}</a>'
        if g.get("categorie_precision"):
            lien_cat += f' <span class="note">({e(g["categorie_precision"])})</span>'
        secondaires = ""
        if g.get("categories_secondaires"):
            secondaires = f"<dt>Touche aussi</dt><dd>{e(majuscule(' ; '.join(g['categories_secondaires'])))}</dd>"
        chiffres = "".join(f"<li>{e(c)}</li>" for c in g.get("chiffres_cles", []))
        blocs.append(f"""<details class="grief" id="grief-{e(g['numero'])}">
  <summary>
    <span class="grief-num">Grief {e(g['numero'])}</span>
    <span class="grief-titre">{e(g['titre'])}{' <span class="hors">hors LCB-FT</span>' if hors else ''}</span>
    <span class="issue issue-{code}">{e(majuscule(g['issue']))}</span>
  </summary>
  <div class="grief-corps">
    <p>{e(g['resume'])}{P(g['pages'])}</p>
    <p class="decide"><strong>Décision de la Commission.</strong> {e(g['precision_issue'])}</p>
    <dl class="infos">
      {f'<dt>Chiffres clés</dt><dd><ul>{chiffres}</ul></dd>' if chiffres else ''}
      <dt>Textes visés</dt><dd>{e(' ; '.join(g.get('textes', [])) or 'non précisé')}</dd>
      <dt>Catégorie</dt><dd>{lien_cat}</dd>
      {secondaires}
    </dl>
  </div>
</details>""")
    issues = l["issues"]
    manquements = f"""<p class="bilan">{decompte(issues)} {e(bilan(issues))}.</p>
<p class="aide"><button type="button" class="lien-bouton" id="tout-ouvrir" hidden>Tout déplier</button></p>
{''.join(blocs)}""" if blocs else "<p>Cette fiche ne détaille pas de griefs.</p>"

    # --- Sanction et procédure
    c = f.get("controle", {})
    pr = f.get("procedure", {})
    lignes_sanction = [
        ("Sanction", e(sanction_txt) + P(s.get("pages", []))),
        ("Proposée par le Collège", e(s.get("proposition_du_college", "non précisé"))),
        ("Publication", e(majuscule(s.get("publication", ""))) +
         (f" ({e(s['duree_publication_nominative'])})" if s.get("duree_publication_nominative") else "")),
        ("Contrôle sur place", e(c.get("controle_sur_place", "non précisé"))),
        ("Rapport de contrôle", e(c.get("rapport_de_controle", "non précisé"))),
        ("Ouverture de la procédure", e(c.get("ouverture_de_la_procedure", "non précisé"))),
        ("Antécédents", e(c.get("antecedents", "non précisé")) + P(c.get("pages", []))),
    ]
    if pr:
        lignes_sanction.append(("Questions de procédure", e(pr["questions_de_procedure"]) + P(pr.get("pages", []))))
    dl = lambda rows: "<dl class=\"tableau-def\">" + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows) + "</dl>"

    lignes_etab = [
        ("Établissement", e(ident["etablissement"])),
        ("Type", e(majuscule(ident["type_etablissement"])) +
         (f". {e(ident['precision_type'])}" if ident.get("precision_type") else "")),
        ("Groupe", e(ident.get("groupe") or "non précisé")),
        ("Pays", e(ident.get("pays") or "non précisé")),
    ]
    if ident.get("activite_et_taille"):
        lignes_etab.append(("Activité et taille", e(ident["activite_et_taille"]) + P(ident.get("pages", []))))

    # --- Contexte
    ctx = f.get("contexte", {})
    liste = lambda items: "<ul>" + "".join(f"<li>{e(x['texte'])}{P(x.get('pages', []))}</li>"
                                           for x in items) + "</ul>" if items else "<p>Non précisé.</p>"
    contexte = ""
    if ctx:
        contexte = f"""<h3>Ce qui a pesé contre l'établissement</h3>{liste(ctx.get('elements_aggravants'))}
<h3>Ce qui a joué en sa faveur</h3>{liste(ctx.get('elements_attenuants'))}
<h3>Mesures correctrices</h3>{liste(ctx.get('mesures_correctrices'))}
<h3>Situation financière</h3><p>{e(ctx['situation_financiere']['texte'])}{P(ctx['situation_financiere'].get('pages', []))}</p>
<h3>Cause profonde</h3><p>{e(ctx['cause_profonde']['texte'])}{P(ctx['cause_profonde'].get('pages', []))}</p>"""

    # --- Leçons (déduites)
    ded = f.get("deduit_par_claude", {})
    lecons = ""
    if ded:
        lecons = f"""<div class="deduit">
<p class="deduit-avert">Ce bloc ne figure pas dans la décision : ce sont des points de contrôle déduits des manquements retenus.</p>
<ul>{''.join(f'<li>{e(x)}</li>' for x in ded.get('points_de_controle', []))}</ul>
</div>"""

    m = f["pour_moi"]
    a_lire = "".join(f"<li>{lien_pages(x['pages'], pdf).strip()} : {e(x['pourquoi'])}</li>"
                     for x in m.get("pages_prioritaires", []))
    mots = "".join(f"<li>{e(x)}</li>" for x in m.get("mots_cles", []))

    # Le lexique est calculé sur le texte affiché (on retire les notes de travail).
    visible = {k: v for k, v in f.items() if k not in ("suivi", "pour_moi", "redaction")}
    termes = lexique(json.dumps(visible, ensure_ascii=False), glossaire)
    lex = "".join(f"<dt>{e(t['terme'])}</dt><dd>{e(t['definition'])}</dd>" for t in termes)

    # « mes_notes » reste privé : il n'est pas affiché sur le site.
    statut = ("Fiche relue par Matéo." if relue else
              "Cette fiche n'a pas encore été relue par Matéo.")

    contenu = f"""
<nav class="fil" aria-label="Fil d'Ariane"><a href="../base.html">Base</a> <span aria-hidden="true">/</span> {e(l['regulateur'])} n°&nbsp;{e(l['procedure'])}</nav>
<header class="fiche-tete">
  <p class="fiche-sur">Commission des sanctions de l'ACPR, procédure n°&nbsp;{e(l['procedure'])}</p>
  <h1>{e(titre)}</h1>
  {f'<p class="fiche-alias">{e(precision)}</p>' if precision else ''}
  <dl class="faits">
    <div><dt>Décision rendue le</dt><dd>{date_en_clair(l['date'])}</dd></div>
    <div><dt>Sanction</dt><dd>{e(sanction_txt)}</dd></div>
    <div><dt>Griefs</dt><dd>{decompte(issues)}<span class="faits-bilan">{e(bilan(issues).split(' : ')[1]) if issues else 'non détaillés'}</span></dd></div>
    <div><dt>Périmètre</dt><dd>{e(f['perimetre'])}</dd></div>
  </dl>
  <p class="avertissement">{statut} Rédigée avec Claude ({e(red['redigee_par'].split('(')[1].split(')')[0]) if '(' in red['redigee_par'] else 'IA'})
  à partir du PDF officiel ; chaque information renvoie à sa page. <a href="{e(pdf)}">Ouvrir la décision officielle</a></p>
</header>
<div class="fiche">
  <nav class="sommaire" aria-label="Sommaire de la fiche"><p>Sur cette page</p><ul>
    {''.join(f'<li><a href="#{a}">{t}</a></li>' for a, t in sommaire)}
  </ul></nav>
  <article class="fiche-corps">
    <section id="en-bref"><h2>En bref</h2><p class="chapo">{e(f['resume_court'])}</p></section>
    <section id="manquements"><h2>Manquements</h2>{manquements}</section>
    <section id="sanction"><h2>Sanction et procédure</h2>{dl(lignes_sanction)}</section>
    <section id="etablissement"><h2>L'établissement</h2>{dl(lignes_etab)}</section>
    <section id="contexte"><h2>Contexte</h2>{contexte or '<p>Non précisé.</p>'}</section>
    <section id="lecons"><h2>Ce qui aurait dû être fait</h2>{lecons or '<p>Non renseigné.</p>'}
      {f'<h3>Pages à lire en priorité</h3><ul class="a-lire">{a_lire}</ul>' if a_lire else ''}
      {f'<h3>Mots-clés</h3><ul class="mots">{mots}</ul>' if mots else ''}
    </section>
    <section id="lexique"><h2>Lexique</h2>{f'<dl class="lexique">{lex}</dl>' if lex else '<p>Aucun terme technique.</p>'}
      <p><a href="../lexique.html">Tout le lexique</a></p></section>
    <section id="source"><h2>Source et rédaction</h2>
      <dl class="tableau-def">
        <dt>Décision officielle</dt><dd><a href="{e(pdf)}">PDF publié par l'ACPR</a> ({d.get('nb_pages', '?')} pages)</dd>
        <dt>Rédaction</dt><dd>{e(red['redigee_par'])}, le {date_en_clair(red['date'])}.</dd>
        <dt>Relecture</dt><dd>{statut}</dd>
        <dt>Confiance de l'analyse</dt><dd>{e(majuscule(m.get('confiance', 'non précisée')))}</dd>
      </dl>
    </section>
  </article>
</div>
"""
    desc = f"Décision de sanction de l'ACPR n° {l['procedure']} : {f['resume_court'][:140]}"
    page(f"decisions/{l['slug']}.html", f"{titre} – procédure n° {l['procedure']}", contenu, desc,
         collecte, scripts='<script src="../statique/fiche.js" defer></script>')


def lexique_page(glossaire, collecte):
    tri = sorted(glossaire, key=lambda t: sans_accents(t["terme"]))
    lettres = {}
    for t in tri:
        lettres.setdefault(sans_accents(t["terme"])[0].upper(), []).append(t)
    nav = "".join(f'<li><a href="#lettre-{k}">{k}</a></li>' for k in lettres)
    blocs = "".join(
        f'<section id="lettre-{k}"><h2>{k}</h2><dl class="lexique">' +
        "".join(f"<dt>{e(t['terme'])}</dt><dd>{e(t['definition'])}</dd>" for t in ts) +
        "</dl></section>" for k, ts in lettres.items())
    contenu = f"""
<div class="titre-page"><h1>Lexique</h1>
<p class="chapo">Les {len(glossaire)} termes techniques employés dans les fiches, expliqués en une phrase.
Chaque fiche reprend en bas de page ceux qu'elle utilise.</p></div>
<nav aria-label="Lettres"><ul class="lettres">{nav}</ul></nav>
<div class="lexique-page">{blocs}</div>"""
    page("lexique.html", "Lexique", contenu, "Glossaire de la conformité et de la lutte contre le blanchiment.",
         collecte, actif="lexique.html")


def pages_fixes(lignes, collecte):
    avec_fiche = [l for l in lignes if l["fiche"]]
    relues = sum(1 for l in avec_fiche
                 if l["fiche"]["redaction"].get("relue_par_mateo") or l["fiche"]["suivi"]["statut"] == "lue")
    valeurs = {
        "nb_decisions": len(lignes), "nb_fiches": len(avec_fiche), "nb_relues": relues,
        "nb_lcbft": sum(1 for l in lignes if l["lcbft"]),
        "categories": "".join(f"<li>{e(majuscule(c))}</li>" for c in CATEGORIES),
        "date_collecte": date_en_clair(collecte["ACPR"]["date"]),
    }
    page("methode.html", "Méthode", gabarit("methode.html", valeurs),
         "Sources, grille d'analyse, mise à jour et limites du projet.", collecte, actif="methode.html")
    page("analyse.html", "Analyse", gabarit("analyse.html", valeurs),
         "Étude comparative des décisions de sanction.", collecte, actif="analyse.html")
    contenu = f"""<div class="titre-page"><h1>À propos</h1></div>
<div class="texte">{texte_de_mateo("a-propos", "Qui est Matéo, pourquoi ce projet, et le lien vers son profil LinkedIn.")}</div>"""
    page("a-propos.html", "À propos", contenu, "Qui a construit ce site et pourquoi.", collecte,
         actif="a-propos.html")


# --------------------------------------------------------------------------

def principal():
    decisions, fiches, glossaire, collecte = charger()
    lignes = preparer(decisions, fiches)

    if SORTIE.exists():
        shutil.rmtree(SORTIE)
    shutil.copytree(ICI / "statique", SORTIE / "statique")
    (SORTIE / ".nojekyll").write_text("")  # dit à GitHub de publier les fichiers tels quels

    accueil(lignes, collecte)
    base(lignes, collecte)
    for l in lignes:
        if l["fiche"]:
            fiche_page(l, glossaire, collecte)
    lexique_page(glossaire, collecte)
    pages_fixes(lignes, collecte)

    nb = sum(1 for l in lignes if l["fiche"])
    print(f"Site fabriqué dans _site/ : {len(lignes)} décisions, {nb} fiches publiées.")
    ALERTES.write_text("\n".join(alertes), encoding="utf-8")
    for a in alertes:
        print("ALERTE " + a)


if __name__ == "__main__":
    principal()
