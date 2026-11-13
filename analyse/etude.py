"""
Étude comparative : les comptages et la liste des points de contrôle.

Ce programme ne lit aucune décision et n'écrit aucune analyse. Il fait trois choses :
  1. il COMPTE, à partir des fiches de donnees/fiches/, ce qui est sanctionné, chez qui
     et avec quelles sanctions, et enregistre le résultat dans donnees/etude/chiffres.json ;
  2. il VÉRIFIE la liste des points de contrôle (donnees/etude/points_de_controle.json) :
     chaque point doit citer des griefs qui existent vraiment, qui portent sur la LCB-FT
     ou le gel des avoirs, et que la Commission a retenus en tout ou en partie ;
  3. il FABRIQUE une copie de cette liste en tableau (points_de_controle.csv), qui
     s'ouvre dans Excel.

Les règles de comptage (JOURNAL.md) :
  - on compte sur la catégorie PRINCIPALE de chaque grief ;
  - les griefs « hors LCB-FT » d'une décision LCB-FT ne sont pas comptés ;
  - l'unité principale est la DÉCISION : « dans combien de décisions ce type de
    manquement a-t-il été retenu ? ». Le nombre de griefs est donné à côté ;
  - un grief écarté est compté à part. Il ne veut pas dire que la pratique est validée.

Le site (site/construire.py) appelle les mêmes fonctions : les chiffres et les graphiques
de la page Analyse suivent donc toujours les fiches.

Lancement :  python analyse/etude.py
"""

import csv
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fiches import CATEGORIES  # la liste des 13 catégories de la grille

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_FICHES = RACINE / "donnees" / "fiches"
DOSSIER_ETUDE = RACINE / "donnees" / "etude"
BASE = RACINE / "donnees" / "decisions.json"
POINTS = DOSSIER_ETUDE / "points_de_controle.json"

# Les mêmes regroupements que le filtre « type d'établissement » du site.
TYPES = {
    "banque": "Banque",
    "établissement de crédit": "Banque",
    "établissement de crédit spécialisé": "Banque",
    "établissement de paiement": "Paiement et monnaie électronique",
    "établissement de monnaie électronique": "Paiement et monnaie électronique",
    "prestataire de services de paiement (office des postes)": "Paiement et monnaie électronique",
    "assureur": "Assurance",
    "entreprise d'assurance": "Assurance",
    "changeur manuel": "Change manuel",
    "intermédiaire en financement participatif": "Financement participatif",
}


# --------------------------------------------------------------------------
# Lecture
# --------------------------------------------------------------------------

# Période couverte par l'étude, telle que l'annonce son texte (site/pages/analyse.html) :
# les décisions rendues à partir de janvier 2019. Les fiches plus anciennes sont publiées
# sur le site mais n'entrent dans l'étude que si l'on change cette date et le texte.
DEBUT_ETUDE = "2019-01-01"


def charger():
    """Renvoie les fiches LCB-FT de la période étudiée (id -> fiche) et la base des décisions."""
    decisions = {d["id"]: d for d in json.loads(BASE.read_text(encoding="utf-8"))}
    fiches = {}
    for chemin in sorted(DOSSIER_FICHES.glob("*/*.json")):
        f = json.loads(chemin.read_text(encoding="utf-8"))
        date = (decisions.get(f["id"]) or {}).get("date_decision") or ""
        if f["perimetre"] != "hors LCB-FT" and date >= DEBUT_ETUDE:
            fiches[f["id"]] = f
    return fiches, decisions


def est_hors_lcbft(grief):
    """Un grief hors LCB-FT est signalé dans la précision de sa catégorie."""
    return "hors LCB-FT" in grief.get("categorie_precision", "")


def griefs_comptes(fiche):
    """Les griefs d'une fiche qui entrent dans l'étude."""
    return [g for g in fiche["griefs"] if not est_hors_lcbft(g)]


def montant_propose(texte):
    """Lit le montant demandé par le Collège dans une phrase comme « blâme et 1,5 million
    d'euros ». Renvoie None si la phrase ne donne pas de montant."""
    t = texte.replace(" ", " ").replace("\xa0", " ")
    m = re.search(r"(\d+(?:,\d+)?|un)\s+millions?\s+d'euros", t)
    if m:
        nombre = 1.0 if m.group(1) == "un" else float(m.group(1).replace(",", "."))
        return int(round(nombre * 1_000_000))
    m = re.search(r"(\d{1,3}(?: \d{3})+|\d+)\s+euros", t)
    return int(m.group(1).replace(" ", "")) if m else None


