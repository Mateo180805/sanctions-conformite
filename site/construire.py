"""
Fabrication du site public (GitHub Pages).

Ce programme lit les données du dépôt et écrit des pages HTML toutes prêtes dans
le dossier _site/. Il ne télécharge rien et n'analyse rien : il met en page.

Il lit :
  - donnees/decisions.json      la base des décisions (une ligne par décision) ;
  - donnees/fiches/*/*.json     les fiches d'analyse (la fiche fait foi) ;
  - donnees/glossaire.json      le glossaire commun (page Lexique et lexique des fiches) ;
  - site/pages/*.html           les textes fixes (Méthode, Analyse) ;
  - donnees/etude/points_de_controle.json   la liste des points de contrôle (page du même nom) ;
  - site/textes/*.txt           les textes écrits par Matéo (introduction, À propos).

Il ne lit JAMAIS donnees/textes/ (le texte intégral des décisions) : certains textes
anonymisés laissent passer des noms. Le site s'appuie uniquement sur les fiches.

Garde-fous :
  - aucun nom de personne physique n'est affiché (voir nom_affiche ; pour l'AMF, la
    collecte ne les enregistre même pas) ;
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
import urllib.parse
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "analyse"))
from fiches import CATEGORIES, date_en_clair, lexique  # noqa: E402  (on réutilise le code des fiches)
import etude  # noqa: E402  (les comptages de l'étude comparative : analyse/etude.py)

DONNEES = RACINE / "donnees"
ICI = Path(__file__).resolve().parent
SORTIE = RACINE / "_site"
ALERTES = RACINE / "_alertes.txt"
LIEN_DEPOT = "https://github.com/Mateo180805/sanctions-conformite"
ADRESSE_SITE = "https://mateo180805.github.io/sanctions-conformite/"
NOM_SITE = "Sanctions Conformité"

MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août",
               "sept.", "oct.", "nov.", "déc."]

# Regroupement des types d'établissement pour le filtre de la base (question 4 du journal).
# La fiche garde le terme exact de la décision ; ce tableau ne sert qu'au filtre.
# Regroupement des types d'établissement : défini une seule fois, dans analyse/etude.py.
TYPES = etude.TYPES
NON_RENSEIGNE = "Non renseigné (fiche à venir)"

# Thèmes de la liste officielle de l'AMF, écrits en clair (affichage et phrase de l'accueil).
THEMES_AMF = {
    "Obligations professionnelles": "obligations professionnelles",
    "Obligation d'information": "obligation d'information",
    "Manquement d'initié": "manquement d'initié",
    "Manipulation de marché": "manipulation de marché",
    "PSI": "prestataires de services d'investissement",
    "CIF, CIP ou autres prestataires": "conseillers et autres prestataires",
    "Produit d'épargne collective": "produits d'épargne collective",
    "Procédure": "procédure",
    "Instrument financier": "instruments financiers",
    "Infrastructure de marché": "infrastructures de marché",
}

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
    if d.get("regulateur") == "AMF":
        # La collecte AMF a déjà retiré les noms de personnes physiques (« Société X et
        # 2 personnes physiques ») : voir collecte/amf.py.
        return majuscule(adoucir_capitales(d.get("nom_site") or "Non précisé"))
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
        elif d["regulateur"] != "ACPR":
            etat = "Pas encore de fiche"
        elif retenue:
            etat = "Fiche en cours de mise à jour"
        elif lcbft:
            etat = "Fiche à venir"
        else:
            etat = "Fiche courte à venir (hors LCB-FT)"

        theme = THEMES_AMF.get(d.get("theme_court"), d.get("theme_court") or "") if d["regulateur"] == "AMF" else ""
        recherche = [d["regulateur"], d["numero_procedure"], etab, type_exact, theme, " ".join(natures)]
        if f:
            recherche += [f["resume_court"], " ".join(f["pour_moi"].get("mots_cles", [])),
                          " ".join(g["titre"] for g in f.get("griefs", [])), " ".join(cats),
                          f["identite"].get("groupe", ""), f["identite"].get("pays", "")]
        lignes.append({
            "id": d["id"], "slug": d["id"].lower(), "regulateur": d["regulateur"],
            "procedure": d["numero_procedure"], "date": d.get("date_decision") or "",
            "annee": (d.get("date_decision") or "")[:4], "etab": etab, "type": type_exact, "theme": theme,
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
        ("points-de-controle.html", "Points de contrôle"), ("methode.html", "Méthode"), ("lexique.html", "Lexique"), ("a-propos.html", "À propos")]


def page(chemin, titre, contenu, description, collecte, actif=None, scripts="", absolu=False):
    """Écrit une page complète (en-tête, menu, contenu, pied de page) dans _site/.

    absolu=True : liens complets (sert à la page 404, qui peut s'afficher à n'importe quelle adresse).
    """
    profondeur = chemin.count("/")
    r = ADRESSE_SITE if absolu else "../" * profondeur
    menu = "".join(
        f'<li><a href="{r}{lien}"{" aria-current=\"page\"" if lien == actif else ""}>{nom}</a></li>'
        for lien, nom in MENU)
    date_maj = date_en_clair(max(c["date"] for c in collecte.values()))
    titre_complet = NOM_SITE if chemin == "index.html" else f"{titre} – {NOM_SITE}"
    # Classe de la page (« p-base », « p-fiche »...) : chaque page a son propre bandeau (style.css).
    classe = ("accueil" if chemin == "index.html" else "fiche" if chemin.startswith("decisions/")
              else chemin.rsplit(".", 1)[0])
    texte = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titre_complet)}</title>
<meta name="description" content="{e(description)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="{NOM_SITE}">
<meta property="og:title" content="{e(titre_complet)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{ADRESSE_SITE}{'' if chemin == 'index.html' else chemin}">
<meta property="og:image" content="{ADRESSE_SITE}statique/apercu.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="{r}statique/polices/public-sans.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}statique/style.css">
<link rel="icon" href="{r}statique/icone.svg" type="image/svg+xml">
</head>
<body class="p-{classe}">
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
    <p>Site personnel de Matéo Bonnesoeur, sans lien avec l'ACPR ni l'AMF. Les décisions sont publiées par
    les commissions des sanctions de ces deux autorités : seul leur texte officiel fait foi.</p>
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
        sanction = f"{l['regulateur']} · {sanction}"
        suite = decompte(l["issues"]) if l["fiche"] else f'<span class="attente">{e(l["etat"])}</span>'
        items.append(f"""<li>
  <time datetime="{l['date']}">{date_courte(l['date'])}</time>
  <div><p class="recent-nom">{nom}</p><p class="recent-sanction">{e(sanction)}</p></div>
  <div class="recent-suite">{suite}</div>
