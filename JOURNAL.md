# JOURNAL – Sanctions Conformité

Journal de bord du projet, version courte (allégée le 13 novembre 2026 pour économiser le quota).
À redonner à Claude au début de chaque session, avec PROJET.md.
Le détail lot par lot est dans `JOURNAL-ARCHIVE.md` : ne pas le relire au début d'une session, seulement au besoin.

Dépôt : https://github.com/Mateo180805/sanctions-conformite (public)

---

## Où on en est (13 novembre 2026)

- [x] Session 1 : collecte ACPR. Base de 111 décisions (2011 à 2026), mise à jour chaque lundi par GitHub Actions.
- [x] Session 2 : fiches d'analyse, lots 1 à 6. **31 fiches sur 67 décisions LCB-FT** : toutes les décisions LCB-FT et gel des avoirs rendues entre janvier 2019 et avril 2026. Aucune n'a encore été relue par Matéo (statut « à lire »).
- [ ] Session 3 : le site (GitHub Pages). **C'est la prochaine étape.**
- [ ] Session 4 : étude comparative et liste des points de contrôle, sur les 31 fiches.
- [ ] Plus tard : les 36 décisions LCB-FT antérieures à 2019, les 44 fiches courtes « hors LCB-FT », puis AMF, CSSF, FINMA.

Les 31 fiches : 2024-06, 2024-02, 2024-01, 2023-01, 2022-07, 2022-06, 2022-05, 2022-04, 2022-03, 2022-02, 2022-01, 2021-05, 2021-01, 2020-11, 2020-09 (nominatives) ; 2020-08, 2020-06, 2020-05, 2020-03, 2020-02, 2020-01, 2019-08, 2019-07, 2019-06, 2019-04, 2018-08, 2018-06, 2018-05, 2018-04, 2018-03, 2017-10 (anonymisées).

Lot 6 (13 novembre) :

| Décision | Établissement (anonymisé) | Sanction | Griefs retenus / en partie / écartés |
|---|---|---|---|
| 2018-04 | grande banque coopérative régionale d'un groupe | blâme, 2 M€ | 4 / 1 / 0 |
| 2017-10 | établissement de paiement irlandais, transfert d'argent par agents | blâme, 1 M€ | 5 / 2 / 3 |
| 2018-05 | changeur manuel, un seul guichet | radiation | 4 / 0 / 0 |

## Comment sont faites les fiches

- **Fiche source** : `donnees/fiches/acpr/ACPR-2024-06.json`, format structuré (identité, contrôle, sanction, procédure, griefs, contexte, points de contrôle déduits, « pour moi »). C'est elle que le site et l'étude doivent lire.
- **Version lisible** : `fiches/acpr/ACPR-2024-06.md`, fabriquée par `analyse/fiches.py`. Ne pas la modifier à la main.
- **`analyse/fiches.py`** vérifie chaque fiche (catégories de la grille, pages existantes, « En bref » présent), fabrique la version lisible, et s'arrête en erreur au moindre problème.
- **Glossaire** : `donnees/glossaire.json` (114 termes). Chaque entrée a un terme, une liste de mots à chercher et une définition ; le lexique d'une fiche ne reprend que les termes qu'elle emploie.
- **Texte des décisions** : `donnees/textes/acpr/`, un fichier par décision, avec un repère « ===== Page N ===== ».
- Marquer une fiche comme lue : modifier `"statut"` et `"mes_notes"` au début du .json, puis relancer le programme.
- Fiches modèles : ACPR-2020-08 (anonymisée) ; ACPR-2019-08 (décision qui ne conclut pas grief par grief) ; ACPR-2019-07 (beaucoup de griefs hors LCB-FT).

## Règles fixées

