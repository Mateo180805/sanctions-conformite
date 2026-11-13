"""
Vérifie qu'une fiche n'invente aucun chiffre.

Pour chaque grief et chaque bloc de la fiche, cherche chaque nombre dans les pages
citées du texte officiel. Un nombre doit y apparaître entier (pas collé à d'autres
chiffres). Signale ce qui manque, en précisant s'il se trouve ailleurs dans le texte.

Les signalements à ignorer après vérification à l'œil : un montant écrit en lettres
ou en « K€ » dans la décision, un numéro de procédure (« 2017-03 »), deux nombres
voisins que le programme a collés (« 2015 131 »). Tout le reste est à corriger :
c'est en général un arrondi ou une addition faits par le rédacteur.

Usage : python analyse/verifier_nombres.py ACPR-2017-05 ACPR-2017-06
"""
import json, re, sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
def pages(txt):
    return {int(m.group(1)): m.group(2) for m in
            re.finditer(r"===== Page (\d+) =====\n(.*?)(?====== Page|\Z)", txt, re.S)}
def norm(s):
    s = s.replace(" ", " ").replace(" ", " ")
    s = re.sub(r"(?<=\d)\s+(?=\d{3}\b)", "", s)    # 1 500 000 (même coupé par un retour à la ligne) -> 1500000
    return s.replace(",", ".")
def nombres(s):
    for m in re.finditer(r"\d[\d   ]*(?:,\d+)?", s):
        n = m.group(0).strip()
        if len(re.sub(r"\D", "", n)) >= 2 or "," in n:
            yield n
def present(n, zone):
    k = re.escape(norm(n))
    return re.search(r"(?<![\d.,])" + k + r"(?![\d]|[.,]\d)", zone) is not None
for ident in sys.argv[1:]:
    F = json.loads((RACINE / "donnees" / "fiches" / "acpr" / f"{ident}.json").read_text(encoding="utf-8"))
    P = pages((RACINE / "donnees" / "textes" / "acpr" / f"{ident}.txt").read_text(encoding="utf-8"))
    tout = norm(" ".join(P.values()))
    def chk(txt, pg, ou):
        zone = norm(" ".join(P.get(p, "") for p in pg))
        for n in nombres(txt):
            if not present(n, zone):
                print(f"{ident} {ou}: « {n} » absent des pages {pg}" + (" (ailleurs)" if present(n, tout) else " (ABSENT DU TEXTE)"))
    for g in F["griefs"]:
        chk(" ".join(g["chiffres_cles"]) + " " + g["resume"] + " " + g["precision_issue"] + " " + g["titre"], g["pages"], "grief " + g["numero"])
    for b in ("identite", "controle", "sanction", "procedure"):
        chk(" ".join(str(v) for k, v in F[b].items() if k not in ("pages", "montant_euros")), F[b]["pages"], b)
    for k in ("elements_aggravants", "elements_attenuants", "mesures_correctrices"):
        for e in F["contexte"][k]:
            chk(e["texte"], e["pages"], k)
    for k in ("situation_financiere", "cause_profonde"):
        chk(F["contexte"][k]["texte"], F["contexte"][k]["pages"], k)
    chk(F["resume_court"], list(P), "resume_court")
