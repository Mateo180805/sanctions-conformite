"""
Outils communs à tous les régulateurs.

Ce fichier ne sait rien de l'ACPR, de l'AMF, etc. Il contient seulement ce dont
tous les programmes de collecte ont besoin :
  - télécharger une page ou un PDF poliment (identifiant clair, pause) ;
  - extraire le texte d'un PDF, page par page ;
  - lire des dates et des montants écrits en français ;
  - lire et enregistrer la base (donnees/decisions.json et decisions.csv).

Pour ajouter un régulateur, on n'a pas besoin de toucher à ce fichier.
"""

import csv
import hashlib
import io
import json
import os
import re
import time
from pathlib import Path

import pdfplumber
import requests
from bs4 import BeautifulSoup

# --- Emplacements des fichiers -------------------------------------------------

RACINE = Path(__file__).resolve().parent.parent      # le dossier du dépôt
DOSSIER_DONNEES = RACINE / "donnees"
FICHIER_BASE = DOSSIER_DONNEES / "decisions.json"
FICHIER_CSV = DOSSIER_DONNEES / "decisions.csv"
FICHIER_SUIVI = DOSSIER_DONNEES / "derniere_collecte.json"
DOSSIER_TEXTES = DOSSIER_DONNEES / "textes"

# --- Politesse -----------------------------------------------------------------

PAUSE_SECONDES = 2        # pause entre deux téléchargements
DELAI_MAX_SECONDES = 60   # au-delà, on considère que le site ne répond pas


def identifiant():
    """Le nom sous lequel le programme se présente aux sites (User-Agent).

    Sur GitHub Actions, la variable GITHUB_REPOSITORY contient « compte/depot » :
    le régulateur peut donc retrouver le projet et me contacter.

    Constat du 12 novembre 2026 : le site de l'ACPR est protégé par un filtre qui
    refuse (code 403) certains identifiants. Ceux ci-dessous, qui disent où
    trouver le projet, sont acceptés. On ne se fait jamais passer pour un
    navigateur : si l'identifiant est refusé un jour, on applique le plan B.
    """
    depot = os.environ.get("GITHUB_REPOSITORY")
    if depot:
        return f"projet-sanctions-conformite/1.0 (projet etudiant; +https://github.com/{depot})"
    return "projet-sanctions-conformite/1.0 (projet etudiant; contact: via GitHub)"


class ErreurCollecte(Exception):
    """Erreur expliquée en clair. Elle arrête le programme : pas d'erreur silencieuse."""


_derniere_requete = 0.0


def telecharger(url):
    """Télécharge une adresse et renvoie la réponse. Attend entre deux appels.

    Une seule nouvelle tentative en cas de panne passagère, puis on s'arrête
    avec un message clair.
    """
    global _derniere_requete
    for tentative in (1, 2):
        attente = PAUSE_SECONDES - (time.time() - _derniere_requete)
        if attente > 0:
            time.sleep(attente)
        _derniere_requete = time.time()
        try:
            reponse = requests.get(
                url,
                headers={"User-Agent": identifiant()},
                timeout=DELAI_MAX_SECONDES,
            )
        except requests.RequestException as erreur:
            if tentative == 1:
                time.sleep(15)
                continue
            raise ErreurCollecte(f"Impossible de joindre {url} : {erreur}")

        if reponse.status_code == 200:
            return reponse
        if reponse.status_code in (403, 429):
            raise ErreurCollecte(
                f"Le site refuse l'accès (code {reponse.status_code}) pour {url}. "
                "Il bloque peut-être les serveurs de GitHub : voir le plan B dans README.md "
                "(lancer la collecte depuis mon ordinateur)."
            )
        if reponse.status_code >= 500 and tentative == 1:
            time.sleep(15)
            continue
        raise ErreurCollecte(f"Réponse inattendue (code {reponse.status_code}) pour {url}.")


def page_html(url):
    """Télécharge une page web et la renvoie prête à être fouillée (BeautifulSoup)."""
    texte = telecharger(url).content.decode("utf-8", errors="replace")
    return BeautifulSoup(texte, "html.parser")


# --- PDF -----------------------------------------------------------------------

def texte_du_pdf(contenu):
    """Renvoie le texte de chaque page d'un PDF (liste : un élément par page)."""
    try:
        with pdfplumber.open(io.BytesIO(contenu)) as pdf:
            return [(page.extract_text() or "").strip() for page in pdf.pages]
    except Exception as erreur:
        raise ErreurCollecte(f"PDF illisible : {erreur}")


def assembler_pages(pages):
    """Un seul texte, avec un repère avant chaque page.

    Les repères « ===== Page 3 ===== » permettront de citer la page dans les fiches.
    """
    return "\n\n".join(f"===== Page {n} =====\n{texte}" for n, texte in enumerate(pages, 1)) + "\n"