</li>""")
    return f'<ol class="recentes">{"".join(items)}</ol>'


def accueil(lignes, collecte):
    acpr = [l for l in lignes if l["regulateur"] == "ACPR"]
    amf = [l for l in lignes if l["regulateur"] == "AMF"]
    avec_fiche = [l for l in lignes if l["fiche"]]
    lcbft = [l for l in acpr if l["lcbft"]]
    annees = sorted(l["annee"] for l in acpr if l["annee"])
    griefs = [i for l in avec_fiche for i in l["issues"]]
    dates_fiches = sorted(l["date"] for l in avec_fiche)
    debut, fin = dates_fiches[0], dates_fiches[-1]
    mois = lambda iso: date_en_clair(iso).split(" ", 1)[1]  # « 10 janvier 2019 » -> « janvier 2019 »
    retenus = sum(1 for i in griefs if i != "écarté")
    phrase_amf = ""
    if amf:
        # Les trois thèmes les plus fréquents de la liste officielle de l'AMF.
        compte = {}
        for l in amf:
            if l["theme"]:
                compte[l["theme"]] = compte.get(l["theme"], 0) + 1
        themes = [t for t, _ in sorted(compte.items(), key=lambda kv: -kv[1])[:3]]
        annees_amf = sorted(l["annee"] for l in amf if l["annee"])
        phrase_amf = f"""
  <p class="chiffres">Elle compte aussi <strong>{len(amf)} décisions</strong> de la Commission des sanctions de
  l'Autorité des marchés financiers (AMF), rendues de {annees_amf[0]} à {annees_amf[-1]}, classées par l'AMF
  surtout en {", ".join(themes[:-1])} et {themes[-1]}. Elles n'ont pas encore de fiche d'analyse.</p>"""
    contenu = f"""
