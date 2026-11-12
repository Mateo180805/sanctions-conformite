"""
Fiches d'analyse : vérification et mise en forme.

Ce programme ne lit aucune décision et n'écrit aucune analyse. Il fait deux choses :
  1. il VÉRIFIE chaque fiche de donnees/fiches/ (champs présents, catégories de la
     grille, pages citées qui existent bien dans le PDF) ;
  2. il FABRIQUE une version lisible de chaque fiche dans fiches/ (fichiers .md),
     que GitHub affiche comme une page mise en forme. Il y ajoute un lexique : les
     mots techniques de la fiche, expliqués à partir de donnees/glossaire.json.

Les fiches .json sont la source. Les fichiers .md sont refaits à chaque lancement :
il ne faut pas les modifier à la main.

Lancement :  python analyse/fiches.py
"""

import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_FICHES = RACINE / "donnees" / "fiches"
DOSSIER_LISIBLE = RACINE / "fiches"
BASE = RACINE / "donnees" / "decisions.json"
GLOSSAIRE = RACINE / "donnees" / "glossaire.json"
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]

# Les catégories communes de la grille (PROJET.md, point 6). Une fiche ne peut pas en inventer.
CATEGORIES = [
    "classification des risques",
    "relation d'affaires et clients occasionnels",
    "connaissance du client à l'entrée en relation",
    "vigilance constante et mise à jour des dossiers",
    "personnes politiquement exposées et vigilance renforcée",
    "dispositif de surveillance des opérations (outils, scénarios, seuils)",
    "analyse des alertes et examen renforcé",
    "déclarations de soupçon à Tracfin",
    "gel des avoirs et sanctions financières",
    "procédures et contrôle interne",
    "gouvernance, moyens et formation",
    "dispositif de groupe, filiales et correspondance bancaire",
    "autre (à préciser)",
]
ISSUES = ["retenu", "retenu en partie", "écarté"]
STATUTS = ["à lire", "lue"]
PERIMETRES = ["LCB-FT", "LCB-FT et gel des avoirs", "gel des avoirs", "hors LCB-FT"]


def verifier(fiche, decision):
    """Renvoie la liste des problèmes trouvés dans une fiche (liste vide = tout va bien)."""
    pb = []
    nb_pages = decision["nb_pages"]

    def pages_ok(pages, ou):
        for p in pages:
            if not isinstance(p, int) or not 1 <= p <= nb_pages:
                pb.append(f"{ou} : page {p} hors du document ({nb_pages} pages)")

    if fiche["suivi"]["statut"] not in STATUTS:
        pb.append("statut inconnu : " + fiche["suivi"]["statut"])
    if not fiche.get("resume_court"):
        pb.append("paragraphe « En bref » (resume_court) absent")
    if fiche["perimetre"] not in PERIMETRES:
        pb.append("périmètre inconnu : " + fiche["perimetre"])

    # Une fiche « hors LCB-FT » est courte : pas de griefs détaillés à vérifier.
    for g in fiche.get("griefs", []):
        ou = f"grief {g['numero']}"
        if g["issue"] not in ISSUES:
            pb.append(f"{ou} : issue inconnue « {g['issue']} »")
        for c in [g["categorie"]] + g["categories_secondaires"]:
            if c not in CATEGORIES:
                pb.append(f"{ou} : catégorie hors grille « {c} »")
        if g["categorie"] == "autre (à préciser)" and not g["categorie_precision"]:
            pb.append(f"{ou} : catégorie « autre » sans précision")
        if not g["pages"]:
            pb.append(f"{ou} : aucune page citée")
        pages_ok(g["pages"], ou)

    for bloc in ("identite", "controle", "sanction"):
        if bloc in fiche:
            pages_ok(fiche[bloc].get("pages", []), bloc)
    return pb


def date_en_clair(iso):
    """« 2025-06-19 » -> « 19 juin 2025 »."""
    a, m, j = iso.split("-")
    return f"{'1er' if j == '01' else int(j)} {MOIS[int(m) - 1]} {a}"


