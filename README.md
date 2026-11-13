# Sanctions Conformité

Base des décisions de sanction des régulateurs financiers, mise à jour chaque semaine.
Projet personnel de Matéo Bonnesoeur (M1 Gestion d'actifs, contrôle des risques et conformité, IAE de Caen).

> **[À écrire par Matéo : deux ou trois phrases de présentation.]**

Régulateurs couverts aujourd'hui : **ACPR** et **AMF** (commissions des sanctions).
Prévus : CSSF (Luxembourg), FINMA (Suisse).

## Ce que contient le dépôt

| Emplacement | Contenu |
|---|---|
| `donnees/decisions.json` | La base : une entrée par décision (identité, sanction, liens officiels, statut « à lire » ou « lue »). |
| `donnees/decisions.csv` | Le même contenu en tableau, à ouvrir dans Excel. |
| `donnees/textes/acpr/` | Le texte de chaque décision de l'ACPR, extrait du PDF officiel, avec un repère à chaque page. (Pas de texte pour l'AMF : voir plus bas.) |
| `donnees/derniere_collecte.json` | Le bilan de la dernière mise à jour (date, nouvelles décisions, erreurs). |
| `donnees/fiches/acpr/` | Les fiches d'analyse (une par décision), au format structuré. C'est la source. |
| `fiches/acpr/` | Les mêmes fiches en version lisible, fabriquées automatiquement. À lire à côté du PDF officiel. |
| `donnees/glossaire.json` | Le glossaire commun : les termes techniques expliqués en une phrase. |
| `analyse/fiches.py` | Le programme qui vérifie les fiches et fabrique leur version lisible. |
| `analyse/etude.py` | Le programme de l'étude comparative : il compte, à partir des fiches, ce qui est sanctionné et avec quelles sanctions, et vérifie la liste des points de contrôle. |
| `donnees/etude/` | Les résultats de l'étude : `chiffres.json` (comptages, refaits par le programme), `points_de_controle.json` (la liste, c'est la source) et sa copie `points_de_controle.csv` pour Excel. |
| `collecte/` | Le programme de collecte, en Python. |
| `.github/workflows/collecte.yml` | La consigne donnée à GitHub : lancer la collecte chaque lundi. |
| `site/` | Le site public : `construire.py` fabrique les pages, `statique/` contient le style, les scripts et les polices, `pages/` les textes fixes (Méthode, Analyse), `textes/` les textes écrits par Matéo. |
| `.github/workflows/site.yml` | La consigne donnée à GitHub : refaire et publier le site après chaque dépôt et chaque collecte. |
| `PROJET.md` | Le cahier des charges du projet. |
| `JOURNAL.md` | Le journal de bord : ce qui est fait, les choix, la suite. |

Les PDF ne sont pas copiés dans le dépôt : chaque décision garde le lien vers le document officiel.

## Comment marche la collecte

### ACPR

1. Le programme ouvre le « Recueil des sanctions » de l'ACPR, la page officielle qui liste toutes les décisions depuis 2011.
2. Il compare cette liste à la base. Une décision déjà connue n'est pas retéléchargée.
3. Pour chaque décision nouvelle, il ouvre sa page, télécharge le PDF et en extrait le texte.
4. Il lit l'en-tête de la décision (numéro de procédure, sanction, dates) et crée une entrée avec le statut « à lire ».
5. Il enregistre le tout dans le dépôt.

### AMF

1. La page officielle « Décisions de la Commission des sanctions » remplit son tableau à partir d'une liste structurée (JSON) fournie par le site de l'AMF. Le programme lit cette liste : une seule requête donne les 454 décisions publiées depuis 2004 (13 novembre 2026).
2. Chaque ligne donne le numéro de la décision (`SAN-2026-07`), le thème choisi par l'AMF, les personnes visées, le montant total avant recours, l'existence d'un recours et le lien vers le PDF.
3. Pour chaque décision nouvelle, le programme télécharge le PDF et y lit la date de la décision, la date de la séance et le nombre de pages. Il compte aussi les mentions du blanchiment (`lcbft_mentions`) : à partir de 3, `lcbft_indice` vaut vrai. C'est un indice de tri, pas une analyse.
4. Une ligne de la liste dont le contenu change (anonymisation, PDF remplacé) est retéléchargée : le programme garde pour cela une empreinte de chaque ligne (`empreinte_ligne`).

L'identifiant d'une décision AMF est `AMF-` suivi du numéro officiel, par exemple `AMF-SAN-2026-07`.

