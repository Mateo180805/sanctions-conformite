"""
Collecte des décisions de la Commission des sanctions de l'AMF.

Comment le site est organisé (vérifié le 13 novembre 2026) :
  1. La page « Décisions de la Commission des sanctions » affiche un tableau.
     Ce tableau est rempli par une adresse du site qui renvoie toute la liste
     d'un coup, dans un format structuré (JSON) : c'est elle qu'on lit. Une
     seule requête suffit donc pour savoir s'il y a du nouveau.
  2. Chaque ligne donne : le numéro de la décision (« SAN-2026-07 »), le thème,
     les personnes sanctionnées, le montant total avant recours, s'il y a un
     recours, et le lien vers le PDF.
  3. La date de la décision n'est pas dans la liste : on la lit dans le PDF.

Deux différences voulues avec l'ACPR :

  - LES PERSONNES PHYSIQUES. L'AMF sanctionne souvent des particuliers (un
    dirigeant, un initié) et publie leur nom pendant une durée limitée, cinq ans
    en général, avant de l'effacer. La base ne reprend donc JAMAIS le nom d'une
    personne physique : elle garde le nom des sociétés et le nombre de personnes
    physiques (« Société X et 2 personnes physiques »).

  - LE TEXTE DES DÉCISIONS. Pour la même raison, le texte complet n'est pas
    copié dans le dépôt (GARDER_TEXTE = False) : un dépôt public garde tout
    indéfiniment dans son historique, même après une anonymisation. Le PDF est
    lu pour en tirer la date, le nombre de pages et un indice « parle de
    blanchiment », puis il n'est pas conservé. Pour rédiger une fiche, on relit
    le PDF officiel (fonction texte_d_une_decision, en bas de ce fichier).

Comme pour l'ACPR, le module fournit NOM, MINIMUM_ATTENDU, lister() et collecter().
"""

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from urllib.parse import unquote, urljoin

from commun import (
    ErreurCollecte, MOTIF_DATE, assembler_pages, date_iso, empreinte,
    montants_en_euros, nettoyer, telecharger, texte_du_pdf,
)

NOM = "AMF"
SITE = "https://www.amf-france.org"
URL_PAGE_LISTE = SITE + "/fr/sanction-transaction/Decisions-de-la-commission-des-sanctions"

# L'adresse que la page officielle interroge pour remplir son tableau. Les nombres
# sont les identifiants des thèmes ; « all/all » veut dire « toutes les dates ».
# Ils sont relus sur la page à chaque collecte (voir lister) ; cette valeur ne sert
# que de secours.
THEMES_PAR_DEFAUT = "91,184,183,325,90,461,89,242,86,462,181"
URL_LISTE = SITE + "/fr/rest/listing_sanction/{themes}/all/all"

# Période couverte : comme pour l'ACPR (première décision en janvier 2011), on garde
# les décisions numérotées à partir de 2011. La loi de régulation bancaire et
# financière du 22 octobre 2010 a profondément changé les sanctions de l'AMF
# (plafond porté à 100 millions d'euros) : les décisions plus anciennes appliquent
# un cadre dépassé.
PREMIERE_ANNEE = 2011

# Exceptions : décisions plus anciennes gardées parce qu'elles restent instructives.
GARDEES_AVANT_2011 = {
    # Les cinq montants totaux les plus élevés d'avant 2011 (de 4 à 9,6 millions d'euros).
    "SAN-2006-14": "plus forte sanction totale d'avant 2011 (manipulation de marché)",
    "SAN-2007-19": "manquement d'initié, 6,25 millions d'euros",
    "SAN-2009-09": "manquement d'initié, 5,55 millions d'euros",
    "SAN-2007-16": "obligation d'information, 5,1 millions d'euros",
    "SAN-2010-04": "manquement d'initié, 4 millions d'euros",
    # Les deux décisions anciennes qui portent nettement sur la lutte contre le blanchiment.
    "SAN-2009-22": "lutte contre le blanchiment",
    "SAN-2009-01": "lutte contre le blanchiment",
}

# La liste officielle comptait 454 décisions le 13 novembre 2026 (depuis 2004) ;
# on en garde 280 (de 2011 à 2026, plus les exceptions).
MINIMUM_ATTENDU = 250

# Le texte des décisions n'est pas enregistré dans le dépôt (voir en haut du fichier).
GARDER_TEXTE = False