def lexique(texte, glossaire):
    """Choisit, dans le glossaire commun, les mots techniques présents dans cette fiche.

    Un sigle écrit en majuscules (DS, PPE, CMF) est cherché tel quel, comme un mot entier ;
    les autres termes sont cherchés sans tenir compte des majuscules.
    """
    trouves = []
    bas = texte.lower()
    for e in glossaire:
        for mot in e["cherche"]:
            if mot.isupper():
                present = re.search(r"(?<![A-Za-zÀ-ÿ])" + re.escape(mot) + r"(?![A-Za-zÀ-ÿ])", texte)
            else:
                present = mot.lower() in bas
            if present:
                trouves.append(e)
                break
    return trouves


def p(pages):
    """Met en forme une liste de pages : [3, 4] -> « (p. 3, 4) »."""
    return f" (p. {', '.join(str(x) for x in pages)})" if pages else ""


def montant(n):
    return "aucun" if n is None else f"{n:,}".replace(",", " ") + " euros"


def en_markdown(f, d, glossaire):
    """Fabrique le texte lisible d'une fiche."""
    L = []
    a = L.append
    ident = f["identite"]
    a(f"# {d['regulateur']} – procédure n° {d['numero_procedure']} – {ident['etablissement']}")
    a("")
    a(f"Décision du {date_en_clair(d['date_decision'])} · [PDF officiel]({d['url_pdf']}) · périmètre : {f['perimetre']}")
    a("")
    a(f"> Statut : **{f['suivi']['statut']}** · fiche relue par Matéo : {'oui' if f['redaction']['relue_par_mateo'] else 'non'}  ")
    a(f"> Rédaction : {f['redaction']['redigee_par']}, le {f['redaction']['date']}.  ")
    a("> Chaque information renvoie à une page du PDF officiel. Fichier produit automatiquement : ne pas le modifier.")
    a("")
    if f.get("resume_court"):
        a("## En bref")
        a("")
        a(f["resume_court"])
        a("")
    a("## Identité")
    a("")
    a(f"- Établissement : {ident['etablissement']}")
    a(f"- Type : {ident['type_etablissement']}. {ident.get('precision_type', '')}")
    a(f"- Groupe : {ident['groupe']}")
    a(f"- Pays : {ident['pays']}")
    if ident.get("activite_et_taille"):
        a(f"- Activité et taille : {ident['activite_et_taille']}")
    a(f"- Pages : {', '.join(str(x) for x in ident['pages'])}")
    a("")
    if "controle" in f:
        c = f["controle"]
        a("## Contrôle et procédure")
        a("")
        a(f"- Contrôle sur place : {c['controle_sur_place']}")
        a(f"- Rapport de contrôle : {c['rapport_de_controle']}")
        a(f"- Ouverture de la procédure : {c['ouverture_de_la_procedure']}")
        a(f"- Antécédents : {c['antecedents']}{p(c['pages'])}")
        if "procedure" in f:
            a(f"- Questions de procédure : {f['procedure']['questions_de_procedure']}{p(f['procedure']['pages'])}")
        a("")
    s = f["sanction"]
    a("## Sanction")
    a("")
    a(f"- Nature : {', '.join(s['nature'])}")
    a(f"- Montant : {montant(s['montant_euros'])}")
    a(f"- Publication : {s['publication']} ({s['duree_publication_nominative']})")
    a(f"- Proposition du Collège : {s['proposition_du_college']}")
    a(f"- Pages : {', '.join(str(x) for x in s['pages'])}")
    a("")
    if f.get("griefs"):
        a("## Manquements")
        a("")
        a("| Grief | Sujet | Issue | Catégorie | Pages |")
        a("|---|---|---|---|---|")
        for g in f["griefs"]:
            a(f"| {g['numero']} | {g['titre']} | {g['issue']} | {g['categorie']} | {', '.join(str(x) for x in g['pages'])} |")
        a("")
        for g in f["griefs"]:
            a(f"### Grief {g['numero']} – {g['titre']}")
            a("")
            a(g["resume"])
            a("")
            a(f"- Issue : **{g['issue']}**. {g['precision_issue']}")
            a(f"- Textes visés : {' ; '.join(g['textes'])}")
            cat = g["categorie"] + (f" – {g['categorie_precision']}" if g["categorie_precision"] else "")
            a(f"- Catégorie : {cat}")
            if g["categories_secondaires"]:
                a(f"- Catégories secondaires : {' ; '.join(g['categories_secondaires'])}")
            a("- Chiffres clés :")
            for c in g["chiffres_cles"]:
                a(f"  - {c}")
            a(f"- Pages : {', '.join(str(x) for x in g['pages'])}")
            a("")
    if "contexte" in f:
        c = f["contexte"]
        a("## Contexte (ce que dit la décision)")
        a("")
        for titre, cle in (("Éléments aggravants ou à charge", "elements_aggravants"),
                           ("Éléments atténuants", "elements_attenuants"),
                           ("Mesures correctrices", "mesures_correctrices")):
            a(f"**{titre}**")
            a("")
            for e in c[cle] or [{"texte": "non précisé", "pages": []}]:
                a(f"- {e['texte']}{p(e['pages'])}")
            a("")
        a(f"**Situation financière** : {c['situation_financiere']['texte']}{p(c['situation_financiere']['pages'])}")
        a("")
        a(f"**Cause profonde** : {c['cause_profonde']['texte']}{p(c['cause_profonde']['pages'])}")
        a("")
    if "deduit_par_claude" in f:
        a("## Ce qui aurait dû être fait (déduit, pas dans la décision)")
        a("")
        a(f"*{f['deduit_par_claude']['avertissement']}*")
        a("")
        for x in f["deduit_par_claude"]["points_de_controle"]:
            a(f"- {x}")
        a("")
    m = f["pour_moi"]
    a("## Pour moi")
    a("")
    if m.get("mots_cles"):
        a(f"- Mots-clés : {', '.join(m['mots_cles'])}")
    a("- Pages à lire en priorité :")
    for x in m["pages_prioritaires"]:
        a(f"  - p. {', '.join(str(y) for y in x['pages'])} : {x['pourquoi']}")
    a(f"- Niveau de confiance de Claude : {m['confiance']}")
    a("- Points à vérifier :")
    for x in m["a_verifier"] or ["aucun"]:
        a(f"  - {x}")
    a(f"- Mes notes : {f['suivi']['mes_notes'] or '(vide)'}")
    a("")
    # Le lexique : seulement les mots techniques réellement utilisés dans cette fiche.
    mots = lexique(json.dumps(f, ensure_ascii=False), glossaire)
    if mots:
        a("## Lexique")
        a("")
        for g in mots:
            a(f"- **{g['terme']}** : {g['definition']}")
        a("")
    return "\n".join(L)


def principal():
    decisions = {d["id"]: d for d in json.loads(BASE.read_text(encoding="utf-8"))}
    glossaire = json.loads(GLOSSAIRE.read_text(encoding="utf-8"))
    erreurs = 0
    nb = 0
    for chemin in sorted(DOSSIER_FICHES.glob("*/*.json")):
        fiche = json.loads(chemin.read_text(encoding="utf-8"))
        ident = fiche["id"]
        if ident not in decisions:
            print(f"ERREUR {chemin.name} : identifiant absent de la base")
            erreurs += 1
            continue
        problemes = verifier(fiche, decisions[ident])
        for x in problemes:
            print(f"ERREUR {ident} : {x}")
        erreurs += len(problemes)
        sortie = DOSSIER_LISIBLE / chemin.parent.name / (ident + ".md")
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(en_markdown(fiche, decisions[ident], glossaire), encoding="utf-8")
        nb += 1
    print(f"{nb} fiche(s) mise(s) en forme, {erreurs} problème(s).")
    # Aucune erreur silencieuse : s'il y a un problème, le programme s'arrête en erreur.
    sys.exit(1 if erreurs else 0)


if __name__ == "__main__":
    principal()
