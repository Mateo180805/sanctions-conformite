"""
Point d'entrée de la collecte.

Utilisation :
    python collecte/lancer.py acpr            collecte normale (seulement le nouveau)
    python collecte/lancer.py acpr --max 3    au plus 3 décisions (pour un essai)

Ce que fait le programme, dans l'ordre :
  1. il lit la liste officielle du régulateur ;
  2. il la compare à la base : une décision déjà connue n'est pas retéléchargée ;
  3. pour chaque décision nouvelle (ou dont le titre a changé, par exemple après
     une anonymisation), il télécharge le PDF, en extrait le texte et crée la
     fiche de base avec le statut « à lire » ;
  4. il enregistre la base et un bilan de la collecte ;
  5. s'il y a eu un problème, il se termine en erreur pour que GitHub me prévienne.
"""

import sys
from datetime import date

import acpr
import amf
from commun import (
    ErreurCollecte, date_iso, enregistrer_base, enregistrer_suivi, enregistrer_texte, lire_base,
)

# Pour ajouter un régulateur : écrire son module (amf.py...) et l'inscrire ici.
REGULATEURS = {"acpr": acpr, "amf": amf}

# Champs que je remplis moi-même : la collecte ne doit jamais les écraser.
CHAMPS_PERSONNELS = ("statut", "mes_notes")


def attribuer_id(fiche, base):
    """Identifiant unique : régulateur + numéro de procédure (ex. ACPR-2024-06).

    Une décision republiée sous forme anonymisée garde le même numéro et la même
    date : elle retrouve donc le même identifiant et remplace l'ancienne version.
    Cas rare : deux décisions différentes pour une même procédure (décision
    annulée puis rejugée). La seconde reçoit alors sa date en plus.
    """
    regulateur = fiche["regulateur"]
    if fiche["numero_procedure"]:
        identifiant = f"{regulateur}-{fiche['numero_procedure']}"
    else:
        identifiant = f"{regulateur}-sans-numero-{fiche['date_decision'] or 'sans-date'}"
    existante = next((d for d in base if d["id"] == identifiant), None)
    if existante and existante.get("date_decision") != fiche["date_decision"]:
        identifiant = f"{identifiant}-du-{fiche['date_decision'] or 'sans-date'}"
    return identifiant


def titre_coherent(titre, fiche):
    """Le titre de la liste correspond-il à la décision téléchargée ?

    On compare la date écrite dans le titre à celles du PDF (décision ou
    audience). Un titre sans date est accepté. Sert à repérer les lignes du
    recueil dont le lien mène par erreur à une autre décision.
    """
    date_titre = date_iso(titre)
    return date_titre is None or date_titre in (fiche["date_decision"], fiche["date_audience"])