# Nombre de fois où le PDF doit parler de blanchiment pour que la décision soit
# signalée comme touchant à la LCB-FT. Ce n'est qu'un indice pour trier.
SEUIL_LCBFT = 3
MOTIF_LCBFT = r"blanchiment|financement du terrorisme"


# --- Les personnes sanctionnées ---------------------------------------------------

# Ce qui annonce une personne physique...
CIVILITE = (r"(?:MM\b\.?|M[Mm][Ee][Ss]?\b\.?|M[Ll][Ll][Ee][Ss]?\b\.?|Melles?\b\.?|M\.|M\s+(?=[A-Z]\b)|"
            r"Messieurs|Mesdames|Monsieur|Madame|Mademoiselle)")

# Lignes de la liste officielle qui ne suivent pas la forme habituelle, corrigées à la main
# (numéro de la décision -> désignation à utiliser à la place).
CORRECTIONS = {
    # « Demande de relèvement de M. A de l'interdiction ... » : une personne physique.
    "SAN-2018-20": "M. A",
}
# ... et ce qui annonce une personne morale (une société, un cabinet...).
MORALE = (r"(?:soci[ée]t[ée]s?|cabinets?|banques?|associations?|fonds|groupes?|caisses?|"
          r"compagnies?|mutuelles?|[ée]tablissements?|entit[ée]s?|succursales?)\b")
# Précisions qui suivent parfois un nom de personne (« M. A, gérant de la société X »).
QUALITE = (r"(?:co-?)?g[ée]rants?\b|pr[ée]sidents?\b|directeurs?\b|directrices?\b|dirigeants?\b|"
           r"administrateurs?\b|anciens?\b|anciennes?\b|en (?:sa|leur) qualit[ée]|"
           r"repr[ée]sentants?\b|salari[ée]s?\b|analystes?\b|commissaires?\b")


def lire_personnes(texte_egard):
    """Sépare les sociétés des personnes physiques dans la colonne « à l'égard de ».

    Renvoie (texte des sociétés, nombre de personnes physiques, au moins un vrai nom ?, doute ?).

    Exemple : « Sociétés Safetic, HSBC France et X et de MM. D et E »
           -> (« Sociétés Safetic, HSBC France et X », 2, True, False)

    Méthode : on découpe la phrase aux virgules, aux « et » et aux retours à la
    ligne. Un morceau qui commence par « M. », « Mme », « MM. »... ouvre une
    série de personnes physiques ; un morceau qui contient « société »,
    « cabinet »... ouvre une série de sociétés ; un morceau sans indice continue
    la série en cours. Les noms de personnes physiques ne sont pas gardés.
    """
    if nettoyer(texte_egard) in ("", "-", "n/a"):
        return "", 0, False, True
    texte = html.unescape(re.sub(r"<br\s*/?>", "\n", texte_egard or ""))
    texte = re.sub(r"<[^>]+>", " ", texte).replace("\r", "")
    # Les parenthèses (« anciennement dénommée Y ») ne doivent pas être découpées.
    texte = re.sub(r"\([^)]*\)", lambda m: m.group(0).replace(",", "‚").replace(" et ", " & "), texte)
    morceaux = re.split(r"(\n+|\s*;\s*|\s*,\s*|\s+ainsi\s+que\s+(?:de\s+|d['’])?|\s+et\s+(?:de\s+|d['’])?)", texte)

    groupes, ouvert = [], False     # groupes de sociétés ; ouvert : le dernier groupe continue
    serie = None                    # "physique", "morale" ou None (début)
    physiques, vrai_nom, doute = 0, False, False
    for i in range(0, len(morceaux), 2):
        morceau = morceaux[i].strip()
        separateur = morceaux[i - 1] if i else ""
        if not morceau:
            continue
        sans_article = re.sub(r"^(?:et\s+|de\s+|d['’]|à\s+|aux?\s+|la\s+|les?\s+|l['’])+", "", morceau, flags=re.I)
        if serie == "physique" and re.match(QUALITE, sans_article, re.I):
            continue                # « gérant de la société X » : précision sur la personne
        if re.match(CIVILITE, sans_article):
            serie = "physique"
        elif re.search(MORALE, morceau, re.I):
            serie = "morale"
        elif serie is None:
            serie, doute = "morale", True   # ni « société » ni « M. » : à vérifier

        if serie == "physique":
            nom = re.sub("^" + CIVILITE, "", sans_article).strip(" .")
            physiques += 1
            ouvert = False          # la société suivante commencera un nouveau groupe
            if len(re.sub(r"[^A-Za-zÀ-ÿ]", "", nom)) > 2:
                vrai_nom = True     # « Pierre Dupont » et non « A » : décision nominative
        elif ouvert:
            lien = " et " if re.search(r"\bet\b|ainsi", separateur) else ", "
            groupes[-1] += lien + morceau
        else:
            groupes.append(morceau)
            ouvert = True

    # « la société X » -> « Société X » au début de chaque groupe.
    groupes = [re.sub(r"^(?:de\s+|à\s+)?(?:la|les|l['’])\s*(?=soci)", "", g, flags=re.I) for g in groupes]
    groupes = [g[:1].upper() + g[1:] for g in groupes]
    texte_societes = nettoyer(", ".join(groupes).replace("‚", ",").replace(" & ", " et "))
    texte_societes = re.sub(r"(,\s*|\s+et\s+)(?:la|les|l['’])\s*(?=soci)", r"\1", texte_societes, flags=re.I)

    # Les sociétés sont-elles nommées, ou désignées par une lettre (« Société X ») ?
    noms = re.sub(MORALE, " ", re.sub(r"\([^)]*\)", " ", texte_societes), flags=re.I)
    noms = [n for n in re.split(r"[\s,;]+|\bet\b|\bla\b|\bles?\b|\bde\b", noms) if n]
    if any(len(re.sub(r"[^A-Za-zÀ-ÿ0-9]", "", n)) > 2 for n in noms):
        vrai_nom = True
    return texte_societes, physiques, vrai_nom, doute


