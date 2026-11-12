"""
Collecte des décisions de la Commission des sanctions de l'ACPR.

Comment le site est organisé (vérifié le 12 novembre 2026) :
  1. Une seule page, le « Recueil des sanctions », liste toutes les décisions
     depuis 2011, classées par année puis par mois.
  2. Chaque ligne de cette liste renvoie vers une page de publication.
  3. Cette page contient un lien « Télécharger » vers le PDF de la décision
     (et parfois, en plus, des arrêts du Conseil d'État).
  4. La première page du PDF commence par un en-tête, placé dans la moitié
     droite : établissement, numéro de procédure, sanction, date d'audience,
     date de la décision. La moitié gauche contient parfois une note sur un
     recours.

Le programme suit ce chemin, sans jamais deviner une adresse.

Chaque module de régulateur fournit les mêmes éléments : NOM, MINIMUM_ATTENDU,
lister() et collecter(). C'est ce qui permettra d'ajouter l'AMF, la CSSF et la
FINMA sans modifier le reste.
"""

import io
import re
from urllib.parse import urljoin

import pdfplumber

from commun import (
    ErreurCollecte, MOTIF_DATE, assembler_pages, date_iso, empreinte,
    montants_en_euros, nettoyer, page_html, telecharger, texte_du_pdf,
)

NOM = "ACPR"
URL_LISTE = "https://acpr.banque-france.fr/fr/reglementation/recueil-des-sanctions"

# Le recueil comptait 113 lignes de décision le 12 novembre 2026. Si on en trouve
# beaucoup moins, c'est que la page a changé : on préfère s'arrêter que croire
# qu'il n'y a rien de nouveau.
MINIMUM_ATTENDU = 100

# « n° 2024-06 », « no 2010-06 », « n°2025-01 »
MOTIF_NUMERO = r"n\s*[°ºo]\s*(\d{4})\s*[-–]\s*(\d{1,2})"

# Mots de la liste qui signalent un dossier LCB-FT ou gel des avoirs.
# Ce n'est qu'un indice pour trier : la fiche dira ce qu'il en est vraiment.
MOTS_LCBFT = ("blanchiment", "gel des avoirs", "lcb", "financement du terrorisme")

# Débuts de ligne qui annoncent une sanction (ou une autre issue) dans l'en-tête.
DEBUT_SANCTION = (
    r"(Avertissement|Bl[âa]me|Sanction|Interdiction|Radiation|Retrait|Suspension|"
    r"Mise hors de cause|Abandon|D[ée]cision de renvoi|Non-lieu|Rejet|\d+ ans? d['’]interdiction)"
)


# --- Étape 1 : la liste ----------------------------------------------------------

