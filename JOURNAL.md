# JOURNAL – Sanctions Conformité

Journal de bord du projet, version courte (allégée le 13 novembre 2026 pour économiser le quota ; mise à jour au lot 8).
À redonner à Claude au début de chaque session, avec PROJET.md.
Le détail lot par lot est dans `JOURNAL-ARCHIVE.md` : ne pas le relire au début d'une session, seulement au besoin.

Dépôt : https://github.com/Mateo180805/sanctions-conformite (public)

---

## Où on en est (13 novembre 2026, session 5)

- [x] Session 1 : collecte ACPR. Base de 111 décisions (2011 à 2026), mise à jour chaque lundi par GitHub Actions.
- [x] Session 2 : fiches d'analyse, lots 1 à 6. **31 fiches sur 67 décisions LCB-FT** : toutes les décisions LCB-FT et gel des avoirs rendues entre janvier 2019 et avril 2026. Aucune n'a encore été relue par Matéo (statut « à lire »).
- [x] Session 3 : le site (GitHub Pages), construit avec Opus 5.5 et **en ligne depuis le 13 novembre** (31 fiches vérifiées sur le site publié). Textes de l'accueil et de la page À propos rédigés par Claude et validés par Matéo.
- [x] Session 4 : étude comparative (page Analyse) et liste de 69 points de contrôle (nouvelle page), sur les 31 fiches. Rédigées avec Fable 5.2, **pas encore relues par Matéo**.
- [x] Session 5 : collecte AMF (avec Opus 5.5). **454 décisions de la Commission des sanctions de l'AMF** (2004 à juillet 2026) ajoutées à la base et au site, mise à jour chaque lundi avec l'ACPR. Pas de fiches AMF.
- [x] Lots 7a et 8 (13 novembre au soir, Opus 5.5) : 8 fiches de décisions d'avant 2019 (2018-01, 2017-01 à 2017-07). **39 fiches.** L'étude reste sur ses 31 décisions de 2019-2026.
- [ ] Plus tard : les 28 décisions restantes LCB-FT de l'ACPR antérieures à 2019, les 44 fiches courtes « hors LCB-FT », des fiches AMF (en commençant par les 28 signalées blanchiment), puis CSSF et FINMA.

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

## Décisions prises (toutes les questions sont closes)

Matéo a validé le 13 novembre l'ensemble des propositions et laissé Claude trancher le reste.