# --------------------------------------------------------------------------
# Comptages
# --------------------------------------------------------------------------

def calculer(fiches, decisions):
    """Fait tous les comptages de l'étude. Renvoie un dictionnaire prêt à enregistrer."""
    ids = sorted(fiches)

    # 1. Par catégorie de manquement
    categories = []
    for cat in CATEGORIES:
        issues = {"retenu": 0, "retenu en partie": 0, "écarté": 0}
        sanctionnees, citees = [], []
        for i in ids:
            de_la_cat = [g for g in griefs_comptes(fiches[i]) if g["categorie"] == cat]
            for g in de_la_cat:
                issues[g["issue"]] += 1
            if de_la_cat:
                citees.append(i)
            if any(g["issue"] != "écarté" for g in de_la_cat):
                sanctionnees.append(i)
        categories.append({
            "categorie": cat,
            "decisions_sanctionnees": sanctionnees,   # au moins un grief retenu, en tout ou en partie
            "decisions_citees": citees,               # au moins un grief, même écarté
            "griefs": sum(issues.values()),
            "retenus": issues["retenu"], "en_partie": issues["retenu en partie"],
            "ecartes": issues["écarté"],
        })
    categories.sort(key=lambda c: (-len(c["decisions_sanctionnees"]), -c["griefs"]))

    # 2. Une ligne par décision
    lignes = []
    for i in ids:
        f, d = fiches[i], decisions[i]
        gr = griefs_comptes(f)
        propose = montant_propose(f["sanction"]["proposition_du_college"])
        prononce = f["sanction"]["montant_euros"] or 0
        if propose is None or "sanction pécuniaire" not in f["sanction"]["nature"]:
            ecart = "sans objet"
        elif prononce < propose:
            ecart = "inférieure"
        elif prononce == propose:
            ecart = "égale"
        else:
            ecart = "supérieure"
        lignes.append({
            "id": i, "procedure": d["numero_procedure"], "date": d["date_decision"],
            "annee": d["date_decision"][:4],
            "type": f["identite"]["type_etablissement"],
            "groupe": TYPES.get(f["identite"]["type_etablissement"], "Autre"),
            "perimetre": f["perimetre"],
            "nominative": not f["identite"]["etablissement"].startswith("anonymisé"),
            "nature": f["sanction"]["nature"], "montant": prononce,
            "montant_propose": propose, "ecart_avec_la_proposition": ecart,
            "griefs": len(gr),
            "retenus": sum(g["issue"] == "retenu" for g in gr),
            "en_partie": sum(g["issue"] == "retenu en partie" for g in gr),
            "ecartes": sum(g["issue"] == "écarté" for g in gr),
            "griefs_hors_lcbft": len(f["griefs"]) - len(gr),
        })
    lignes.sort(key=lambda l: l["date"])

    # 3. Par type d'établissement et par année
    def regrouper(cle):
        groupes = {}
        for l in lignes:
            g = groupes.setdefault(l[cle], {"decisions": 0, "montant_total": 0, "griefs": 0})
            g["decisions"] += 1
            g["montant_total"] += l["montant"]
            g["griefs"] += l["griefs"]
        return groupes

    par_type = dict(sorted(regrouper("groupe").items(), key=lambda kv: -kv[1]["decisions"]))
    par_annee = dict(sorted(regrouper("annee").items()))

    # 4. Les sanctions
    amendes = sorted(l["montant"] for l in lignes if l["montant"])
    ecarts = {}
    for l in lignes:
        ecarts[l["ecart_avec_la_proposition"]] = ecarts.get(l["ecart_avec_la_proposition"], 0) + 1

    tous = [g for i in ids for g in griefs_comptes(fiches[i])]
    return {
        "avertissement": "Fichier fabriqué par analyse/etude.py à partir des fiches. Ne pas le modifier à la main.",
        "nb_decisions": len(ids),
        "periode": {"premiere_decision": lignes[0]["date"], "derniere_decision": lignes[-1]["date"]},
        "nb_griefs": len(tous),
        "nb_griefs_hors_lcbft_exclus": sum(l["griefs_hors_lcbft"] for l in lignes),
        "issues": {
            "retenus": sum(g["issue"] == "retenu" for g in tous),
            "en_partie": sum(g["issue"] == "retenu en partie" for g in tous),
            "ecartes": sum(g["issue"] == "écarté" for g in tous),
        },
        "nb_nominatives": sum(l["nominative"] for l in lignes),
        "perimetres": {p: sum(l["perimetre"] == p for l in lignes)
                       for p in sorted({l["perimetre"] for l in lignes})},
        "categories": categories,
        "par_type": par_type,
        "par_annee": par_annee,
        "sanctions": {
            "avec_amende": len(amendes),
            "sans_amende": [l["id"] for l in lignes if not l["montant"]],
            "total": sum(amendes),
            "mediane": int(statistics.median(amendes)),
            "minimum": amendes[0], "maximum": amendes[-1],
            "au_plus_un_million": sum(a <= 1_000_000 for a in amendes),
            "ecart_avec_la_proposition_du_college": ecarts,
        },
        "decisions": lignes,
    }


