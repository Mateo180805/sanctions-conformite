# JOURNAL – Sanctions Conformité

Journal de bord du projet. La session la plus récente est en haut.
À redonner à Claude au début de chaque session, avec PROJET.md.

---

## Session 2 – 12 novembre 2026 (en cours) – Fiches d'analyse ACPR

### État après le lot 3a

- [x] Format des fiches choisi et validé par Matéo.
- [x] Essai de la grille sur 3 décisions (2024-06, 2024-02, 2022-07), validé.
- [x] Lot 1 : 5 décisions (2024-01, 2023-01, 2022-05, 2022-06, 2022-03). Déposé sur GitHub par Matéo et vérifié (dépôt identique à la copie de travail, collecte du lundi intacte).
- [x] Lot 2 : 5 décisions (2022-04, 2022-02, 2022-01, 2021-05, 2021-01).
- [x] Lot 3a : 3 décisions (2020-11, 2020-09, 2020-08), dans une nouvelle conversation.
- [ ] Lots suivants : voir « Prochaine étape ».

**16 fiches faites sur 66 décisions LCB-FT** : toutes les décisions LCB-FT et gel des avoirs rendues entre octobre 2021 et avril 2026. Aucune n'a encore été relue par Matéo (statut « à lire »).

| Décision | Établissement | Sanction | Griefs (retenus / en partie / écartés) |
|---|---|---|---|
| 2024-06 | MoneyGram International | blâme, 1,3 M€ | 6 / 2 / 0 |
| 2024-01 | Banque Chaabi du Maroc | blâme, 250 000 € | 5 / 0 / 2 |
| 2024-02 | Banque Delubac & Cie | blâme, 600 000 € | 8 / 1 / 0 |
| 2023-01 | BRED | blâme, 2,5 M€ | 0 / 3 / 1 |
| 2022-07 | Treezor | blâme, 1 M€ | 3 / 2 / 1 |
| 2022-05 | SFPMEI | blâme, 100 000 € | 5 / 0 / 1 |
| 2022-06 | Mutuelle de Poitiers Assurances | blâme, 600 000 € | 3 / 0 / 0 |
| 2022-03 | Abeille Vie | blâme, 3,5 M€ | 4 / 6 / 0 |
| 2022-04 | BMW Finance | blâme, 500 000 € | 10 / 0 / 0 |
| 2022-02 | Financière des paiements électroniques (Nickel) | blâme, 1 M€ | 3 / 4 / 1 |
| 2022-01 | Axa Banque | blâme, 1 M€ | 1 / 5 / 0 |
| 2021-05 | Crédit agricole du Languedoc | blâme, 1,5 M€ | 2 / 2 / 0 |
| 2021-01 | W-HA (Orange Money France) | blâme, 700 000 € | 5 / 0 / 0 |
| 2020-11 | Office des postes et télécommunications de Nouvelle-Calédonie | blâme, 150 000 € | 7 / 1 / 0 |
| 2020-09 | MMA IARD (gel des avoirs seulement) | blâme, 4 M€ | 5 / 0 / 0 |
| 2020-08 | anonymisé (« société A », banque luxembourgeoise, monnaie électronique) | blâme, 120 000 € | 4 / 4 / 1 |

### Le format retenu

- **Une fiche source par décision** : `donnees/fiches/acpr/ACPR-2024-06.json`. Format structuré, pour que le site (session 3) et l'étude comparative (session 4) puissent compter sans ressaisie.
- **Une version lisible** : `fiches/acpr/ACPR-2024-06.md`, fabriquée automatiquement. C'est elle qu'on lit, à côté du PDF. Il ne faut pas la modifier à la main.
- **Un programme** : `analyse/fiches.py`. Il n'écrit aucune analyse. Il vérifie chaque fiche (catégories de la grille, pages citées existant dans le PDF, paragraphe « En bref » présent) puis fabrique la version lisible. En cas de problème, il s'arrête en erreur.
- **Un glossaire commun** : `donnees/glossaire.json` (59 termes depuis le lot 3a). Le programme ajoute en bas de chaque fiche un lexique avec les seuls termes qu'elle emploie.
- Pour marquer une fiche comme lue ou y mettre des notes : modifier les deux lignes `"statut"` et `"mes_notes"` au début du fichier .json, puis relancer le programme.