<section class="ouverture">
  <h1>Ce que l'ACPR et l'AMF reprochent à ceux qu'elles sanctionnent</h1>
  <div class="intro">{texte_de_mateo("introduction", "Deux ou trois phrases de Matéo : ce qu'est ce site et pourquoi il l'a construit.")}</div>
  <p class="chiffres">La base réunit <strong>{len(acpr)} décisions</strong> de la Commission des sanctions
  de l'Autorité de contrôle prudentiel et de résolution (ACPR), rendues de {annees[0]} à {annees[-1]}.
  <strong>{len(lcbft)}</strong> portent sur la lutte contre le blanchiment et le financement du terrorisme
  ou sur le gel des avoirs. <strong>{len(avec_fiche)}</strong> d'entre elles, rendues entre {mois(debut)}
  et {mois(fin)}, ont une fiche d'analyse : {len(griefs)} griefs examinés, dont {retenus} retenus
  en tout ou en partie.</p>{phrase_amf}
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
         "Base des décisions de sanction de l'ACPR et de l'AMF, avec une fiche d'analyse "
         "pour les décisions de l'ACPR sur la lutte contre le blanchiment.", collecte, actif="index.html")


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
        precision = l["type"] or l["theme"]
        type_txt = f'<span class="type">{e(majuscule(precision))}</span>' if precision else ""
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
  <p class="chapo">Toutes les décisions des commissions des sanctions de l'ACPR et de l'AMF publiées sur
  leurs sites officiels. Les fiches d'analyse couvrent pour l'instant les décisions de l'ACPR sur la lutte
  contre le blanchiment rendues depuis 2019.</p>
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
         "Toutes les décisions de sanction de l'ACPR et de l'AMF, avec recherche et filtres.", collecte,
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


# --------------------------------------------------------------------------
# L'étude comparative : page Analyse et page Points de contrôle
# --------------------------------------------------------------------------

# Le texte de site/pages/analyse.html a été écrit sur ce nombre de fiches. S'il change,
# les graphiques suivent tout seuls, mais les phrases sont à relire : un bandeau le signale.
ETUDE_NB_FICHES = 31
ETUDE_DATE = "13 novembre 2026"


def liens_fiches(texte, publiees):
    """Remplace [[2020-05]] par un lien vers la fiche, et [[2020-05#11]] par un lien vers son
    grief 11. Si la fiche n'est pas publiée (retirée le temps d'être anonymisée), pas de lien."""
    def un_lien(m):
        procedure, grief = m.group(1), m.group(2)
        if "ACPR-" + procedure not in publiees:
            return procedure
        ancre = f"#grief-{grief}" if grief else ""
        titre = f"Décision {procedure}, grief {grief}" if grief else f"Décision {procedure}"
        return f'<a class="ref" href="decisions/acpr-{procedure}.html{ancre}" title="{titre}">{procedure}</a>'
    return re.sub(r"\[\[(\d{4}-\d{2})(?:#(\d+))?\]\]", un_lien, texte)


def millions(n):
    """4000000 -> « 4 M€ » ; 150000 -> « 150 000 € » ; 0 -> « – »."""
    if not n:
        return "–"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " M€"
    return euros(n)


def barre(valeur, maximum, classe="r"):
    """Une barre horizontale dont la longueur est proportionnelle à la valeur."""
    largeur = 100 * valeur / maximum if maximum else 0
    return f'<span class="barre {classe}" style="width:{largeur:.1f}%"></span>'


