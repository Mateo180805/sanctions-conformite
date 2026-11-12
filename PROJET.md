# PROJET – Sanctions Conformité

Cahier des charges du projet. Version du 12 novembre 2026 (session 1).
Ce fichier est à redonner à Claude au début de chaque session, avec JOURNAL.md.

## 1. Qui je suis

Je m'appelle Matéo Bonnesoeur. Je suis en M1 du master « Gestion d'actifs, contrôle des risques et conformité » à l'IAE de Caen. Je vise un métier en conformité, surtout dans la lutte contre la criminalité financière : LCB-FT, sanctions internationales et gel des avoirs, abus de marché. Je vise de grandes banques, à Paris, au Luxembourg ou en Suisse, et je cherche un stage en conformité, contrôle interne ou LCB-FT.

Je ne suis pas développeur. Chaque manipulation technique doit m'être expliquée pas à pas, comme à un débutant, en me disant toujours où cliquer. Je travaille dans l'application Claude, sur mon ordinateur.

## 2. Pourquoi ce projet

En cours, on apprend les règles, mais on voit rarement ce qui se passe quand un dispositif de conformité échoue. Les décisions de sanction des régulateurs montrent exactement ce qu'ils reprochent aux établissements. Je veux donc une base qui récupère ces décisions automatiquement, que je lis au fur et à mesure, et une analyse qui en tire des leçons.

Mes trois objectifs :
- apprendre le métier à partir de cas réels ;
- avoir un projet concret à montrer en entretien. On me demandera « pourquoi avez-vous fait ça ? » et « comment ça marche ? » : je dois pouvoir tout expliquer simplement, y compris la partie technique ;
- préparer chaque entretien en sachant ce qu'on a reproché à la banque en face.

## 3. Ce que je veux construire

a) Une base des décisions de sanction des régulateurs des pays où je veux travailler. On commence par l'ACPR (Commission des sanctions). Plus tard, dans d'autres sessions : l'AMF (Commission des sanctions), la CSSF au Luxembourg et la FINMA en Suisse. Tout est conçu dès le départ pour pouvoir ajouter ces régulateurs facilement.

b) Une mise à jour automatique : chaque semaine, la base vérifie s'il y a de nouvelles décisions et les ajoute, sans que j'aie besoin d'ouvrir Claude.

c) Une analyse : chaque décision est résumée dans une fiche, avec la même grille pour toutes (point 6).

d) Une étude comparative (ce qui est sanctionné, à quelle fréquence, avec quelles sanctions) et une liste des points de contrôle les plus sanctionnés, comme celles qu'utilise un service de contrôle interne. Ce sera pour la session 4.

e) Un site public, sobre et facile à comprendre, dont je mettrai le lien sur mon CV et sur LinkedIn.

## 4. Contraintes techniques

- Tout doit être gratuit. Le projet vit dans un dépôt GitHub public. La mise à jour tourne avec GitHub Actions (gratuit pour un dépôt public) chaque semaine, avec aussi un bouton pour la lancer à la main. Le site est hébergé avec GitHub Pages.
- Pas de base de données à installer : des fichiers simples (JSON, CSV, texte) dans le dépôt. Il reste léger (le texte extrait et le lien officiel plutôt que tous les PDF), pour pouvoir être transmis en .zip lors des sessions suivantes.
- Pas d'API payante. Les nouvelles décisions arrivent avec le statut « à lire » ; c'est moi qui les lis et qui valide leur fiche. La documentation note comment on pourrait ajouter des résumés automatiques plus tard, sans le mettre en place.
- Code simple, en Python pour la collecte, commenté en français. Je dois pouvoir expliquer en entretien comment il marche.
- Collecte respectueuse : peu de requêtes, une pause entre deux téléchargements, un identifiant clair, et seulement ce qui est nouveau.
- Si la collecte échoue (site modifié, accès bloqué), le programme s'arrête avec un message clair pour que GitHub me prévienne. Aucune erreur silencieuse.
- GitHub peut désactiver les tâches programmées d'un dépôt public resté longtemps sans activité : cette règle est vérifiée et une parade est prévue (voir JOURNAL.md).
- Si GitHub ne peut pas accéder au site d'un régulateur, il y a un plan B (lancer la collecte depuis mon ordinateur).
- Si un autre outil serait nettement plus simple pour une étape (Claude Code par exemple), Claude me le dit et explique pourquoi. Sinon, on reste dans l'application Claude.

## 5. Ce que je sais des sources

- ACPR : les décisions de la Commission des sanctions sont publiées au registre officiel de l'ACPR, sous forme nominative ou anonymisée. Sur le site, elles sont listées dans le « Recueil des sanctions » : https://acpr.banque-france.fr/fr/reglementation/recueil-des-sanctions (l'ancienne adresse anglaise /en/node/33459 n'est plus accessible).
- Les PDF des décisions ont des adresses de formats très différents : on part des pages de liste, on ne devine pas les adresses.
- Une même décision peut avoir été publiée d'abord avec le nom de l'établissement, puis anonymisée plus tard (fichiers « ..._anonymisee.pdf »). Le numéro de procédure (par exemple « procédure n° 2022-01 »), précédé du nom du régulateur, sert d'identifiant unique pour éviter les doublons.
- L'en-tête d'une décision donne souvent la sanction (par exemple « Blâme et sanction pécuniaire d'un million d'euros ») et les dates d'audience et de décision.
- Pour plus tard : la CSSF publie en général ses sanctions LBC/FT, sous forme nominative ou anonyme. La FINMA publie des résumés anonymisés de ses procédures dans une base en ligne, et ordonne surtout des mesures plutôt que des amendes.

