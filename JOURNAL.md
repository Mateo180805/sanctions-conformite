# JOURNAL – Sanctions Conformité

Journal de bord du projet. La session la plus récente est en haut.
À redonner à Claude au début de chaque session, avec PROJET.md.

---

## Session 1 – 12 novembre 2026 – Lancement et collecte ACPR

### État à la fin de la session

- [x] Programme de collecte ACPR écrit et testé sur toutes les décisions du recueil.
- [x] Base initiale : 108 décisions (2011 à juin 2025), toutes au statut « à lire ».
- [x] Workflow GitHub Actions écrit (chaque lundi + lancement manuel).
- [ ] Dépôt GitHub créé et fichiers déposés (à faire par Matéo, étape en cours).
- [ ] Première collecte lancée sur GitHub : elle doit ajouter 3 décisions (voir « Test prévu »).

### Ce qu'on a appris sur le site de l'ACPR

- Une seule page liste tout : le « Recueil des sanctions », classé par année (2011 à 2026) puis par mois. Adresse : https://acpr.banque-france.fr/fr/reglementation/recueil-des-sanctions
- L'adresse anglaise du brief (/en/node/33459) répond « accès refusé » : abandonnée.
- Le chemin est toujours le même : ligne du recueil → page de publication → un lien « Télécharger » vers le PDF.
- Le recueil compte 113 lignes de décision, pour 111 décisions accessibles. Deux lignes ont un lien erroné sur le site officiel :
  - la ligne « n° 2014-05 du 26 février 2015 » (Cards Off) mène au PDF de la décision de renvoi du 22 décembre 2014. La décision finale de février 2015 n'est donc pas dans la base ;
  - la ligne « n° 2013-04 du 11 avril 2014 » mène à la décision du 19 mai 2016 (même procédure, rejugée après annulation par le Conseil d'État). La décision de 2014 n'est donc pas dans la base.
  Ces deux anomalies sont notées dans le champ `lignes_recueil_incoherentes` des fiches concernées.
- Le titre du recueil donne parfois la date de l'audience, pas celle de la décision (exemple : procédure 2024-06, audience le 19 mars 2026, décision rendue le 15 avril 2026). La base retient la date lue dans le PDF.
- Les PDF contiennent tous du texte (aucun scan) : l'extraction fonctionne de 2011 à 2026.
- Le site est protégé par un filtre (Akamai) qui refuse certains identifiants de programme (code 403). L'identifiant du projet, qui donne l'adresse du dépôt GitHub, est accepté. On ne sait pas encore si les serveurs de GitHub sont acceptés : c'est ce que le premier lancement dira.

### Choix faits

- **Identifiant** : `ACPR-` + numéro de procédure (ex. `ACPR-2024-06`). Deux décisions différentes pour une même procédure : la seconde reçoit sa date (`ACPR-2013-02-du-2014-03-19`).
- **Une seule base** `donnees/decisions.json` pour tous les régulateurs, plus une copie CSV pour Excel. Un fichier texte par décision, avec un repère « ===== Page N ===== » pour pouvoir citer les pages.
- **Un module par régulateur** (`collecte/acpr.py`), des outils communs (`collecte/commun.py`), un point d'entrée (`collecte/lancer.py`). Ajouter l'AMF = écrire `amf.py` et l'inscrire dans `lancer.py`.
- **Seulement le nouveau** : une décision est reconnue par l'adresse de sa page. Si son titre change dans le recueil (anonymisation), elle est retéléchargée et remplace l'ancienne ; le statut et les notes sont conservés.
- **Rien n'est deviné** : champ vide + alerte quand l'en-tête ne se lit pas bien. 8 décisions ont une alerte.
- **Anonymisation** (sur les 111 décisions) : 33 anonymisées, 1 « à vérifier » (procédure 2016-08), 77 nominatives. Pour une décision anonymisée, le champ `etablissement` vaut « anonymisé ».
- **Parade aux 60 jours** : GitHub désactive les tâches programmées d'un dépôt public après 60 jours sans activité (règle vérifiée dans la documentation GitHub). Chaque collecte réécrit `donnees/derniere_collecte.json` et l'enregistre, donc une activité par semaine.
- **Dépôt des fichiers avec GitHub Desktop** plutôt que par le site : le site refuse plus de 100 fichiers à la fois et gère mal le dossier caché `.github`.

### Test prévu

Les trois décisions les plus récentes (`ACPR-2024-01`, `ACPR-2024-06`, `ACPR-2025-01`) ont été retirées exprès de la base livrée. La première collecte sur GitHub doit les retrouver et les ajouter : c'est la preuve que toute la chaîne fonctionne (liste, page, PDF, texte, enregistrement).

### Points ouverts

1. **Accès de GitHub au site de l'ACPR** : inconnu avant le premier lancement. En cas de refus (403) : plan B du README.
2. **Adresses officielles qui trahissent un nom** : pour quelques décisions anonymisées, l'adresse de la page ou du PDF sur le site de l'ACPR contient encore un nom. La base ne s'en sert pas pour identifier qui que ce soit, mais ces liens seront visibles sur le site. À décider en session 3 (par exemple : n'afficher que le numéro de procédure et un lien « source officielle »).
3. **Noms de personnes physiques** : certains titres officiels et en-têtes citent des dirigeants. Ils sont dans la base tels que publiés par l'ACPR. Sur le site (session 3), ils ne devront pas être mis en avant.
4. **Montants** : 15 décisions sans montant lu. Pour la plupart, c'est normal (blâme seul, interdiction, mise hors de cause). Pour 5, il faut lire le PDF : 2021-04, 2015-02, 2012-02 (plusieurs personnes sanctionnées), 2011-03, 2010-02 (sanction absente de l'en-tête).
5. **Recours** : les suites (recours, arrêts du Conseil d'État) sont reprises du recueil dans le champ `suites`. Neuf rattachements automatiques d'arrêts du Conseil d'État sont à vérifier (marqués « à vérifier » dans le texte).
6. **Versions des actions GitHub** (`actions/checkout@v5`, `actions/setup-python@v6`) : non vérifiées en ligne pendant la session. Si GitHub signale une version inconnue, il suffira de changer le chiffre.

### Avant la session 2 (pour Matéo)

- Vérifier le lundi suivant que la collecte a tourné (onglet Actions).
- Ouvrir `donnees/decisions.csv` dans Excel et parcourir la liste.
- Lire en entier deux ou trois décisions LCB-FT récentes, pour savoir à quoi ressemble une décision avant qu'on construise les fiches. Suggestions : 2024-06 (établissement de paiement), 2024-02 (banque, avec gel des avoirs), 2022-07 (monnaie électronique).
- Réfléchir à deux questions : la session 2 traite-t-elle les 66 décisions LCB-FT d'un coup ou par lots de 10 ? Les fiches « hors LCB-FT » sont-elles faites en même temps ?

### Prochaine étape

Session 2 : fiches d'analyse. Commencer par un essai de la grille sur 3 décisions, à valider avant de traiter un lot.