# --------------------------------------------------------------------------
# La liste des points de contrôle
# --------------------------------------------------------------------------

def lire_points(fiches):
    """Lit et vérifie la liste des points de contrôle. Renvoie (liste, problèmes)."""
    donnees = json.loads(POINTS.read_text(encoding="utf-8"))
    problemes, deja = [], set()
    for p in donnees["points"]:
        ou = f"point {p.get('id', '?')}"
        if p["id"] in deja:
            problemes.append(f"{ou} : identifiant en double")
        deja.add(p["id"])
        if p["categorie"] not in CATEGORIES:
            problemes.append(f"{ou} : catégorie hors grille « {p['categorie']} »")
        for champ in ("question", "preuve"):
            if not p.get(champ, "").strip():
                problemes.append(f"{ou} : champ « {champ} » vide")
        if not p["sources"]:
            problemes.append(f"{ou} : aucune décision citée")
        for procedure, numeros in p["sources"].items():
            fiche = fiches.get("ACPR-" + procedure)
            if not fiche:
                problemes.append(f"{ou} : pas de fiche pour la décision {procedure}")
                continue
            griefs = {g["numero"]: g for g in fiche["griefs"]}
            for n in numeros:
                g = griefs.get(n)
                if not g:
                    problemes.append(f"{ou} : la décision {procedure} n'a pas de grief {n}")
                elif g["issue"] == "écarté":
                    problemes.append(f"{ou} : le grief {n} de {procedure} a été écarté")
                elif est_hors_lcbft(g):
                    problemes.append(f"{ou} : le grief {n} de {procedure} est hors LCB-FT")
    return donnees, problemes


def ecrire_csv(donnees, chemin):
    """Le tableau des points de contrôle, lisible dans Excel (séparateur point-virgule)."""
    with open(chemin, "w", encoding="utf-8-sig", newline="") as fichier:
        tableau = csv.writer(fichier, delimiter=";")
        tableau.writerow(["Numéro", "Catégorie", "Point de contrôle", "Ce qu'on peut demander comme preuve",
                          "Nombre de décisions", "Décisions ACPR (griefs)"])
        for p in donnees["points"]:
            sources = " ; ".join(f"{proc} (grief{'s' if len(n) > 1 else ''} {', '.join(n)})"
                                 for proc, n in p["sources"].items())
            tableau.writerow([p["id"], p["categorie"], p["question"], p["preuve"],
                              len(p["sources"]), sources])


# --------------------------------------------------------------------------

def principal():
    fiches, decisions = charger()
    DOSSIER_ETUDE.mkdir(parents=True, exist_ok=True)

    chiffres = calculer(fiches, decisions)
    (DOSSIER_ETUDE / "chiffres.json").write_text(
        json.dumps(chiffres, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{chiffres['nb_decisions']} décisions, {chiffres['nb_griefs']} griefs comptés "
          f"({chiffres['nb_griefs_hors_lcbft_exclus']} griefs hors LCB-FT exclus).")
    for c in chiffres["categories"]:
        print(f"  {len(c['decisions_sanctionnees']):2} décisions | {c['griefs']:3} griefs "
              f"({c['retenus']} retenus, {c['en_partie']} en partie, {c['ecartes']} écartés) | {c['categorie']}")

    if POINTS.exists():
        donnees, problemes = lire_points(fiches)
        if problemes:
            print("\nLa liste des points de contrôle a des problèmes :")
            for p in problemes:
                print("  - " + p)
            sys.exit(1)   # arrêt en erreur : pas d'erreur silencieuse
        ecrire_csv(donnees, DOSSIER_ETUDE / "points_de_controle.csv")
        print(f"{len(donnees['points'])} points de contrôle vérifiés, tableau enregistré.")


if __name__ == "__main__":
    principal()
