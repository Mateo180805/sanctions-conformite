"""
Lecture compacte d'une décision, pour rédiger une fiche en lisant moins de texte.

Retire les en-têtes et pieds de page, la liste des personnes présentes, et coupe les
considérants qui ne font que citer des textes de loi (ceux qui ne contiennent pas le
mot « grief »). Les faits et les raisonnements ne sont jamais coupés. Les repères de
page restent, sous la forme ⟦p.N⟧.

Usage : python analyse/lire_decision.py ACPR-2017-05 > /tmp/decision.txt
La vérification des chiffres (analyse/verifier_nombres.py) se fait, elle, sur le texte complet.
"""
import re, sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
ident = sys.argv[1]
brut = (RACINE / "donnees" / "textes" / "acpr" / f"{ident}.txt").read_text(encoding="utf-8")
lignes = []
for l in brut.splitlines():
    s = l.strip()
    if re.fullmatch(r"Autorité de contrôle prudentiel et de résolution \d+", s): continue
    if re.match(r"Décision de la Commission des sanctions\s*[–-]\s*[Pp]rocédure", s): continue
    if re.match(r"^- (M\.|Mme|MM\.|Mmes)", s): continue
    if re.match(r"^(Vu la Convention|Vu le règlement intérieur|Vu la directive)", s): continue
    m = re.fullmatch(r"===== Page (\d+) =====", s)
    if m:
        lignes.append(f"⟦p.{m.group(1)}⟧"); continue
    lignes.append(s)
texte = " ".join(x for x in lignes if x)
texte = re.sub(r"\s+", " ", texte)
# découpe en paragraphes numérotés
parts = re.split(r"(?=(?<![\w,])\d{1,3}\.\s+(?:Considérant|Mais|Cependant|En |Il |La |Le |Les |Aux |Si |S'|Selon|Toutefois|Par |Ainsi|D'|Dès|Pour))", texte)
coupes = 0
out = []
for p in parts:
    corps = re.sub(r"⟦p\.\d+⟧", "", p)
    loi = re.match(r"\d{1,3}\.\s+Considérant\s+(qu['’]aux termes|que,? selon (le|la|l['’]|les) (\w+ )?(I|II|III|IV|V|VI|\d|premier|deuxième|troisième|article|alinéa)|que l['’]article|qu['’]en (vertu|application) (de|du|des)|que (le|la|les) (I|II|III|IV|V|VI|premier|deuxième|troisième)\b (de l|du |des )?)", corps)
    if loi and "grief" not in corps and len(p) > 400:
        pages = re.findall(r"⟦p\.\d+⟧", p)
        out.append(p[:260] + " […citation coupée…] " + " ".join(pages))
        coupes += 1
    else:
        out.append(p)
res = "\n".join(out)
print(res)
print(f"\n[{len(brut)} caractères bruts -> {len(res)} ; {coupes} considérants de citation coupés]", file=sys.stderr)