### Choix faits

- **Accessibilité (demande de Matéo)** : chaque fiche commence par un paragraphe « En bref » en langage courant ; les résumés de griefs évitent le jargon ; le lexique explique le vocabulaire sans alourdir le texte. Règle ajoutée à PROJET.md (point 7).
- **Trois issues par grief** : « retenu », « retenu en partie », « écarté ». Beaucoup de griefs ne sont retenus que pour une partie des dossiers.
- **Une 13e catégorie** : « relation d'affaires et clients occasionnels » (griefs MoneyGram et Chaabi).
- **La vigilance complémentaire** (pays à haut risque, PPE) reste rangée dans « personnes politiquement exposées et vigilance renforcée », avec une précision.
- **Une catégorie principale par grief**, plus des catégories secondaires facultatives. Pour l'étude comparative, compter d'abord sur la catégorie principale.
- **Blocs ajoutés à la grille** : contrôle et procédure (dates, antécédents, proposition du Collège), situation financière, mots-clés. PROJET.md (point 6) est à jour.
- **Ce qui est déduit** est isolé dans le bloc « Ce qui aurait dû être fait » et marqué comme tel. Les montants masqués par l'ACPR restent masqués.
- **Aucun nom de personne physique** dans les fiches.
- **Issue d'un grief** : la fiche suit la formule de la décision. Quand la décision dit « fondé » tout en écartant un argument, la fiche indique « retenu » et le précise.
- **Lecture des textes (à partir du lot 2)** : avant lecture, les en-têtes et pieds de page répétés et les longues citations entre guillemets (articles de loi recopiés) sont retirés ; les numéros d'articles et tout le raisonnement restent. Gain : 5 à 15 % de texte.

### Lot 3a (2020-11, 2020-09, 2020-08) – ce qu'il faut savoir

- Nouvelle conversation. L'espace de travail était vide au départ : aucun fichier laissé par un passage interrompu. Le dépôt a été cloné depuis GitHub (état « lot 2 »).
- Contrôle fait après rédaction : `analyse/fiches.py` (16 fiches, 0 problème) ; un contrôle automatique a recherché chaque nombre cité dans les pages indiquées du texte (tous retrouvés) ; les issues ont été comparées à la phrase de conclusion de chaque grief.
- Contrairement à ce qu'indiquait ce journal, 2020-11 et 2020-09 sont nominatives. Les décisions anonymisées commencent à 2020-08 et vont jusqu'à 2017-10.
- **MMA IARD (2020-09)** : publication nominative pour 5 ans à compter du 30 novembre 2021. La décision devrait être anonymisée sur le site de l'ACPR fin novembre 2026. La collecte la retéléchargera ; il faudra alors retirer le nom de la fiche (champs `etablissement`, `groupe`, « En bref », résumés). Même sujet en février 2027 pour 2020-11. À prévoir pour le site : une fiche ne doit pas garder un nom que l'ACPR a retiré.
- **2020-08 (anonymisée)** : la fiche ne reprend que ce qui sert à comprendre (siège au Luxembourg, groupe japonais de commerce en ligne). Deux anomalies du texte officiel notées dans la fiche, sans rien corriger : l'addition 634 + 2 314 donnée pour 2 978 (p. 6-7) et l'article « L. 562-2-1 » cité pour « L. 561-2-1 » (p. 4).
- Glossaire : 12 termes ajoutés (Direction générale du Trésor, mesure restrictive, « exact match » et recherche floue, homonymie, courtier, assurance non-vie, tacite reconduction, vigilance simplifiée, porte-monnaie électronique, place de marché, franc Pacifique, établissement de crédit). Conséquence normale : 8 fiches lisibles anciennes (.md) ont été refaites, leur lexique s'étant allongé. Leur contenu n'a pas changé.
- Aucun champ de la base à corriger pour ces trois décisions.
- Type d'établissement : deux nouveaux libellés (« prestataire de services de paiement (office des postes) », « établissement de crédit »). À harmoniser en session 3 avec la question 4.
- Issues : « périmètre réduit » = « retenu en partie » (2020-11 grief 1, 2020-08 griefs 3, 5, 8, 9). « Fondé » avec un exemple écarté ou une « portée limitée » = « retenu », avec la précision.