def graphique_categories(chiffres):
    """Un tableau-graphique : une ligne par catégorie, une barre pour le nombre de décisions,
    et les griefs découpés en retenus / en partie / écartés, comme la frise des fiches."""
    n = chiffres["nb_decisions"]
    lignes = []
    for c in chiffres["categories"]:
        d = len(c["decisions_sanctionnees"])
        issues = (["retenu"] * c["retenus"] + ["retenu en partie"] * c["en_partie"]
                  + ["écarté"] * c["ecartes"])
        nom = "Autres obligations" if c["categorie"].startswith("autre") else majuscule(c["categorie"])
        lien = "base.html?categorie=" + urllib.parse.quote(c["categorie"])
        lignes.append(f"""<tr>
  <th scope="row"><a href="{e(lien)}">{e(nom)}</a></th>
  <td class="g-barre"><span class="piste">{barre(d, n)}</span></td>
  <td class="g-nombre"><strong>{d}</strong><span class="sur"> / {n}</span></td>
  <td class="g-griefs">{decompte(issues)}<span class="g-detail">{c['griefs']}</span></td>
</tr>""")
    return f"""<figure class="graphique">
<figcaption><strong>Nombre de décisions où le manquement est retenu, en entier ou en partie</strong>
<span>Sur {n} décisions. À droite, les griefs correspondants.</span></figcaption>
<div class="defile"><table class="graphe graphe-categories">
<thead><tr><th scope="col">Catégorie</th><th scope="col" colspan="2">Décisions</th><th scope="col">Griefs</th></tr></thead>
<tbody>{''.join(lignes)}</tbody></table></div>
{legende()}
</figure>"""


def graphique_simple(titre, sous_titre, entetes, rangees, classe=""):
    """Tableau-graphique générique. rangees : liste de (libellé, valeur, texte de la valeur, colonnes en plus)."""
    maximum = max(r[1] for r in rangees)
    corps = "".join(
        f"""<tr><th scope="row">{lib}</th>
  <td class="g-barre"><span class="piste">{barre(v, maximum)}</span></td>
  <td class="g-nombre"><strong>{txt}</strong></td>{''.join(f'<td class="g-plus">{x}</td>' for x in plus)}</tr>"""
        for lib, v, txt, plus in rangees)
    tetes = (f'<th scope="col">{entetes[0]}</th><th scope="col" colspan="2">{entetes[1]}</th>'
             + "".join(f'<th scope="col">{x}</th>' for x in entetes[2:]))
    return f"""<figure class="graphique">
<figcaption><strong>{titre}</strong><span>{sous_titre}</span></figcaption>
<div class="defile"><table class="graphe {classe}"><thead><tr>{tetes}</tr></thead><tbody>{corps}</tbody></table></div>
</figure>"""