def lister():
    """Lit le Recueil des sanctions et renvoie une entrée par ligne de décision.

    Chaque entrée contient : le titre, les thèmes entre parenthèses, l'année, les
    adresses des pages de publication et les suites (recours, arrêts du Conseil
    d'État) indiquées sous la décision.
    """
    contenu = page_html(URL_LISTE).find("main")
    if contenu is None:
        raise ErreurCollecte("Recueil ACPR : zone principale de la page introuvable.")

    entrees = []
    annee = None
    for element in contenu.find_all(["h2", "li"]):
        if element.name == "h2":
            titre = element.get_text(strip=True)
            if re.fullmatch(r"\d{4}", titre):
                annee = titre
            continue
        if element.find_parent("li") is not None:
            continue  # ligne imbriquée : c'est une suite, traitée avec sa décision

        # Les suites (recours...) sont dans une sous-liste : on les met de côté.
        suites = []
        for sous_ligne in element.find_all("li"):
            lien = sous_ligne.find("a", href=True)
            suites.append({
                "texte": nettoyer(sous_ligne.get_text(" ")),
                "url": urljoin(URL_LISTE, lien["href"]) if lien else None,
            })
        for sous_liste in element.find_all("ul"):
            sous_liste.extract()

        texte = nettoyer(element.get_text(" "))
        liens = [a for a in element.find_all("a", href=True) if not a["href"].startswith("#")]
        if not liens:
            continue  # sommaire des années, menus...

        if not re.match(r"d[ée]cision", texte, re.I):
            # Ligne isolée qui n'est pas une décision (arrêt du Conseil d'État) :
            # on la rattache à la décision qui la précède dans la liste.
            if entrees:
                entrees[-1]["suites"].append({
                    "texte": texte + " [rattachement automatique, à vérifier]",
                    "url": urljoin(URL_LISTE, liens[0]["href"]),
                })
            continue

        titre = nettoyer(" ".join(a.get_text(" ") for a in liens))
        themes = nettoyer(texte.replace(titre, "", 1)).strip(" ().")
        if not themes:
            # Parfois les thèmes sont dans le lien lui-même : « ... (thèmes) »
            coupe = re.match(r"(.*?)\s*\((.+)\)\.?$", titre)
            if coupe:
                titre, themes = coupe.groups()

        urls = []
        for a in liens:
            url = urljoin(URL_LISTE, a["href"])
            if url not in urls:
                urls.append(url)

        entrees.append({
            "titre_liste": titre,
            "themes_liste": themes,
            "annee_recueil": annee,
            "urls_page": urls,
            "suites": suites,
        })

    # Du plus ancien au plus récent : si deux décisions portent le même numéro de
    # procédure, la plus ancienne garde l'identifiant simple.
    entrees.reverse()
    return entrees


# --- Étape 2 : une décision -------------------------------------------------------

def trouver_pdf(url_page):
    """Sur la page de publication, renvoie (PDF de la décision, autres PDF, alertes)."""
    if url_page.lower().split("?")[0].endswith(".pdf"):
        return url_page, [], []  # la ligne de la liste pointe directement vers le PDF
    contenu = page_html(url_page).find("main")
    pdfs = []
    for a in (contenu.find_all("a", href=True) if contenu else []):
        if ".pdf" in a["href"].lower():
            url = urljoin(url_page, a["href"])
            if url not in [u for u, _ in pdfs]:
                pdfs.append((url, nettoyer(a.get_text(" "))))
    if not pdfs:
        raise ErreurCollecte(f"Aucun PDF trouvé sur {url_page} : à regarder à la main.")
    alertes = []
    if len(pdfs) > 1:
        # Le premier document est la décision ; les suivants sont des arrêts liés.
        alertes.append(
            f"{len(pdfs)} PDF sur la page officielle : le premier a été pris comme décision, à vérifier."
        )
    return pdfs[0][0], [u for u, _ in pdfs[1:]], alertes


def zones_en_tete(contenu_pdf):
    """Découpe le haut de la première page : (moitié droite, moitié gauche).

    L'en-tête de la décision est dans la moitié droite, au-dessus de la ligne
    « AUTORITÉ DE CONTRÔLE PRUDENTIEL ». Renvoie (None, None) si cette ligne
    est introuvable.
    """
    with pdfplumber.open(io.BytesIO(contenu_pdf)) as pdf:
        page = pdf.pages[0]
        limite = next(
            (mot["top"] for mot in page.extract_words() if mot["text"].startswith("AUTORIT")), None
        )
        if limite is None or limite < 20:
            return None, None
        limite -= 3  # petite marge : on s'arrête juste au-dessus de cette ligne
        milieu = page.width / 2
        droite = page.crop((milieu, 0, page.width, limite)).extract_text() or ""
        gauche = page.crop((0, 0, milieu, limite)).extract_text() or ""
        return droite, gauche