### Incident au dépôt du lot 1

Pendant la copie des fichiers, le dossier `workflows` est sorti de `.github` : GitHub Desktop affichait `collecte.yml` comme supprimé, plus une copie à la racine. Corrigé avant validation (clic droit > Discard changes sur les deux lignes). À surveiller à chaque dépôt : aucune ligne rouge, et le bon nombre de fichiers.

### Incident de session

Un premier passage sur le lot 1 a été interrompu avant la fin : il n'apparaissait plus dans la conversation, mais trois fiches (2024-01, 2022-05, 2022-06) et une première version du lexique étaient restées dans l'espace de travail. Elles n'ont pas été reprises telles quelles : chaque fiche a été relue en entier contre le texte de la décision, puis corrigée (détails retirés car absents du texte, un décompte de griefs rectifié). Leçon : livrer un .zip à la fin de chaque lot.

La même chose s'est produite pour le lot 2 : le passage qui l'a rédigé (lecture des cinq décisions, fiches, journal, .zip) s'est interrompu juste avant la livraison. Cette fois, les fiches n'ont pas été relues ligne à ligne : elles ont subi un contrôle ciblé contre les textes. Pour chaque grief, l'issue a été comparée à la phrase de conclusion de la décision ; chaque chiffre cité a été recherché dans les pages indiquées ; les décomptes de dossiers ont été relus dans le texte. Résultat : aucune erreur d'issue ni de chiffre, une référence de page complétée (fiche 2021-01, grief 3) et une phrase du « En bref » reformulée pour coller au texte (fiche 2021-05). Le lot 2 est donc un peu moins vérifié que le lot 1 : à relire par Matéo en priorité sur le PDF.

Pour limiter ce risque : des lots plus courts (3 décisions), et une conversation neuve.

### Constats sur la base et les sources

- Aucun champ de la base à corriger pour ces 13 décisions (montant, sanction, dates, publication concordent avec les textes).
- Coquille probable dans un texte officiel : la décision 2024-06 cite page 4 une « décision n° 2025-01 du 7 novembre 2025 » ; la décision de cette date porte le n° 2024-01. Noté dans la fiche, rien n'est corrigé.
- La décision 2018-05 (8 avril 2019, anonymisée) est marquée « hors LCB-FT » dans la base, mais son texte mentionne souvent le blanchiment. À vérifier quand on arrivera à 2019. Trois autres décisions « hors LCB-FT » en parlent un peu (2012-03, 2014-11, 2012-09) : à regarder aussi.
- Deux décisions (2022-05, 2024-01) mêlent griefs LCB-FT et griefs d'un autre ordre (agent non enregistré, protection de la clientèle, activité des succursales). Ces griefs sont classés « autre » ou « procédures et contrôle interne » avec la mention « grief hors LCB-FT ».

### Questions ouvertes pour Matéo

1. Faut-il une catégorie « agents et externalisation » ? Le thème revient dans 6 des 13 fiches (MoneyGram, Treezor, SFPMEI, Abeille Vie, BMW Finance, Nickel). Pour l'instant : mots-clés + précision de catégorie. Réponse de Matéo (12 novembre) : non pour l'instant, continuer avec des mots-clés. Le thème revient aussi dans 2020-08 (agent et distributeur) et 2020-09 (courtiers).
2. Longueur des fiches : 2 à 3 pages en version lisible. À raccourcir ou non pour la suite.
3. Le grief sur les informations qui accompagnent les transferts de fonds (W-HA, règlement UE 2015/847) est classé « autre ».
4. Type d'établissement : les fiches reprennent le terme de la décision (« banque », « établissement de crédit spécialisé », « établissement de paiement », « établissement de monnaie électronique », « assureur »). À harmoniser pour les filtres du site.
5. Les champs `statut` et `mes_notes` existent à la fois dans la base et dans la fiche. Proposition : la fiche fait foi ; à trancher en session 3.