- **4.** Types d'établissement regroupés pour le filtre du site : Banque ; Paiement et monnaie électronique ; Assurance ; Change manuel ; Financement participatif (dictionnaire `TYPES`, dans `analyse/etude.py` depuis la session 4). La fiche garde le terme exact.
- **5.** La fiche fait foi pour le statut « lue » ; `mes_notes` n'est pas publié.
- **6.** Pas de quatrième issue. Les griefs abandonnés par la poursuite restent « écarté » avec leur précision. Dans l'étude, les « écartés » sont comptés à part et ne sont jamais présentés comme des pratiques validées.
- **10.** Fiche 2018-03 : la date de la sanction de 2015 reste tue et les deux fiches ne sont pas reliées.
- **11.** Fiche 2018-06 : grief 11 laissé « retenu », grief 3 laissé « hors LCB-FT ».
- **12.** Appliquée le 13 novembre (session 4 ; un seul grief a changé : 2018-06 grief 7, passé en « vigilance constante et mise à jour des dossiers ») : identification des clients occasionnels -> « relation d'affaires et clients occasionnels » ; connaissance du client non mise à jour -> « vigilance constante et mise à jour des dossiers » ; les griefs « autre » restent « autre » avec leur précision.
- **13.** Le lien « Source officielle » garde l'adresse de l'ACPR (c'est la source publique) ; le site n'affiche jamais le nom.
- Longueur des fiches : inchangée.
- (Remplacé le 13 novembre au soir, à la demande de Matéo.) Le statut de relecture n'est plus affiché sur le site ; la page Méthode dit que les fiches sont une première analyse rédigée avec Claude.

## Le site (session 3)

Adresse prévue : https://mateo180805.github.io/sanctions-conformite/

- **Fonctionnement** : `site/construire.py` (Python sans bibliothèque à installer) lit `decisions.json`, les fiches et le glossaire, et fabrique les pages dans `_site/` (non enregistré dans le dépôt). `.github/workflows/site.yml` vérifie les fiches (`analyse/fiches.py`), fabrique le site et le publie à chaque dépôt sur `main`, après chaque collecte du lundi, ou avec « Run workflow ». Réglage GitHub nécessaire une fois : Settings > Pages > Source : « GitHub Actions ».
- **Pages** : Accueil, Base (tableau, recherche, filtres régulateur / année / type / manquement retenu / montant / thème / « seulement analysées », tri date et montant, filtres recopiés dans l'adresse), une page par fiche, Analyse et Points de contrôle (session 4), Méthode, Lexique (114 termes), À propos.
- **Style** : fond blanc, encre bleu-noir, un seul accent bleu pétrole (#0d5c64), titres en Newsreader, texte en Public Sans (polices libres, hébergées avec le site, licences dans `site/statique/polices/`). Signe distinctif : la « frise des griefs », une barre par grief (pleine = retenu, hachurée = en partie, vide = écarté). Testé sur ordinateur et téléphone (390 px), sans erreur JavaScript ; le site reste lisible sans JavaScript.
- **Textes de Matéo** : `site/textes/introduction.txt` et `site/textes/a-propos.txt` (texte simple ; lignes commençant par # ignorées ; une adresse web devient un lien). Tant qu'ils sont vides, un cadre « Emplacement réservé » s'affiche. Textes fixes : `site/pages/methode.html` (écrit à la première personne, **à relire par Matéo**) et `site/pages/analyse.html`.
- **Garde-fous** : le site ne lit jamais `donnees/textes/`. Noms de personnes physiques retirés des noms d'établissement des décisions sans fiche (2011-03, 2015-01, 2015-04, 2016-08), vérifié sur tout le site. Si l'ACPR anonymise une décision dont la fiche garde un nom (2020-09 fin novembre 2026, 2020-11 février 2027), la fiche est retirée du site, le reste est publié, et la tâche « Site » passe au rouge (e-mail). Il faut alors anonymiser la fiche.
- **Choix d'affichage** : sur une fiche publique, pas de « points à vérifier » ni de « mes notes » (notes de travail) ; on affiche le statut de relecture, le niveau de confiance, les pages à lire, les mots-clés. Les noms écrits TOUT EN CAPITALES dans le recueil sont remis en minuscules à l'affichage (sigles connus conservés). Le lien « Source officielle » garde l'adresse de l'ACPR, qui contient encore un nom pour quelques décisions anonymisées (visible au survol) : à trancher (remplacer par le lien du recueil ?).
- **Ajouts du 13 novembre après mise en ligne** : fond blanc cassé (#faf7f2) et accent plus présent ; transitions discrètes (changement de page, ouverture des griefs, filtres), coupées si l'appareil demande moins d'animations ; aperçu de partage pour LinkedIn (balises Open Graph et image `site/statique/apercu.png`) ; page 404.
- La base est triée par date de décision, pas par numéro de procédure : 2017-10, 2018-04 et 2018-05 (jugées en 2019) apparaissent parmi les lignes de 2019.
- Le lien LinkedIn n'est pas encore sur la page À propos : l'ajouter à la fin de `site/textes/a-propos.txt` (adresse complète).

## L'étude (session 4)

- **Programme** : `analyse/etude.py` compte à partir des fiches et écrit `donnees/etude/chiffres.json` ; il vérifie aussi la liste des points de contrôle et fabrique sa copie CSV. Le site appelle les mêmes fonctions : graphiques et tableaux suivent les fiches tout seuls. Le regroupement des types d'établissement (`TYPES`) est maintenant défini une seule fois, dans `analyse/etude.py`.
- **Règles de comptage** : unité principale = la décision où le manquement est retenu, en entier ou en partie ; nombre de griefs donné à côté ; catégorie principale seulement ; griefs hors LCB-FT exclus (14) ; écartés comptés à part.
- **Chiffres clés** : 31 décisions, 236 griefs (162 retenus, 63 en partie, 11 écartés). En tête : déclarations de soupçon (26 décisions), alertes et examen renforcé (22), surveillance (21), contrôle interne (20), gel des avoirs (18 sur les 21 qui l'examinent). 28 amendes, de 20 000 € à 4 M€, total 32,76 M€ ; jamais au-dessus de la demande du Collège (19 en dessous, 9 égales).
- **Texte** : `site/pages/analyse.html`. Les repères `[[2020-05]]` et `[[2020-05#11]]` deviennent des liens vers la fiche ou le grief (pas de lien si la fiche est retirée du site). Aucun nom d'établissement dans le texte, pour ne pas dépendre de l'anonymisation. Les chiffres écrits dans les phrases sont ceux du 13 novembre sur 31 fiches : si le nombre de fiches change, un bandeau « Texte à mettre à jour » s'affiche (constantes `ETUDE_NB_FICHES` et `ETUDE_DATE` dans `site/construire.py`) et il faut reprendre le texte.
- **Points de contrôle** : `donnees/etude/points_de_controle.json` est la source (69 points, identifiants du type DS-1, GEL-2). Chaque point a une question, une ligne « à demander » et les griefs qui l'illustrent. Le programme refuse un point qui cite un grief inexistant, écarté ou hors LCB-FT. Pour marquer la liste comme relue : passer `"relu_par_mateo"` à `true` dans ce fichier.
- **Choix faits par Claude** (Matéo a laissé trancher) : page « Points de contrôle » à part, dans le menu ; étude publiée avec la mention « fiches pas encore relues » ; graphiques faits de tableaux HTML avec barres (lisibles sans JavaScript et sur téléphone), dans le style de la frise des griefs ; la sanction de 2015 de la fiche 2018-03 n'est pas citée dans l'étude (décision 10).
- **Points à vérifier par Matéo** : la leçon 8 de l'étude (« douze décisions au moins » où le défaut était déjà signalé) est un décompte fait par Claude à partir du champ « antécédents » des fiches ; le montant demandé par le Collège est lu automatiquement dans une phrase de la fiche (vérifié à l'œil sur les 31) ; 2020-11 grief 5 (signalements classés sans analyse) est rangé en « vigilance constante », ce qui se discute.

## La collecte AMF (session 5)

- **Source** : la page « Décisions de la Commission des sanctions » de l'AMF remplit son tableau à partir d'une liste JSON (`/fr/rest/listing_sanction/<thèmes>/all/all`). Une seule requête donne toute la liste (454 lignes le 13 novembre). Programme : `collecte/amf.py`, branché dans `collecte/lancer.py` (`python collecte/lancer.py amf`, ou sans rien pour les deux régulateurs). Le site de l'AMF accepte l'identifiant du projet ; robots.txt ne l'interdit pas.
- **Identifiant** : `AMF-` + numéro officiel, par exemple `AMF-SAN-2026-07`. Le champ `numero_procedure` contient « SAN-2026-07 » ; le numéro de procédure interne lu dans le PDF récent (« 25-05 ») est dans `procedure_interne`.
- **Ce qui vient de la liste** : thème choisi par l'AMF (`theme_court`), personnes visées, montant total avant recours (toutes personnes confondues), recours (oui/non, dans `suites`), lien du PDF. **Ce qui vient du PDF** : date de la décision (« Décision n° 6 du … » ou « A Paris, le … »), date de la séance, nombre de pages, nombre de mentions du blanchiment (`lcbft_mentions` ; `lcbft_indice` vrai à partir de 3 : **28 décisions**, presque toutes en « obligations professionnelles » ou « conseillers et autres prestataires »).
- **Personnes physiques (choix de Claude, à valider)** : la base n'enregistre jamais leur nom. `etablissement` ne garde que les sociétés ; `nom_site` affiche « Société X et 2 personnes physiques ». `publication` = « nominative » si un vrai nom (société ou personne) figure dans la liste. Le texte intégral des décisions AMF n'est **pas** copié dans `donnees/textes/` (`GARDER_TEXTE = False`) : l'AMF publie les noms des particuliers pour une durée limitée et l'historique d'un dépôt public est permanent. Pour une fiche AMF, Claude relit le PDF officiel (`amf.texte_d_une_decision`). Limites : des noms de société contiennent un nom de famille (« Salzillo Finance », « Nicolas Miguet et Associés ») ; l'adresse officielle de quelques PDF anciens contient un nom (2009-31, 2009-33), comme pour l'ACPR (décision 13).
- **Mise à jour** : une décision est retéléchargée si sa ligne change (empreinte `empreinte_ligne` : personnes, sanction, PDF), par exemple après une anonymisation. Quand rien n'a changé : 2 requêtes par semaine. `lancer.py` enregistre maintenant la base toutes les 20 décisions (rien n'est perdu si GitHub coupe une exécution).
- **Contrôles faits** : 419 dates lues dans le PDF ; chaque fois que le titre officiel donne aussi une date, les deux concordent. 35 dates viennent seulement du titre officiel (alerte « Date prise dans l'adresse », dont les 3 décisions sans PDF). Toutes les décisions ont une date. Aucun nom de personne physique de la liste ne se retrouve dans la base (vérifié automatiquement sur 93 noms). Une nouvelle collecte juste après ne trouve rien à refaire.
- **À vérifier par Matéo (non bloquant)** : 39 décisions ont une alerte (`alertes` dans `decisions.json`) : 35 dates prises dans le titre, 7 désignations à vérifier (sociétés sans le mot « société », ex. « BNP PARIBAS SA »), 3 sans PDF (SAN-2014-18, SAN-2013-02, SAN-2010-05, dont une sanction annulée par le Conseil d'État). 57 décisions sans montant : ce sont des avertissements, blâmes, interdictions ou mises hors de cause.
- **Site** : les décisions AMF apparaissent dans la Base (filtre « Régulateur »), avec le thème de l'AMF sous le nom et la mention « Pas encore de fiche ». Accueil (titre « Ce que l'ACPR et l'AMF reprochent à ceux qu'elles sanctionnent », un paragraphe de chiffres AMF), Méthode (sources, règle sur les personnes physiques, limites) et pied de page mis à jour. Les pages Analyse et Points de contrôle restent sur les 31 fiches ACPR. Corrigé au passage : sur téléphone, les filtres de la Base mettaient le compteur à jour sans masquer les lignes (défaut de la session 3, une ligne dans `style.css`).
- Le texte d'introduction de Matéo (`site/textes/introduction.txt`) parle encore seulement de l'ACPR : à adapter par lui s'il le souhaite.
- **Risque** : on ne sait pas encore si le site de l'AMF accepte les serveurs de GitHub. À vérifier lundi 16 novembre (onglet Actions). Si l'AMF refuse : plan B du README (`python collecte/lancer.py amf` depuis l'ordinateur).

## Fin de journée du 13 novembre : textes et mise en forme

- **Textes complétés à la place de Matéo** (à relire par lui) : l'introduction de l'accueil et la page À propos mentionnent maintenant l'AMF ; la présentation du README est écrite. Le lien LinkedIn reste à coller par Matéo : une ligne en commentaire l'attend à la fin de `site/textes/a-propos.txt` (enlever le # du début).
- **Mise en forme, sans changer le contenu** (`site/statique/style.css`, bloc « Mise en forme générale » à la fin ; dans `site/construire.py`, seulement une classe `p-...` ajoutée à `<body>`) :
  - chaque page a son bandeau d'en-tête, avec une petite mention au-dessus du titre : accueil sombre, Base beige, Analyse bleu pétrole foncé, Points de contrôle bleu pétrole très clair, fiche blanche avec ses chiffres clés encadrés, Méthode, Lexique et À propos blancs avec un filet ; un motif de « frise » à droite sur grand écran ;
  - le contenu est rangé dans des blocs blancs bordés : filtres, tableau de la base, sections des fiches, sommaire, étude et graphiques, points de contrôle par catégorie, lettres du lexique (sur deux colonnes) ;
  - menu avec la page en cours sur fond d'accent ; pied de page sombre ;
  - testé sur ordinateur et sur téléphone (390 px), sans erreur JavaScript ni débordement horizontal.

## Soir du 13 novembre : décisions de Matéo et lot 7 (avec Opus 5.5, Fable épuisé)

- **AMF limitée à 2011** (demande de Matéo) : on garde les décisions numérotées à partir de 2011, comme l'ACPR (première décision en janvier 2011), plus 7 exceptions définies dans `collecte/amf.py` (`PREMIERE_ANNEE`, `GARDEES_AVANT_2011`) : les 5 plus fortes sanctions d'avant 2011 (SAN-2006-14, 2007-19, 2009-09, 2007-16, 2010-04) et les 2 décisions anciennes sur le blanchiment (SAN-2009-22, 2009-01). **280 décisions AMF** au lieu de 454. La collecte du lundi applique le même filtre. Justification affichée sur la page Méthode : loi du 22 octobre 2010 (plafond porté à 100 millions d'euros).
- **Plus de prénom sur le site, sauf À propos** (demande de Matéo) : suppression de « pas encore relue par Matéo » sur les fiches et de la ligne « Relecture » ; pied de page « Site personnel (à propos) » sans le nom ; compteur de fiches relues retiré de la page Méthode ; avertissements de l'étude reformulés sans mention de relecture. La page Méthode garde la phrase honnête : fiches, étude et points de contrôle sont une première analyse ; seul le texte officiel fait foi. Le statut « à lire » / « lue » reste dans les fichiers, non affiché. **Ceci remplace la règle « les fiches gardent la mention pas encore relue ».**
- **Page À propos réécrite**, plus longue et moins formelle (parcours en banque, origine du projet, ce qu'il cherche, partie technique). Lien LinkedIn toujours à coller par Matéo.
- **Priorité choisie par Matéo** : d'abord les 36 décisions LCB-FT de l'ACPR antérieures à 2019, même méthode que Fable, lots de 3. Ensuite seulement le reste (44 fiches courtes hors LCB-FT, puis AMF). Plus de développement du site ni de nouveau régulateur pour l'instant.
- **Lot 7 (Opus 5.5)** : 3 fiches. Méthode inchangée (lecture complète, `analyse/fiches.py`, recherche de chaque nombre dans les pages citées, issues comparées aux phrases de conclusion). Le script de recherche des nombres est à refaire à chaque session (il était dans /tmp) : extraire les nombres des chiffres clés, résumés et précisions, et les chercher dans les pages citées du texte.

| Décision | Établissement (anonymisé) | Sanction | Griefs retenus / en partie / écartés |
|---|---|---|---|
| 2018-01 | grande banque de détail, « mandats cash » non filtrés (gel des avoirs) | blâme, 50 M€ | 4 / 0 / 0 |
| 2017-03 | assureur vie absorbé, bons de capitalisation au porteur | 800 000 € (pas de blâme : fusion-absorption) | 7 / 1 / 0 |
| 2017-02 | assureur absorbé, même groupe et même jour que 2017-03 | 200 000 € (idem) | 6 / 1 / 1 |

- Points à vérifier signalés dans les fiches : 2017-03 grief 6 (pas de phrase de conclusion propre, classé retenu) et deux coquilles probables du texte ; 2017-02 grief 7 abandonné mais cité dans le récapitulatif de la décision.
- **L'étude reste sur sa période** : `analyse/etude.py` ne compte que les fiches de décisions rendues depuis le 1er janvier 2019 (`DEBUT_ETUDE`). Les chiffres de l'étude n'ont pas bougé (31 décisions) et aucun bandeau « Texte à mettre à jour » n'apparaît. Quand toutes les décisions d'avant 2019 auront leur fiche, il faudra décider d'élargir l'étude (changer la date et reprendre le texte).
- (Mis à jour au lot 8 : voir plus bas.)

## Lot 8 (13 novembre au soir, Opus 5.5, effort max)

Cinq fiches de plus, et corrections du lot 7a. **39 fiches au total.**

| Décision | Établissement | Sanction (demande du Collège) | Griefs retenus / en partie / écartés |
|---|---|---|---|
| 2017-01 | CNP Assurances (bancassurance, deux réseaux bancaires distributeurs) | blâme, 8 M€ (10 M€) | 5 / 9 / 0 |
| 2017-04 | Caisse fédérale de Crédit Mutuel (contrôle centré sur la fédération Méditerranée) | blâme, 1 M€ (3 M€) | 4 / 3 / 1 |
| 2017-07 | Sigue Global Services SAS (transfert d'argent, corridor Chine) | blâme, 100 000 € (90 000 €) | 14 / 2 / 1 |
| 2017-06 | Sigue Global Services Ltd (société sœur britannique, réseau d'agents) | blâme, 60 000 € (60 000 €) | 4 / 2 / 0 |
| 2017-05 | Caisse fédérale du Crédit Mutuel Nord Europe | blâme, 1,5 M€ (3 M€ minimum) | 9 / 1 / 0 |

- **À retenir pour l'étude, le jour où elle sera élargie aux décisions d'avant 2019** : en 2017-07, la Commission prononce **plus** que la demande du Collège (100 000 € contre 90 000 €). La phrase de l'étude « jamais au-dessus de la demande du Collège » ne vaut que pour 2019-2026. En 2017-05, la Commission retient deux griefs que le rapporteur proposait d'écarter.
- **Corrections du lot 7a** : la fiche 2018-01 contenait une addition faite par Claude (« 5,5 millions d'envois pour 1,3 milliard ») ; remplacée par les chiffres officiels. La fiche 2017-01, faite dans ce lot, avait aussi une addition (« 40 alertes ») et un mauvais décompte (« dont 8 en partie » au lieu de 9) : corrigés avant livraison.
- **Nouvelles règles de rédaction** (suite à ces erreurs) : jamais d'arrondi (« près de 68 000 ») ni d'addition dans une fiche ; on reprend le chiffre exact du texte. Le décompte des issues dans « En bref » est vérifié par programme. Les détails personnels sans lien avec le manquement (religion, origine, divorce, profession sans rapport) ne sont pas repris, comme pour la fiche 2019-06.
- **Deux outils ajoutés au dépôt**, à utiliser à chaque lot :
  - `analyse/lire_decision.py ACPR-xxxx-xx` : lecture compacte (en-têtes et citations de lois retirées, faits jamais coupés), environ 10 % de texte en moins ;
  - `analyse/verifier_nombres.py ACPR-xxxx-xx` : cherche chaque nombre de la fiche dans les pages citées, en entier. Il a repéré les arrondis et additions ci-dessus. Les faux signalements connus sont décrits en tête du fichier.
- **Rythme constaté** : 5 fiches par demande avec Opus 5.5 en effort max, plus les vérifications. C'est la longueur de la conversation qui limite, pas l'effort : mieux vaut **une conversation neuve par lot**.
- **Il reste 28 décisions LCB-FT de l'ACPR d'avant 2019** (407 pages), des plus récentes aux plus anciennes : 2017-08, 2016-08, 2016-10, 2016-07, 2016-09, 2016-06, 2016-05, 2016-01, 2016-03, 2015-08, 2015-10, 2015-07, 2015-06, 2014-10, 2014-07, 2014-08, 2015-01, 2013-06, 2014-06, 2012-08, 2013-01, 2012-05, 2012-04, 2011-03, 2011-02, 2011-01, 2010-05, 2010-01. Soit environ **5 à 6 demandes** de 5 fiches. Attention : pour 2016-08, la base indique une publication « à vérifier » et un nom d'établissement qui contient des noms de personnes physiques (à ne pas reprendre).

## Thèmes repérés pendant la session 2

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

## Prochaine étape (après la session 5)

**À faire par Matéo, sans Claude** :
- déposer le .zip de la session 5 (routine ci-dessus), puis vérifier sur le site la Base filtrée sur « AMF » ;
- lundi 16 novembre : vérifier dans l'onglet Actions que la collecte (ACPR et AMF) est verte ;
- relire l'étude (page Analyse), la liste des points de contrôle, puis les fiches, en commençant par les plus citées dans l'étude (2020-05, 2020-03, 2019-06, 2024-06, 2022-07) ;
- éventuellement adapter son texte d'introduction (il ne parle que de l'ACPR) et ajouter le lien LinkedIn à `site/textes/a-propos.txt`.

**Session 6**, dans une nouvelle conversation, au choix :
- les 36 décisions LCB-FT de l'ACPR antérieures à 2019 (par lots de 3, avec Fable 5.2), puis mise à jour du texte de l'étude ;
- ou des fiches AMF, en commençant par les 28 décisions signalées blanchiment (Fable 5.2 ; la grille du point 6 de PROJET.md devra être complétée pour les abus de marché) ;
- ou la collecte de la CSSF puis de la FINMA (Opus 5.5 ou Sonnet 5.5).

Message de reprise : « Lot 9 : lis PROJET.md et JOURNAL.md (pas l'archive), récupère le dépôt, puis fais les 5 fiches ACPR suivantes d'avant 2019 (2017-08, 2016-08, 2016-10, 2016-07, 2016-09), même méthode que le lot 8, avec analyse/lire_decision.py et analyse/verifier_nombres.py. »

Modèle conseillé : Fable 5.2 pour les fiches et pour reprendre le texte de l'étude ; Opus 5.5 ou Sonnet 5.5 pour la collecte et le site.