def nom_pour_le_site(texte_societes, physiques):
    """« Société X et 2 personnes physiques », « 3 personnes physiques »..."""
    personnes = ""
    if physiques:
        personnes = f"{physiques} personne{'s' if physiques > 1 else ''} physique{'s' if physiques > 1 else ''}"
    societes = texte_societes
    if societes and personnes:
        return f"{societes} et {personnes}"
    return societes or personnes or "Non précisé"


# --- Étape 1 : la liste ----------------------------------------------------------

def texte_simple(code):
    """« <p>30 000 €<br>1 blâme</p> » -> [« 30 000 € », « 1 blâme »]"""
    lignes = re.split(r"<br\s*/?>|</p>|\n", code or "")
    lignes = [nettoyer(html.unescape(re.sub(r"<[^>]+>", " ", l))) for l in lignes]
    return [l for l in lignes if l]


def lister():
    """Lit la liste officielle et renvoie une entrée par décision.

    Les entrées ne contiennent aucun nom de personne physique. Pour savoir si une
    ligne a changé (anonymisation, PDF remplacé), on garde une « empreinte » de
    la ligne : un code calculé à partir de son contenu, qui change dès que la
    ligne change, sans rien révéler de ce qu'elle contient.
    """
    # Les identifiants des thèmes sont écrits dans la page officielle : on les relit.
    page = telecharger(URL_PAGE_LISTE).content.decode("utf-8", errors="replace")
    trouve = re.search(r'name="filtre"[^>]*value="([\d,]+)"', page)
    themes = trouve.group(1) if trouve else THEMES_PAR_DEFAUT

    reponse = telecharger(URL_LISTE.format(themes=themes))
    try:
        lignes = json.loads(reponse.content.decode("utf-8"))["data"]
    except (ValueError, KeyError, TypeError):
        raise ErreurCollecte("Liste AMF : réponse illisible, le site a sans doute changé.")

    entrees = []
    for ligne in lignes:
        try:
            infos = ligne["infos"]
            numero = infos["title"].strip()
            url_page = infos["link"]["url"]
            pdf = infos["download"]["sanction"]["links"]["url"]
            societes, physiques, vrai_nom, doute = lire_personnes(CORRECTIONS.get(numero, infos["text_egard"]))
            sanction = texte_simple(infos["text"])
            recours = (infos.get("recours") or "").strip().lower() == "oui"
            theme = html.unescape(ligne.get("theme") or "")
            publie = datetime.fromtimestamp(int(ligne["date"]), timezone.utc).date().isoformat()
        except (KeyError, TypeError, ValueError) as erreur:
            raise ErreurCollecte(f"Liste AMF : ligne au format inattendu ({erreur}).")
        if not re.fullmatch(r"SAN-\d{4}-\d{1,3}", numero):
            raise ErreurCollecte(f"Liste AMF : numéro de décision inattendu (« {numero[:40]} »).")

        entrees.append({
            "numero": numero,
            "titre_liste": f"{numero} – {theme}",
            "themes_liste": theme,
            "annee_recueil": numero.split("-")[1],
            "urls_page": [urljoin(SITE, url_page)],
            "url_pdf": urljoin(SITE, pdf) if pdf else None,
            "societes": societes,
            "personnes_physiques": physiques,
            "nominative": vrai_nom,
            "designation_douteuse": doute,
            "sanction_lignes": sanction,
            "date_publication": publie,
            "suites": [{"texte": "Recours formé contre la décision (indiqué dans la liste de l'AMF)", "url": None}]
                      if recours else [],
            # Empreinte de la ligne : personnes, sanction et adresse du PDF.
            "empreinte_ligne": hashlib.sha256(json.dumps(
                [infos["text_egard"], infos["text"], pdf], ensure_ascii=False).encode("utf-8")).hexdigest()[:16],
        })

    # Seulement la période couverte, plus les exceptions.
    entrees = [e for e in entrees
               if int(e["annee_recueil"]) >= PREMIERE_ANNEE or e["numero"] in GARDEES_AVANT_2011]

    # Du plus ancien au plus récent, comme pour l'ACPR.
    entrees.sort(key=lambda e: [int(x) for x in e["numero"].split("-")[1:]])
    return entrees