- Trois issues par grief : « retenu », « retenu en partie », « écarté ». « Périmètre réduit » = retenu en partie. « Fondé » ou « établi » mais relativisé, ou de portée limitée = retenu, avec la précision.
- Une catégorie principale par grief (13 catégories, liste dans `analyse/fiches.py`), plus des catégories secondaires facultatives. L'étude compte sur la catégorie principale.
- Les griefs hors LCB-FT d'une décision LCB-FT restent dans la fiche avec la mention « grief hors LCB-FT » dans `categorie_precision`, et sont **exclus des comptages de l'étude** (décision de Matéo, 12 novembre). Fiches concernées : 2019-07, 2022-05, 2024-01, 2018-06 (grief 3).
- La vigilance renforcée ou complémentaire (pays à haut risque) est rangée avec les personnes politiquement exposées. La COSI est rangée avec les déclarations de soupçon, avec une précision (décision du 12 novembre). Pas de catégorie « agents et externalisation » : des mots-clés (« agent et distributeur », « externalisation »).
- Anonymisation : une fiche suit le texte officiel en ligne (nom si le PDF le donne, « anonymisé » sinon). On ne cherche jamais un nom retiré. Aucun nom de personne physique. Les montants masqués par l'ACPR restent masqués.
- Ce qui est déduit est isolé dans le bloc « Ce qui aurait dû être fait ». Les décomptes faits par Claude et les coquilles des textes officiels sont signalés dans « Points à vérifier », sans rien corriger.
- Fiche 2019-06 : l'indice religieux cité page 11 de la décision reste hors du résumé (décision du 12 novembre).
- Méthode par lot : 3 décisions ; lecture des textes sans en-têtes ni pieds de page ; après rédaction, `analyse/fiches.py`, recherche automatique de chaque nombre dans les pages citées, issues comparées à la phrase de conclusion de chaque grief ; livraison d'un .zip.

## Questions ouvertes pour Matéo

- **4.** Type d'établissement : les fiches reprennent le terme de la décision (une dizaine de libellés). À regrouper pour les filtres du site. Session 3.
- **5.** `statut` et `mes_notes` existent dans la base et dans la fiche. Proposition : la fiche fait foi. Session 3.
- **6.** Faut-il une quatrième issue « abandonné par la poursuite » ? Trois griefs concernés (2020-06 grief 13, 2019-07 grief 11, 2017-10 grief 2), classés « écarté » avec précision. D'autres « écartés » ne valident rien non plus (erreur de base légale, preuve insuffisante). À trancher avant l'étude.
- **10.** Fiche 2018-03 : la date exacte de la sanction de 2015 est tue et les deux fiches ne seront pas reliées sur le site. Choix provisoire de Claude, à confirmer.
- **11.** Fiche 2018-06 : grief 11 « retenu » ou « retenu en partie » ? Grief 3 bien « hors LCB-FT » ?
- **12.** Classements à harmoniser avant l'étude : identification des clients occasionnels (2018-05 et 2017-10, grief 1) ; connaissance du client non mise à jour (2018-04 grief 4 et 2018-06 grief 7, rangés différemment) ; griefs classés « autre » (données de chargement de la monnaie électronique, informations sur les virements, conservation des données, réponses inexactes au questionnaire de l'ACPR).
- Longueur des fiches (2 à 3 pages) : à raccourcir ou non.

Questions closes : 1 (pas de catégorie agents), 7 (anonymisation), 8 (COSI), 9 (griefs hors LCB-FT).

## À traiter en session 3 (le site)

- **Noms résiduels** : plusieurs textes officiels anonymisés laissent passer un nom ou des détails qui resserrent l'identification (2020-05 p. 4, 2020-03 p. 7, 2020-01 p. 11, 2018-03 p. 7, 2018-06 p. 4, 2018-04 p. 8, 2017-10 p. 2 et 13). Le site ne doit ni afficher ni rendre cherchables les textes de `donnees/textes/` : il s'appuie sur les fiches.
- **Adresses officielles qui trahissent un nom** : pour quelques décisions anonymisées, l'adresse de la page ou du PDF contient encore un nom. Proposition : afficher le numéro de procédure et un lien « source officielle ».
- **Noms de personnes physiques** : certains titres et en-têtes de la base citent des dirigeants. Ne pas les mettre en avant.
- **Fiches à anonymiser bientôt** : 2020-09 (MMA IARD, fin novembre 2026) et 2020-11 (février 2027). Quand l'ACPR retire le nom, la collecte retélécharge la décision ; il faut alors retirer le nom de la fiche. Une fiche ne doit pas garder un nom que l'ACPR a retiré.
- Le site doit fonctionner avec 31 fiches complètes et 80 décisions sans fiche (statut clair : « fiche à venir »).
- Page « Méthode » : dire quel modèle a fait quoi (fiches : Fable 5.2 ; site : le modèle utilisé en session 3), puis relecture par Matéo.
- Emplacements à laisser pour les textes de Matéo (introduction, À propos).

## À savoir pour la session 4 (l'étude)