### Points à vérifier par Matéo dans les fiches

Chaque fiche a une rubrique « Points à vérifier ». Les plus utiles : 2022-03 (décision longue, issues des griefs 3, 4 et 5), 2022-02 (grief 2 très découpé ; deux dates différentes pour le scénario sur les espèces), 2024-06 (grief 8 : deux chiffres différents dans la décision), 2023-01, 2022-07, 2022-01 et 2021-05 (décomptes de dossiers faits par Claude).

Décision à lire en premier pour la méthode : 2022-01 (Axa Banque), pages 11 et 12, où la Commission explique quand il faut un examen renforcé et quand il faut déclarer. Les décisions suivantes la citent souvent.

### Prochaine étape

Suite des fiches LCB-FT, des plus récentes aux plus anciennes, par lots de 3. Toutes les décisions restantes sont anonymisées : ne jamais chercher à retrouver l'établissement.

- Lot 3b : 2020-06, 2020-05, 2020-03 – 43 pages.
- Lot 4a : 2020-02, 2019-08, 2020-01 – 35 pages.
- Lot 4b : 2019-07, 2019-06, 2019-04 – 47 pages.
- Lot 5 : 2018-08, 2018-06, 2018-03 – 34 pages.
- Lot 6 : 2018-04, 2017-10, 2018-05 – 28 pages. 2018-05 (radiation, 5 pages) est marquée « hors LCB-FT » dans la base : vérifier à la lecture ; fiche courte si c'est confirmé. On atteint alors janvier 2019 et 31 fiches.

Calendrier visé : 30 fiches le 13 novembre au soir, site le 14, étude comparative le 15. Si les crédits manquent : s'arrêter après le lot 4b (25 fiches, tout 2020-2026 couvert) et garder le site, qui compte plus pour un recruteur que cinq fiches de 2018-2019.

Une nouvelle conversation tous les deux lots. Message de reprise : « Session 2, suite : lis PROJET.md et JOURNAL.md, récupère le dépôt, prends ACPR-2020-08 comme modèle de fiche anonymisée et traite le lot suivant du journal. »

Reste hors de portée d'ici le 15 novembre : les 36 décisions LCB-FT antérieures à 2019 et les 45 fiches courtes « hors LCB-FT ».

---

## Session 1 – 12 novembre 2026 – Lancement et collecte ACPR

Dépôt : https://github.com/Mateo180805/sanctions-conformite (public)

### État à la fin de la session

- [x] Programme de collecte ACPR écrit et testé sur toutes les décisions du recueil.
- [x] Base : 111 décisions (janvier 2011 à mai 2026), toutes au statut « à lire ».
- [x] Workflow GitHub Actions écrit (chaque lundi + lancement manuel).
- [x] Dépôt GitHub public créé et fichiers déposés par Matéo avec GitHub Desktop.
- [x] Première collecte lancée à la main sur GitHub le 12 novembre 2026 : réussie, 3 décisions ajoutées, 0 erreur.
- [ ] Première collecte automatique : lundi 16 novembre 2026 vers 7 h 17, heure de Paris (à vérifier par Matéo).

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
- Le site est protégé par un filtre (Akamai) qui refuse certains identifiants de programme (code 403). L'identifiant du projet, qui donne l'adresse du dépôt GitHub, est accepté. Les serveurs de GitHub sont acceptés (vérifié le 12 novembre 2026).

### Choix faits