# --- Étape 2 : une décision -------------------------------------------------------

def date_dans_adresse(url):
    """« ...-du-6-mai-2014-... » ou « ...du%206%20mai%202014... » -> « 2014-05-06 »."""
    lisible = re.sub(r"[-_]+", " ", unquote(url or ""))
    trouve = re.search(r"\bdu\s+" + MOTIF_DATE, lisible)
    return date_iso(trouve.group(0)) if trouve else None


def lire_pdf(pages):
    """Tire du texte de la décision : date, séance, numéro de procédure, indice LCB-FT."""
    complet = "\n".join(pages)
    debut = pages[0] if pages else ""
    resultat = {"date_decision": None, "date_audience": None, "procedure": None, "mentions_lcbft": 0}

    # La date : « Décision n° 6 du 21 juillet 2026 » en première page (forme récente),
    # sinon la dernière mention « Fait à Paris, le ... » ou « A Paris, le ... » (formes anciennes).
    en_tete = re.search(r"D[ée]cision\s+n\s*[°ºo]\s*\d+\s+du\s+" + MOTIF_DATE, debut, re.I)
    if en_tete:
        resultat["date_decision"] = date_iso(en_tete.group(0))
    else:
        fins = re.findall(r"(?:Fait\s+)?[àÀA]\s+Paris,?\s+le\s+" + MOTIF_DATE, complet, re.I)
        if fins:
            jour, mois, annee = fins[-1]
            resultat["date_decision"] = date_iso(f"{jour} {mois} {annee}")

    seance = re.search(r"s[ée]ance\s+(?:publique\s+|non\s+publique\s+)?du\s+" + MOTIF_DATE, complet, re.I)
    if seance:
        resultat["date_audience"] = date_iso(seance.group(0))
    procedure = re.search(r"Proc[ée]dure\s+n\s*[°ºo]\s*(\d{2,4}\s*[-/]\s*\d{1,3})", debut, re.I)
    if procedure:
        resultat["procedure"] = re.sub(r"\s+", "", procedure.group(1))
    resultat["mentions_lcbft"] = len(re.findall(MOTIF_LCBFT, complet, re.I))
    return resultat


def telecharger_pages(url_pdf):
    """Télécharge le PDF et renvoie (contenu, texte de chaque page)."""
    contenu = telecharger(url_pdf).content
    if not contenu.startswith(b"%PDF"):
        raise ErreurCollecte(f"Le fichier reçu n'est pas un PDF : {url_pdf}")
    return contenu, texte_du_pdf(contenu)