def etude_pages(lignes, valeurs, collecte):
    fiches_lcbft, decisions = etude.charger()
    chiffres = etude.calculer(fiches_lcbft, decisions)
    publiees = {l["id"] for l in lignes if l["fiche"]}

    types = graphique_simple(
        "Décisions par type d'établissement", f"{chiffres['nb_decisions']} décisions, de 2019 à 2026.",
        ["Type", "Décisions", "Total des amendes"],
        [(e(t), v["decisions"], str(v["decisions"]), [millions(v["montant_total"])])
         for t, v in chiffres["par_type"].items()], "graphe-types")
    annees = graphique_simple(
        "Décisions par année", "Année de la décision, pas du contrôle. 2026 : jusqu'en avril.",
        ["Année", "Décisions", "Total des amendes"],
        [(a, v["decisions"], str(v["decisions"]), [millions(v["montant_total"])])
         for a, v in chiffres["par_annee"].items()], "graphe-annees")
    par_montant = sorted(chiffres["decisions"], key=lambda l: (-l["montant"], l["date"]))
    montants = graphique_simple(
        "Montant de l'amende, décision par décision",
        "De la plus forte à la plus faible. Le type d'établissement est celui de la fiche.",
        ["Décision", "Amende", "Établissement", "Demandé par le Collège"],
        [(liens_fiches(f"[[{l['procedure']}]]", publiees), l["montant"],
          millions(l["montant"]) if l["montant"] else e(" et ".join(l["nature"])),
          [e(majuscule(l["type"])), millions(l["montant_propose"]) if l["montant"] else "–"])
         for l in par_montant], "graphe-montants")

    note = ""
    if chiffres["nb_decisions"] != ETUDE_NB_FICHES:
        note = (f'<div class="reserve"><p><strong>Texte à mettre à jour.</strong> Les graphiques portent sur '
                f'{chiffres["nb_decisions"]} décisions, mais les phrases de cette page ont été écrites le '
                f'{ETUDE_DATE} sur {ETUDE_NB_FICHES} décisions. Les chiffres cités dans le texte peuvent '
                f'donc être dépassés.</p></div>')

    donnees, problemes = etude.lire_points(fiches_lcbft)
    if problemes:
        sys.exit("La liste des points de contrôle a des problèmes :\n  - " + "\n  - ".join(problemes))

    valeurs = dict(valeurs, graph_categories=graphique_categories(chiffres), graph_types=types,
                   graph_annees=annees, graph_montants=montants, note_actualite=note,
                   nb_points=len(donnees["points"]))
    texte = re.sub(r"\A<!--.*?-->\s*", "", gabarit("analyse.html", valeurs), flags=re.S)  # note de travail
    page("analyse.html", "Analyse", liens_fiches(texte, publiees),
         "Étude comparative de 31 décisions de sanction de l'ACPR en matière de lutte contre le "
         "blanchiment et de gel des avoirs.", collecte, actif="analyse.html")
    points_page(donnees, chiffres, publiees, collecte)


def points_page(donnees, chiffres, publiees, collecte):
    """La liste des points de contrôle, rangée par catégorie, de la plus sanctionnée à la moins sanctionnée."""
    sanctionnees = {c["categorie"]: len(c["decisions_sanctionnees"]) for c in chiffres["categories"]}
    ordre = [c["categorie"] for c in chiffres["categories"]]
    sommaire, sections = [], []
    for k, cat in enumerate(ordre, 1):
        points = [p for p in donnees["points"] if p["categorie"] == cat]
        if not points:
            continue
        nom = "Autres obligations" if cat.startswith("autre") else majuscule(cat)
        sommaire.append(f'<li><a href="#c{k}">{e(nom)}</a> <span>{len(points)}</span></li>')
        items = []
        for p in points:
            refs = ", ".join(
                liens_fiches(f"[[{proc}#{nums[0]}]]", publiees)
                for proc, nums in sorted(p["sources"].items()))
            items.append(f"""<li class="point" id="{e(p['id'].lower())}">
  <p class="point-question"><span class="point-id">{e(p['id'])}</span> {e(p['question'])}</p>
  <p class="point-preuve"><span>À demander</span><span class="v">{e(p['preuve'])}</span></p>
  <p class="point-sources"><span>{pluriel(len(p['sources']), 'décision', 'décisions')}</span><span class="v">{refs}</span></p>
</li>""")
        sections.append(f"""<section id="c{k}">
<h2>{e(nom)}</h2>
<p class="avertissement">Manquement retenu dans {sanctionnees[cat]} des {chiffres['nb_decisions']} décisions étudiées.</p>
<ol class="points">{''.join(items)}</ol>
</section>""")

    # La même liste en tableau, à télécharger.
    (SORTIE / "telechargements").mkdir(parents=True, exist_ok=True)
    etude.ecrire_csv(donnees, SORTIE / "telechargements" / "points-de-controle.csv")

    relue = "" if donnees["redaction"].get("relu_par_mateo") else " Elle n'a pas encore été relue point par point."
    contenu = f"""<div class="titre-page">
  <h1>Points de contrôle</h1>
  <p class="chapo">{len(donnees['points'])} questions à se poser sur un dispositif de lutte contre le blanchiment
  et de gel des avoirs, tirées de ce que la Commission des sanctions de l'ACPR a réellement sanctionné.</p>
</div>
<div class="fiche">
<nav class="sommaire" aria-label="Catégories">
  <p>Catégories</p>
  <ul class="sommaire-points">{''.join(sommaire)}</ul>
</nav>
<div class="fiche-corps points-corps">
<div class="texte">
<p><strong>Ces points ne sont pas écrits par l'ACPR.</strong> Ils sont déduits des griefs que sa Commission des
sanctions a retenus, en entier ou en partie, dans les {chiffres['nb_decisions']} décisions de
l'<a href="analyse.html">étude</a>. Chaque point renvoie aux décisions qui l'illustrent : le numéro mène au
grief concerné. La ligne « À demander » suggère ce qu'un contrôleur peut réclamer comme preuve ; c'est une
proposition, pas une exigence réglementaire.</p>
<p>La liste a été établie avec Claude à partir des fiches, le {ETUDE_DATE}.{relue} Elle ne couvre que ce
qui a été sanctionné : un sujet absent n'est pas un sujet sans risque.</p>
<p><a class="bouton" href="telechargements/points-de-controle.csv" download>Télécharger la liste (CSV, pour Excel)</a></p>
</div>
{''.join(sections)}
</div>
</div>"""
    page("points-de-controle.html", "Points de contrôle", contenu,
         f"{len(donnees['points'])} points de contrôle LCB-FT et gel des avoirs, déduits des décisions de "
         "sanction de l'ACPR.", collecte, actif="points-de-controle.html")