**Personnes physiques.** L'AMF sanctionne souvent des particuliers et publie leur nom pendant une durée limitée (cinq ans en général). Le programme ne l'enregistre jamais : il garde le nom des sociétés et le nombre de personnes physiques (« Société X et 2 personnes physiques », champ `nom_site`). Pour la même raison, le texte intégral des décisions de l'AMF n'est pas copié dans le dépôt, dont l'historique est public et permanent. Pour rédiger une fiche, on relit le PDF officiel. Seule exception, hors du contrôle du programme : l'adresse officielle de quelques PDF anciens contient un nom.

### Pour les deux

L'identifiant d'une décision est le nom du régulateur suivi du numéro de procédure, par exemple `ACPR-2024-06`. Si le régulateur republie plus tard la décision sous forme anonymisée, elle garde le même identifiant : l'ancienne version est remplacée, sans doublon.

Règles de bonne conduite : une pause de deux secondes entre deux téléchargements, un identifiant qui dit qui collecte et où trouver le projet, et seulement ce qui est nouveau (une requête par semaine quand rien n'a changé).

Si quelque chose ne va pas (site modifié, accès refusé, PDF illisible), le programme s'arrête en erreur avec un message en clair. GitHub affiche alors l'exécution en rouge et envoie un e-mail.

## Vérifier que la mise à jour a tourné

Onglet **Actions** du dépôt : une ligne par exécution, verte si tout va bien, rouge sinon.
Le fichier `donnees/derniere_collecte.json` donne la date et le résultat du dernier passage.

Pour lancer la collecte à la main : onglet **Actions** → « Collecte hebdomadaire » → **Run workflow**.

GitHub désactive les tâches programmées d'un dépôt public après 60 jours sans activité. Ici, chaque collecte modifie `derniere_collecte.json` et l'enregistre : le dépôt a donc une activité chaque semaine.

## Plan B : lancer la collecte depuis son ordinateur

À utiliser si le site d'un régulateur refuse les serveurs de GitHub.

1. Installer Python (python.org) si ce n'est pas fait.
2. Ouvrir un terminal dans le dossier du dépôt.
3. Taper `pip install -r requirements.txt` (une seule fois).
4. Taper `python collecte/lancer.py acpr` (ou `amf`, ou rien pour les deux).
5. Enregistrer et envoyer les changements avec GitHub Desktop (« Commit », puis « Push »).

## Ce qui est lu automatiquement, et ses limites

Le numéro de procédure, les dates, la sanction et le montant sont lus dans l'en-tête du PDF par le programme. Quand une information manque ou paraît douteuse, le programme ne devine pas : il laisse le champ vide et écrit une alerte dans le champ `alertes` de la décision. Ces champs sont vérifiés à la lecture de chaque décision.

Le champ `lcbft_indice` signale seulement que la liste officielle (ACPR) ou le texte de la décision (AMF) mentionne le blanchiment ou le gel des avoirs. C'est un indice de tri, pas une analyse.

## Plus tard : des résumés automatiques (non mis en place)

Aujourd'hui, les nouvelles décisions arrivent avec le statut « à lire » et les fiches d'analyse sont préparées en session avec Claude, puis relues à la main. On pourrait automatiser le premier jet : après la collecte, une étape supplémentaire enverrait le texte de chaque nouvelle décision à un modèle de langage par une API, avec la grille d'analyse de `PROJET.md`, et rangerait la réponse dans un dossier `fiches/` avec le statut « à relire ». Il faudrait une clé d'API, enregistrée dans les « Secrets » du dépôt, et ce service est payant. Le projet devant rester gratuit, ce n'est pas fait.

## Le site

Le site est publié avec GitHub Pages : https://mateo180805.github.io/sanctions-conformite/

`site/construire.py` lit la base et les fiches, et écrit des pages HTML toutes prêtes dans `_site/` (dossier non enregistré dans le dépôt). Il ne lit jamais `donnees/textes/` : certains textes anonymisés laissent passer des noms, le site ne s'appuie donc que sur les fiches. Aucun nom de personne physique n'est affiché. Si l'ACPR anonymise une décision dont la fiche garde le nom, la fiche est retirée du site et la tâche « Site » passe au rouge.

Pour voir le site sur son ordinateur avant de déposer : `python site/construire.py`, puis ouvrir `_site/index.html`.

Les textes de l'accueil et de la page « À propos » se modifient dans `site/textes/introduction.txt` et `site/textes/a-propos.txt`.

## Sources et méthode

Sources : registre officiel et Recueil des sanctions de l'ACPR, <https://acpr.banque-france.fr/fr/reglementation/recueil-des-sanctions> ; décisions de la Commission des sanctions de l'AMF, <https://www.amf-france.org/fr/sanction-transaction/Decisions-de-la-commission-des-sanctions>.
Le programme de collecte a été écrit avec Claude (Fable pour l'ACPR, Opus pour l'AMF), d'Anthropic, puis relu et testé avec Matéo. Seules les décisions officielles font foi.