## 6. La grille d'analyse (une fiche par décision)

**Identité**
- régulateur, numéro de procédure, date de la décision, lien vers le PDF officiel ;
- établissement (ou « anonymisé »), type d'établissement (banque, établissement de paiement ou de monnaie électronique, assureur, changeur manuel, intermédiaire, société de gestion…), groupe et pays si la décision les mentionne.

**Sanction**
- nature (avertissement, blâme, interdiction…), montant en euros, publication nominative ou anonyme.

**Manquements**
- la liste des griefs, chacun résumé en une ou deux phrases, avec les textes visés et les chiffres clés (nombre de dossiers, montants, durée) ;
- pour chaque grief : retenu ou écarté ;
- chaque grief classé dans une catégorie commune : classification des risques ; connaissance du client à l'entrée en relation ; vigilance constante et mise à jour des dossiers ; personnes politiquement exposées et vigilance renforcée ; dispositif de surveillance des opérations (outils, scénarios, seuils) ; analyse des alertes et examen renforcé ; déclarations de soupçon à Tracfin ; gel des avoirs et sanctions financières ; procédures et contrôle interne ; gouvernance, moyens et formation ; dispositif de groupe, filiales et correspondance bancaire ; autre (à préciser).

**Contexte**
- circonstances aggravantes ou atténuantes, mesures correctrices prises par l'établissement ;
- cause profonde, seulement si la décision l'explique ;
- « ce qui aurait dû être fait » : les points de contrôle qu'on peut en tirer, marqués comme déduits.

**Pour moi**
- les pages à lire en priorité ;
- le niveau de confiance de Claude et les points que je dois vérifier ;
- un statut (« à lire » ou « lue ») et un champ « mes notes » que je remplirai.

Les décisions qui ne portent ni sur la LCB-FT ni sur le gel des avoirs (protection de la clientèle, prudentiel…) ont une fiche courte avec la mention « hors LCB-FT ».

## 7. Règles de qualité

- Ne jamais rien inventer. Chaque information vient du texte de la décision, avec la page. Si elle n'y est pas : « non précisé ».
- Toujours séparer ce que dit la décision de ce qui en est déduit.
- Ne jamais chercher à retrouver l'identité d'un établissement ou d'une personne dans une décision anonymisée. Sur le site, ne mettre en avant aucun nom de personne physique.
- Avant de traiter un lot, tester la méthode sur quelques décisions et me montrer le résultat.
- Signaler les doutes au lieu de les cacher.
- Le site cite toujours la source officielle et a une page « Méthode » qui dit honnêtement que la collecte et la première analyse ont été faites avec Claude (Fable), puis relues par moi.

## 8. Le site

Il s'adresse à des recruteurs en conformité, et à moi.

Pages : Accueil (ce que c'est en deux phrases, quelques chiffres, les dernières décisions) ; Base (un tableau avec recherche et filtres : régulateur, année, type d'établissement, catégorie de manquement, montant) ; une fiche par décision ; Analyse (l'étude et ses graphiques) ; Méthode (sources, grille, mise à jour, limites, usage de l'IA) ; À propos (qui je suis, pourquoi ce projet, lien LinkedIn).

Style : sobre et éditorial, comme une base juridique ou un site de journalisme de données. Fond clair, texte foncé, une seule couleur d'accent, typographie très lisible, tableaux aérés, graphiques simples. Pas d'emoji, pas de dégradés, pas d'effets à la mode, pas d'icônes décoratives, pas de phrases de marketing. Il doit être agréable sur téléphone, rapide et accessible, et surtout ne pas avoir l'air généré par une IA.

Textes : courts et factuels. Des emplacements clairement marqués sont laissés pour les textes que j'écrirai moi-même (introduction, À propos).

## 9. Organisation du travail

- On avance en sessions, une conversation par session.
- Deux fichiers sont tenus dans le dépôt : PROJET.md (ce cahier des charges, mis à jour si on change quelque chose) et JOURNAL.md (ce qui est fait, les choix, les problèmes, la prochaine étape). À la fin de chaque session, Claude met JOURNAL.md à jour et me le donne. Au début de chaque session, je redonne les deux.
- À chaque étape : Claude explique en deux ou trois phrases simples ce qu'il fait et pourquoi (pour que je puisse l'expliquer en entretien), me donne les manipulations exactes, puis attend mon retour avant de continuer.
- Des fichiers complets, prêts à déposer, jamais des morceaux à recoller.
- Mes limites d'utilisation sont serrées : être efficace, ne pas réécrire un fichier entier pour une petite modification, et me prévenir avant une étape très longue.

## 10. Plan des sessions

1. Lancer le projet et récupérer les décisions de l'ACPR.
2. Fiches d'analyse des décisions de l'ACPR (grille du point 6), en commençant par un essai sur quelques décisions.
3. Le site (GitHub Pages).
4. Étude comparative et liste des points de contrôle.
5. Et suivantes : AMF, CSSF, FINMA.

L'ordre des sessions 2 à 5 peut changer ; le noter ici si c'est le cas.