def lire_en_tete(droite, gauche):
    """Lit l'en-tête de la décision.

    Forme habituelle (moitié droite du haut de la première page) :
        NOM DE L'ÉTABLISSEMENT
        Procédure no 2024-06
        Blâme et sanction pécuniaire de 1,3 million d'euros
        Publication sous une forme nominative pendant 5 ans
        Audience du 19 mars 2026
        Décision rendue le 15 avril 2026

    Tout ce qui n'est pas trouvé reste vide et une alerte est ajoutée : le
    programme ne complète jamais par une supposition.
    """
    resultat = {
        "numero_procedure": None, "numeros_lies": [], "nom_en_tete": None,
        "sanction_texte": None, "montant_euros": None,
        "date_audience": None, "date_decision": None,
        "en_tete_brut": None, "note_en_tete": None,
    }
    alertes = []
    if droite is None:
        alertes.append("En-tête non reconnu : numéro, sanction et dates à vérifier dans le PDF.")
        return resultat, alertes

    # On retire les traits de séparation et le titre courant répété en haut de page.
    lignes = [
        l.strip() for l in droite.splitlines()
        if re.search(r"[A-Za-zÀ-ÿ0-9]{2}", l) and "Commission des sanctions" not in l
    ]
    resultat["en_tete_brut"] = " | ".join(lignes)
    bloc = " ".join(lignes)

    # Note de la moitié gauche (souvent : « X a formé un recours devant le Conseil d'État »).
    note = nettoyer(" ".join(
        l for l in (gauche or "").splitlines()
        if len(l.strip()) > 3 and not l.strip().startswith("Décision de la Co")
    ))
    resultat["note_en_tete"] = note or None

    # On range chaque ligne : procédure, dates, sanction ou nom.
    est_procedure = lambda l: re.match(r"(Proc[ée]dures?\b|n[o°º0]\s*\d{4}\s*[-–])", l, re.I)
    est_date = lambda l: re.match(r"(Audience|Audition|D[ée]cision rendue|Rendue|\d{4}$)", l, re.I)

    # Numéro(s) de procédure
    numeros = []
    for ligne in filter(est_procedure, lignes):
        for annee, rang in re.findall(r"(\d{4})\s*[-–]\s*(\d{1,2})", ligne):
            numero = f"{annee}-{int(rang):02d}"
            if numero not in numeros:
                numeros.append(numero)
    if numeros:
        resultat["numero_procedure"] = numeros[0]
        resultat["numeros_lies"] = numeros[1:]
    else:
        alertes.append("Numéro de procédure absent de l'en-tête.")

    # Dates
    audience = re.search(r"(?:Audiences?|Audition)\s+(?:du|des)\s+" + MOTIF_DATE, bloc, re.I)
    if audience:
        resultat["date_audience"] = date_iso(audience.group(0))
    rendue = re.search(r"rendue\s+le\s+" + MOTIF_DATE, bloc, re.I)
    if rendue:
        resultat["date_decision"] = date_iso(rendue.group(0))
    else:
        alertes.append("Date de la décision absente de l'en-tête.")

    # Nom et sanction : le nom est au début ; la sanction commence à la première
    # ligne qui ressemble à une sanction (« Blâme », « Avertissement »...).
    reste = [l for l in lignes if not est_procedure(l) and not est_date(l)]
    debut = next((i for i, l in enumerate(reste) if re.match(DEBUT_SANCTION, l, re.I)), None)
    if debut is None:
        resultat["nom_en_tete"] = " ".join(reste) or None
        alertes.append("Sanction absente de l'en-tête : à lire dans le dispositif de la décision.")
    else:
        resultat["nom_en_tete"] = " ".join(reste[:debut]) or None
        resultat["sanction_texte"] = " ".join(reste[debut:])
        montants = montants_en_euros(resultat["sanction_texte"])
        if len(montants) == 1:
            resultat["montant_euros"] = montants[0]
        elif len(montants) > 1:
            alertes.append("Plusieurs montants dans l'en-tête (plusieurs personnes sanctionnées) : montant à saisir à la main.")

    return resultat, alertes