- **Identifiant** : `ACPR-` + numéro de procédure (ex. `ACPR-2024-06`). Deux décisions différentes pour une même procédure : la seconde reçoit sa date (`ACPR-2013-02-du-2014-03-19`).
- **Une seule base** `donnees/decisions.json` pour tous les régulateurs, plus une copie CSV pour Excel. Un fichier texte par décision, avec un repère « ===== Page N ===== » pour pouvoir citer les pages.
- **Un module par régulateur** (`collecte/acpr.py`), des outils communs (`collecte/commun.py`), un point d'entrée (`collecte/lancer.py`). Ajouter l'AMF = écrire `amf.py` et l'inscrire dans `lancer.py`.
- **Seulement le nouveau** : une décision est reconnue par l'adresse de sa page. Si son titre change dans le recueil (anonymisation), elle est retéléchargée et remplace l'ancienne ; le statut et les notes sont conservés.
- **Rien n'est deviné** : champ vide + alerte quand l'en-tête ne se lit pas bien. 8 décisions ont une alerte.
- **Anonymisation** (sur les 111 décisions) : 33 anonymisées, 1 « à vérifier » (procédure 2016-08), 77 nominatives. Pour une décision anonymisée, le champ `etablissement` vaut « anonymisé ».
- **Parade aux 60 jours** : GitHub désactive les tâches programmées d'un dépôt public après 60 jours sans activité (règle vérifiée dans la documentation GitHub). Chaque collecte réécrit `donnees/derniere_collecte.json` et l'enregistre, donc une activité par semaine.
- **Dépôt des fichiers avec GitHub Desktop** plutôt que par le site : le site refuse plus de 100 fichiers à la fois et gère mal le dossier caché `.github`.

### Test de la chaîne complète : réussi

Les trois décisions les plus récentes (`ACPR-2024-01`, `ACPR-2024-06`, `ACPR-2025-01`) ont été retirées exprès de la base livrée. La première collecte sur GitHub les a retrouvées et ajoutées : toute la chaîne fonctionne (liste, page, PDF, texte, enregistrement dans le dépôt).

### Points ouverts

1. **Accès de GitHub au site de l'ACPR** : fonctionne aujourd'hui. Le filtre du site peut changer : en cas de refus (403) un jour, plan B du README.
2. **Adresses officielles qui trahissent un nom** : pour quelques décisions anonymisées, l'adresse de la page ou du PDF sur le site de l'ACPR contient encore un nom. La base ne s'en sert pas pour identifier qui que ce soit, mais ces liens seront visibles sur le site. À décider en session 3 (par exemple : n'afficher que le numéro de procédure et un lien « source officielle »).
3. **Noms de personnes physiques** : certains titres officiels et en-têtes citent des dirigeants. Ils sont dans la base tels que publiés par l'ACPR. Sur le site (session 3), ils ne devront pas être mis en avant.
4. **Montants** : 15 décisions sans montant lu. Pour la plupart, c'est normal (blâme seul, interdiction, mise hors de cause). Pour 5, il faut lire le PDF : 2021-04, 2015-02, 2012-02 (plusieurs personnes sanctionnées), 2011-03, 2010-02 (sanction absente de l'en-tête).
5. **Recours** : les suites (recours, arrêts du Conseil d'État) sont reprises du recueil dans le champ `suites`. Neuf rattachements automatiques d'arrêts du Conseil d'État sont à vérifier (marqués « à vérifier » dans le texte).
6. **Routine avant chaque session** : dans GitHub Desktop, cliquer « Fetch origin » puis « Pull origin » pour récupérer les décisions ajoutées par la collecte automatique, puis compresser le dossier du dépôt en .zip et le donner à Claude.

### Avant la session 2 (pour Matéo)

- Vérifier lundi 16 novembre que la collecte a tourné (onglet Actions du dépôt : une ligne verte datée du jour).
- Ouvrir `donnees/decisions.csv` dans Excel et parcourir la liste.
- Lire en entier deux ou trois décisions LCB-FT récentes, pour savoir à quoi ressemble une décision avant qu'on construise les fiches. Suggestions : 2024-06 (établissement de paiement), 2024-02 (banque, avec gel des avoirs), 2022-07 (monnaie électronique).
- Réfléchir à deux questions : la session 2 traite-t-elle les 66 décisions LCB-FT d'un coup ou par lots de 10 ? Les fiches « hors LCB-FT » sont-elles faites en même temps ?

### Prochaine étape

Session 2 : fiches d'analyse. Commencer par un essai de la grille sur 3 décisions, à valider avant de traiter un lot.