def pages_fixes(lignes, collecte):
    avec_fiche = [l for l in lignes if l["fiche"]]
    relues = sum(1 for l in avec_fiche
                 if l["fiche"]["redaction"].get("relue_par_mateo") or l["fiche"]["suivi"]["statut"] == "lue")
    valeurs = {
        "nb_decisions": len(lignes), "nb_fiches": len(avec_fiche), "nb_relues": relues,
        "nb_lcbft": sum(1 for l in lignes if l["lcbft"]),
        "categories": "".join(f"<li>{e(majuscule(c))}</li>" for c in CATEGORIES),
        "date_collecte": date_en_clair(max(c["date"] for c in collecte.values())),
        "nb_acpr": sum(1 for l in lignes if l["regulateur"] == "ACPR"),
        "nb_amf": sum(1 for l in lignes if l["regulateur"] == "AMF"),
        "nb_lcbft_acpr": sum(1 for l in lignes if l["regulateur"] == "ACPR" and l["lcbft"]),
        "nb_lcbft_amf": sum(1 for l in lignes if l["regulateur"] == "AMF" and l["lcbft"]),
    }
    page("methode.html", "Méthode", re.sub(r"\A<!--.*?-->\s*", "", gabarit("methode.html", valeurs), flags=re.S),
         "Sources, grille d'analyse, mise à jour et limites du projet.", collecte, actif="methode.html")
    etude_pages(lignes, valeurs, collecte)
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
    page("404.html", "Page introuvable", """<div class="titre-page"><h1>Page introuvable</h1>
<p class="chapo">Cette adresse ne correspond à aucune page du site. La fiche a peut-être changé d'adresse,
ou elle a été retirée le temps d'être mise à jour.</p></div>
<p><a class="bouton" href="base.html">Aller à la base des décisions</a></p>""".replace(
        'href="base.html"', f'href="{ADRESSE_SITE}base.html"'),
         "Page introuvable.", collecte, absolu=True)

    nb = sum(1 for l in lignes if l["fiche"])
    print(f"Site fabriqué dans _site/ : {len(lignes)} décisions, {nb} fiches publiées.")
    ALERTES.write_text("\n".join(alertes), encoding="utf-8")
    for a in alertes:
        print("ALERTE " + a)


if __name__ == "__main__":
    principal()