def collecter(entree):
    """Télécharge une décision et renvoie (fiche de base, texte complet).

    Les champs lus automatiquement dans l'en-tête sont à vérifier à la lecture :
    c'est le rôle du champ « alertes ».
    """
    url_page = entree["urls_page"][0]
    url_pdf, autres_pdf, alertes = trouver_pdf(url_page)
    contenu = telecharger(url_pdf).content
    pages = texte_du_pdf(contenu)
    en_tete, alertes_en_tete = lire_en_tete(*zones_en_tete(contenu))
    alertes += alertes_en_tete

    if sum(len(p) for p in pages) < 1000:
        alertes.append("Très peu de texte extrait : PDF probablement scanné, à lire directement.")

    titre = entree["titre_liste"]

    # Le numéro : d'abord l'en-tête du PDF, sinon le titre de la liste.
    numero = en_tete["numero_procedure"]
    if not numero:
        dans_titre = re.search(MOTIF_NUMERO, titre)
        if dans_titre:
            numero = f"{dans_titre.group(1)}-{int(dans_titre.group(2)):02d}"

    # La date : d'abord l'en-tête du PDF. Le titre de la liste donne parfois la
    # date de l'audience et non celle de la décision.
    date_decision = en_tete["date_decision"]
    if not date_decision:
        date_decision = date_iso(titre)
        if date_decision:
            alertes.append("Date prise dans le titre de la liste (peut être la date d'audience).")

    # L'établissement : ce qui suit « à l'égard de » (ou « à l'encontre de ») dans
    # le titre officiel ; à défaut, le nom écrit dans l'en-tête du PDF.
    designation = None
    apres = re.search(r"à\s+(?:l\s*['’]\s*)?(?:[ée]gard|encontre)\s+(.*)$", titre, re.I)
    if apres:
        designation = re.sub(r"^(de la |de l['’]\s*|du |des |de |d['’]\s*)", "", apres.group(1), flags=re.I).strip()
    else:
        designation = en_tete["nom_en_tete"]

    # Nominative ou anonymisée ? On croise deux indices :
    #   - la désignation officielle se termine par une lettre seule (« société A », « [A] ») ;
    #   - le nom du fichier PDF contient « anonymis ».
    nom_court = (designation or "").split(",")[0].split("(")[0].strip()
    lettre_seule = bool(re.search(r"(^|\s)\[?[A-Z]\]?$", nom_court))
    fichier_anonymise = bool(re.search(r"anonymis", url_pdf, re.I))
    if lettre_seule:
        publication, etablissement = "anonymisée", "anonymisé"
    elif fichier_anonymise:
        publication, etablissement = "à vérifier", designation
        alertes.append("Le fichier est dit « anonymisé » mais le titre officiel donne un nom : anonymisation partielle ? À vérifier.")
    else:
        publication, etablissement = "nominative", designation

    themes = entree["themes_liste"]
    fiche = {
        "id": None,  # attribué par lancer.py
        "regulateur": NOM,
        "numero_procedure": numero,
        "numeros_lies": en_tete["numeros_lies"],
        "date_decision": date_decision,
        "date_audience": en_tete["date_audience"],
        "etablissement": etablissement,
        "designation_officielle": designation,
        "publication": publication,
        "sanction_texte": en_tete["sanction_texte"],
        "montant_euros": en_tete["montant_euros"],
        "themes_liste": themes,
        "lcbft_indice": any(mot in (themes + " " + titre).lower() for mot in MOTS_LCBFT),
        "titre_liste": titre,
        "annee_recueil": entree["annee_recueil"],
        "url_page": url_page,
        "urls_page": entree["urls_page"],
        "url_pdf": url_pdf,
        "autres_pdf": autres_pdf,
        "empreinte_pdf": empreinte(contenu),
        "nb_pages": len(pages),
        "en_tete_brut": en_tete["en_tete_brut"],
        "note_en_tete": en_tete["note_en_tete"],
        "suites": entree["suites"],
        "lignes_recueil_incoherentes": [],
        "alertes": alertes,
        "statut": "à lire",
        "mes_notes": "",
    }
    return fiche, assembler_pages(pages)