def collecter_regulateur(module, maximum=None):
    aujourd_hui = date.today().isoformat()
    base = lire_base()
    connues = {url: d for d in base if d["regulateur"] == module.NOM for url in d.get("urls_page", [])}
    # L'AMF donne un numéro stable à chaque décision (« SAN-2026-07 ») : on s'en sert
    # aussi, car l'adresse de la page peut changer quand la décision est anonymisée.
    par_numero = {d["numero_procedure"]: d for d in base if d["regulateur"] == module.NOM}

    entrees = module.lister()
    print(f"{module.NOM} : {len(entrees)} lignes de décision dans la liste officielle, "
          f"{sum(1 for d in base if d['regulateur'] == module.NOM)} décisions dans la base.")
    if len(entrees) < module.MINIMUM_ATTENDU:
        raise ErreurCollecte(
            f"{module.NOM} : seulement {len(entrees)} décisions trouvées dans la liste "
            f"(au moins {module.MINIMUM_ATTENDU} attendues). La page a sans doute changé : "
            "il faut adapter le programme."
        )

    # Que faut-il télécharger ? Ce qui est inconnu, ou connu mais dont le titre a
    # changé (par exemple après une anonymisation).
    a_traiter = []
    for entree in entrees:
        deja = next((connues[u] for u in entree["urls_page"] if u in connues), None)
        if deja is None and entree.get("numero"):
            deja = par_numero.get(entree["numero"])
        if deja is None:
            a_traiter.append(entree)
        elif "empreinte_ligne" in entree:
            # AMF : la ligne de la liste a-t-elle changé (personnes, sanction, PDF) ?
            if deja.get("empreinte_ligne") != entree["empreinte_ligne"]:
                a_traiter.append(entree)
            elif deja.get("suites") != entree["suites"]:
                deja["suites"] = entree["suites"]
        elif entree["titre_liste"] in deja.get("lignes_recueil_incoherentes", []):
            pass  # anomalie du site déjà notée : inutile de retélécharger chaque semaine
        elif deja["titre_liste"] != entree["titre_liste"]:
            a_traiter.append(entree)
        elif deja.get("suites") != entree["suites"]:
            deja["suites"] = entree["suites"]  # nouveau recours signalé : simple mise à jour

    if maximum is not None:
        a_traiter = a_traiter[:maximum]

    nouvelles, modifiees, anomalies, erreurs = [], [], [], []
    for rang, entree in enumerate(a_traiter, 1):
        # Enregistrement intermédiaire toutes les 20 décisions : si l'exécution est
        # coupée (temps maximum de GitHub dépassé, panne), le travail déjà fait est gardé.
        if rang % 20 == 0:
            enregistrer_base(base)
        try:
            fiche, texte = module.collecter(entree)
        except ErreurCollecte as erreur:
            # On note le problème et on continue avec les autres décisions.
            erreurs.append(f"{entree['titre_liste']} : {erreur}")
            print(f"  ERREUR  {entree['titre_liste'][:80]} : {erreur}")
            continue

        fiche["id"] = attribuer_id(fiche, base)
        fiche["date_collecte"] = aujourd_hui
        ancienne = next((d for d in base if d["id"] == fiche["id"]), None)
        coherent = titre_coherent(fiche["titre_liste"], fiche)

        if ancienne and not coherent:
            # Le lien de cette ligne mène à une décision déjà dans la base, mais le
            # titre annonce une autre date : erreur de lien sur le site officiel.
            # On garde la fiche existante et on note l'anomalie.
            ancienne["lignes_recueil_incoherentes"].append(fiche["titre_liste"])
            ancienne["alertes"].append(
                f"Une autre ligne du recueil renvoie vers cette décision avec une autre date "
                f"(« {fiche['titre_liste']} ») : lien officiel probablement erroné."
            )
            anomalies.append(fiche["titre_liste"])
            print(f"  ANOMALIE  ligne du recueil mal reliée : {fiche['titre_liste'][:80]}")
            continue

        # Le texte n'est enregistré que si le module en fournit un (pas pour l'AMF).
        fiche["fichier_texte"] = enregistrer_texte(module.NOM, fiche["id"], texte) if texte else None
        if not coherent:
            fiche["lignes_recueil_incoherentes"].append(fiche["titre_liste"])
            fiche["alertes"].append("La date du titre de la liste ne correspond pas à celle du PDF : à vérifier.")

        if ancienne:
            # Même décision, nouvelle version (souvent : anonymisation).
            # On garde mon travail (statut, notes) et on signale qu'il faut revérifier.
            for champ in CHAMPS_PERSONNELS:
                fiche[champ] = ancienne.get(champ, fiche[champ])
            fiche["lignes_recueil_incoherentes"] += ancienne.get("lignes_recueil_incoherentes", [])
            fiche["date_collecte"] = ancienne.get("date_collecte", aujourd_hui)
            if ancienne.get("empreinte_pdf") != fiche["empreinte_pdf"]:
                fiche["modifiee_le"] = aujourd_hui
                fiche["alertes"].append(
                    f"PDF remplacé par le régulateur (détecté le {aujourd_hui}) : fiche à revérifier."
                )
            if ancienne.get("publication") == "nominative" and fiche["publication"] == "anonymisée":
                fiche["alertes"].append(f"Décision anonymisée par le régulateur (détecté le {aujourd_hui}).")
            base[base.index(ancienne)] = fiche
            modifiees.append(fiche["id"])
            print(f"  MODIFIÉE  {fiche['id']}")
        else:
            base.append(fiche)
            nouvelles.append(fiche["id"])
            print(f"  NOUVELLE  {fiche['id']}  {fiche['date_decision']}  {fiche['sanction_texte']}")

    enregistrer_base(base)
    enregistrer_suivi(module.NOM, {
        "date": aujourd_hui,
        "lignes_dans_la_liste_officielle": len(entrees),
        "decisions_dans_la_base": sum(1 for d in base if d["regulateur"] == module.NOM),
        "nouvelles": nouvelles,
        "modifiees": modifiees,
        "anomalies_du_site": anomalies,
        "erreurs": erreurs,
    })
    print(f"{module.NOM} : {len(nouvelles)} nouvelle(s), {len(modifiees)} modifiée(s), "
          f"{len(anomalies)} anomalie(s) du site, {len(erreurs)} erreur(s).")
    return erreurs


def main():
    arguments = sys.argv[1:]
    maximum = None
    if "--max" in arguments:
        position = arguments.index("--max")
        maximum = int(arguments[position + 1])
        del arguments[position:position + 2]
    noms = arguments or list(REGULATEURS)

    erreurs = []
    for nom in noms:
        if nom not in REGULATEURS:
            sys.exit(f"Régulateur inconnu : {nom}. Choix possibles : {', '.join(REGULATEURS)}.")
        try:
            erreurs += collecter_regulateur(REGULATEURS[nom], maximum)
        except ErreurCollecte as erreur:
            erreurs.append(str(erreur))

    if erreurs:
        print("\nLA COLLECTE A RENCONTRÉ DES PROBLÈMES :")
        for erreur in erreurs:
            print(" -", erreur)
        sys.exit(1)  # code d'erreur : GitHub marque l'exécution en rouge et envoie un e-mail
    print("Collecte terminée sans erreur.")


if __name__ == "__main__":
    main()