def empreinte(contenu):
    """Empreinte du fichier : si le PDF change un jour, l'empreinte change aussi."""
    return hashlib.sha256(contenu).hexdigest()


# --- Dates et montants en français ---------------------------------------------

MOIS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5,
    "juin": 6, "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10,
    "novembre": 11, "décembre": 12, "decembre": 12,
}
MOTIF_DATE = r"(\d{1,2})\s*(?:er)?\s+([a-zéûôA-ZÉÛ]+)\s+(\d{4})"


def date_iso(texte):
    """« 1er décembre 2022 » -> « 2022-12-01 ». Renvoie None si rien de lisible."""
    trouve = re.search(MOTIF_DATE, texte or "")
    if not trouve:
        return None
    jour, mois, annee = trouve.groups()
    numero_mois = MOIS.get(mois.lower())
    if not numero_mois:
        return None
    return f"{annee}-{numero_mois:02d}-{int(jour):02d}"


def montants_en_euros(texte):
    """Renvoie tous les montants écrits en chiffres dans un texte.

    « 1,3 million d'euros » -> [1300000] ; « 800 000 euros » -> [800000].
    Un montant écrit en lettres n'est pas lu : mieux vaut « non lu » qu'un chiffre faux.
    """
    texte = (texte or "").replace("\u00a0", " ").replace("\u202f", " ")
    montants = [1_000_000 for _ in re.finditer(r"d['’]un\s+million\s+d['’]euros", texte, re.I)]
    motif = r"(\d[\d .]*(?:,\d+)?)\s*(millions?|milliards?)?\s*(?:d['’]\s*)?(?:euros?|€)"
    for nombre, unite in re.findall(motif, texte, re.I):
        nombre = nombre.strip()
        if unite:
            valeur = float(nombre.replace(" ", "").replace(",", "."))
            facteur = 1_000_000 if unite.lower().startswith("million") else 1_000_000_000
            montants.append(int(round(valeur * facteur)))
        else:
            montants.append(int(nombre.split(",")[0].replace(" ", "").replace(".", "")))
    return montants


def nettoyer(texte):
    """Remplace les suites d'espaces et de retours à la ligne par un seul espace."""
    return re.sub(r"\s+", " ", texte or "").strip()


# --- La base -------------------------------------------------------------------

def lire_base():
    """Lit donnees/decisions.json. Renvoie une liste vide si le fichier n'existe pas."""
    if not FICHIER_BASE.exists():
        return []
    return json.loads(FICHIER_BASE.read_text(encoding="utf-8"))


COLONNES_CSV = [
    "id", "regulateur", "numero_procedure", "date_decision", "etablissement",
    "publication", "sanction_texte", "montant_euros", "themes_liste",
    "lcbft_indice", "statut", "url_pdf", "url_page",
]


def enregistrer_base(decisions):
    """Écrit la base en JSON (complet) et en CSV (résumé, lisible dans Excel)."""
    DOSSIER_DONNEES.mkdir(exist_ok=True)
    # Les plus récentes d'abord ; les décisions sans date à la fin.
    decisions.sort(key=lambda d: (d.get("date_decision") or "", d["id"]), reverse=True)
    FICHIER_BASE.write_text(
        json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with open(FICHIER_CSV, "w", encoding="utf-8-sig", newline="") as fichier:
        tableau = csv.DictWriter(fichier, fieldnames=COLONNES_CSV, delimiter=";", extrasaction="ignore")
        tableau.writeheader()
        tableau.writerows(decisions)


def enregistrer_texte(regulateur, identifiant_decision, texte):
    """Écrit le texte d'une décision dans donnees/textes/<regulateur>/<id>.txt."""
    dossier = DOSSIER_TEXTES / regulateur.lower()
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / f"{identifiant_decision}.txt"
    chemin.write_text(texte, encoding="utf-8")
    return str(chemin.relative_to(RACINE)).replace("\\", "/")


def enregistrer_suivi(regulateur, bilan):
    """Note le résultat de la dernière collecte.

    Ce petit fichier change à chaque passage : il sert de témoin (« la mise à jour
    a bien tourné lundi ») et crée chaque semaine une activité dans le dépôt, ce
    qui évite que GitHub désactive la tâche programmée après 60 jours sans activité.
    """
    suivi = {}
    if FICHIER_SUIVI.exists():
        suivi = json.loads(FICHIER_SUIVI.read_text(encoding="utf-8"))
    suivi[regulateur] = bilan
    FICHIER_SUIVI.write_text(json.dumps(suivi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