- Compter sur la catégorie principale ; exclure les griefs « hors LCB-FT » ; ne pas lire un « écarté » comme une pratique validée (question 6).
- Décisions à part : 2019-08 (avertissement, sans amende, financement participatif) ; 2018-03 (blâme sans amende à cause de la situation financière) ; 2018-05 (radiation) ; 2020-09 (gel des avoirs seulement) ; 2019-07 (21 griefs dont beaucoup hors LCB-FT).
- Thèmes transversaux déjà repérés (détail et références dans l'archive) : mauvaise connaissance du client à l'origine des défauts de déclaration ; stocks d'alertes et délais ; alertes closes sans analyse écrite ; seuils sans rapport avec l'opération moyenne ; fractionnement ; bloquer un client ne remplace pas la déclaration ; déclarations complémentaires oubliées ; gel des avoirs (« exact match », mesures nationales, fréquence du filtrage, obligation de résultat) ; dispense de la monnaie électronique mal appliquée ; agents, distributeurs et prestataires qui n'excusent pas l'établissement ; outil ou règle du groupe ; argument « les textes n'étaient pas clairs », toujours rejeté ; petite structure et montant de l'amende ; plusieurs griefs pour les mêmes faits ; demandes d'un contrôle précédent restées sans suite.
- Décisions utiles pour les futures sessions Luxembourg et Suisse : 2020-08, 2019-06 (établissements luxembourgeois, partage ACPR / CSSF), 2018-08 et 2017-10 (passeport européen, représentant permanent).

## Rappels de la session 1 (collecte)

- Source : le « Recueil des sanctions » de l'ACPR. Programme : `collecte/acpr.py`, `collecte/commun.py`, `collecte/lancer.py`. Base : `donnees/decisions.json` et sa copie `decisions.csv`.
- Le champ `lcbft_indice` vient des thèmes du recueil. Il était faux pour 2018-05 (corrigé à la main le 13 novembre). Trois autres décisions « hors LCB-FT » parlent de blanchiment et restent à vérifier : 2012-03, 2014-11, 2012-09.
- 5 décisions sans montant lu, à vérifier dans le PDF : 2021-04, 2015-02, 2012-02, 2011-03, 2010-02. Neuf rattachements d'arrêts du Conseil d'État à vérifier. Deux lignes du recueil ont un lien erroné (2014-05 et 2013-04).
- Si GitHub ne peut plus accéder au site de l'ACPR (403) : plan B du README (collecte depuis l'ordinateur de Matéo).
- À vérifier par Matéo : la première collecte automatique, lundi 16 novembre 2026 (onglet Actions du dépôt, une ligne verte).

## Routine de dépôt (GitHub Desktop)

1. Décompresser le .zip livré et copier son contenu dans le dossier du dépôt, en remplaçant les fichiers.
2. Vérifier le nombre de fichiers annoncé et l'absence de ligne rouge (le dossier `workflows` doit rester dans `.github`).
3. « Commit to main », puis **« Push origin »** (oublié une fois, au lot 4a).
4. Avant chaque session : « Fetch origin » puis « Pull origin ».

## Quota et choix du modèle

- Un lot de 3 fiches a coûté environ 17 points de la jauge Fable de Matéo (lot 5), pas 7. La jauge Fable se réinitialise le lundi à 10 h.
- Fable 5.2 : à garder pour les fiches et pour le texte de l'étude. Le site et les programmes de comptage peuvent être faits avec un autre modèle (Opus 5.5 ou Sonnet 5.5).
- À la fin de chaque demande, Claude indique le modèle et le niveau d'effort conseillés pour la suivante (demande de Matéo, 13 novembre).
- Pour économiser : une conversation neuve par session ; ne lire que ce journal et PROJET.md ; ne lire une fiche ou l'archive que si la tâche le demande.

## Prochaine étape

**Session 3 – le site**, dans une nouvelle conversation, après dépôt du lot 6 sur GitHub.

Message de reprise : « Session 3 : lis PROJET.md et JOURNAL.md (pas l'archive), récupère le dépôt, vérifie qu'il contient bien le lot 6 (31 fiches) et commence le site. Avant de coder, propose-moi le plan et la maquette de la page d'accueil et d'une fiche. »

Modèle conseillé pour cette session : Opus 5.5, effort élevé pour la première demande (plan, structure, maquette), puis effort moyen pour les pages suivantes.