def collecter(entree):
    """Télécharge une décision et renvoie (fiche de base, texte ou None)."""
    alertes = []
    numero = entree["numero"]
    url_page, url_pdf = entree["urls_page"][0], entree["url_pdf"]

    pages, contenu = [], None
    if url_pdf:
        contenu, pages = telecharger_pages(url_pdf)
        if sum(len(p) for p in pages) < 1000:
            alertes.append("Très peu de texte extrait : PDF probablement scanné, à lire directement.")
    else:
        alertes.append("Aucun PDF dans la liste de l'AMF pour cette décision.")
    lu = lire_pdf(pages)

    # La date : celle du PDF, vérifiée avec celle écrite dans l'adresse quand il y en a une.
    date_adresse = date_dans_adresse(url_page) or date_dans_adresse(url_pdf)
    date_decision = lu["date_decision"] or date_adresse
    if not date_decision:
        alertes.append("Date de la décision non trouvée : à lire dans le PDF.")
    elif not lu["date_decision"]:
        alertes.append("Date prise dans l'adresse de la page (non trouvée dans le PDF).")
    elif date_adresse and date_adresse != lu["date_decision"]:
        alertes.append(f"La date lue dans le PDF ({lu['date_decision']}) diffère de celle de l'adresse "
                       f"de la page ({date_adresse}) : à vérifier.")
    if date_decision and not (int(numero[4:8]) - 2 <= int(date_decision[:4]) <= int(numero[4:8]) + 1):
        alertes.append(f"La date lue ({date_decision}) est loin de l'année du numéro {numero} : à vérifier.")

    # Les personnes : sociétés nommées, personnes physiques comptées.
    societes, physiques = entree["societes"], entree["personnes_physiques"]
    if entree["designation_douteuse"]:
        alertes.append("Désignation sans « société » ni « M. » : vérifier qu'il ne s'agit pas d'une personne physique.")
    nom_site = nom_pour_le_site(societes, physiques)

    # La sanction : le montant est le total avant recours, toutes personnes confondues.
    lignes = [l for l in entree["sanction_lignes"] if l not in ("-", "n/a")]
    montants = montants_en_euros(" ; ".join(lignes))
    montant = montants[0] if len(montants) == 1 else None
    if len(montants) > 1:
        alertes.append("Plusieurs montants dans la liste : montant à saisir à la main.")
    sanction = " ; ".join(lignes) or None
    if montant is not None and sanction:
        sanction = "Sanction pécuniaire, total avant recours : " + sanction

    mentions = lu["mentions_lcbft"]
    fiche = {
        "id": None,  # attribué par lancer.py : « AMF-SAN-2026-07 »
        "regulateur": NOM,
        "numero_procedure": numero,          # pour l'AMF : le numéro officiel de la décision
        "numeros_lies": [],
        "procedure_interne": lu["procedure"],
        "date_decision": date_decision,
        "date_audience": lu["date_audience"],
        "date_publication": entree["date_publication"],
        "etablissement": societes or None,
        "nom_site": nom_site,
        "personnes_physiques": physiques,
        "designation_officielle": nom_site,
        "publication": "nominative" if entree["nominative"] else "anonymisée",
        "sanction_texte": sanction,
        "montant_euros": montant,
        "themes_liste": entree["themes_liste"],
        "theme_court": entree["themes_liste"],
        "lcbft_indice": mentions >= SEUIL_LCBFT,
        "lcbft_mentions": mentions,
        "titre_liste": entree["titre_liste"],
        "empreinte_ligne": entree["empreinte_ligne"],
        "annee_recueil": entree["annee_recueil"],
        "url_page": url_page,
        "urls_page": entree["urls_page"],
        "url_pdf": url_pdf,
        "autres_pdf": [],
        "empreinte_pdf": empreinte(contenu) if contenu else None,
        "nb_pages": len(pages) or None,
        "en_tete_brut": None,
        "note_en_tete": None,
        "suites": entree["suites"],
        "lignes_recueil_incoherentes": [],
        "alertes": alertes,
        "statut": "à lire",
        "mes_notes": "",
    }
    return fiche, (assembler_pages(pages) if GARDER_TEXTE and pages else None)


def texte_d_une_decision(fiche):
    """Pour travailler sur une décision : retélécharge son PDF et renvoie le texte complet."""
    if not fiche.get("url_pdf"):
        raise ErreurCollecte(f"{fiche['id']} : pas de PDF connu.")
    return assembler_pages(telecharger_pages(fiche["url_pdf"])[1])
