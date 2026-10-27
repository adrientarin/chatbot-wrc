# Spec : Chatbot WRC (version 1)

Status: ready-for-agent

## Problem Statement

En tant que fan de rallye, je dois aujourd'hui jongler entre le site wrc.com, l'application officielle et divers sites de fans pour savoir qui mène un rallye, quel écart sépare deux équipages après une spéciale, où en est le classement du championnat ou quand a lieu le prochain rallye. L'information est dispersée, souvent en anglais, et il n'existe pas d'interlocuteur à qui poser simplement une question (« Et son écart sur le 2e ? ») comme on le ferait à un ami passionné.

## Solution

Un chatbot local, en français, passionné de rallye, à qui je pose des questions en langage naturel sur la saison en cours du WRC (catégories WRC1 et WRC2). Il répond avec des données fiables et récentes tirées de la source utilisée par wrc.com, et précise toujours de quand date la donnée (« après l'ES7, données de 14h32 »). Il peut aussi raconter de la culture rallye de mémoire, en le signalant comme tel, mais ne donne jamais un temps, un écart, des points ou une position qu'il n'a pas récupérés. L'interface est une page de chat dans le navigateur, lancée sur mon PC.

## User Stories

### Conversation et personnalité

1. En tant que fan, je veux poser mes questions en français et en langage naturel, afin de ne pas avoir à apprendre une syntaxe.
2. En tant que fan, je veux que le chatbot me tutoie et parle avec enthousiasme, afin d'avoir l'impression de discuter avec un passionné.
3. En tant que fan, je veux que le chatbot reste factuel et neutre envers les pilotes, afin de pouvoir lui faire confiance.
4. En tant que fan débutant, je veux que le jargon rallye soit expliqué quand c'est utile, afin de comprendre les réponses.
5. En tant que fan, je veux que le chatbot se souvienne de la conversation en cours, afin de pouvoir enchaîner (« Et son écart sur le 2e ? »).
6. En tant que fan, je veux que rien ne soit conservé d'une session à l'autre, afin de repartir d'une conversation propre.
7. En tant que fan, je veux que le chatbot recentre gentiment, avec humour, les questions hors sujet (F1, devoirs de maths), afin qu'il reste un spécialiste du rallye.
8. En tant que fan, je veux que le chatbot me raconte de la culture rallye (histoire, anecdotes) en précisant qu'elle vient de sa mémoire, afin de distinguer le récit des données.
9. En tant que fan, je veux que le chatbot réponde « je ne sais pas » plutôt que d'inventer une donnée, afin de ne jamais être induit en erreur.
10. En tant que fan, je veux lancer le chatbot sur mon PC et lui parler dans mon navigateur, afin de l'utiliser simplement.

### Calendrier

11. En tant que fan, je veux connaître le calendrier de la saison en cours, afin de savoir quand ont lieu les rallyes.
12. En tant que fan, je veux savoir quel est le prochain rallye, afin de m'organiser pour le suivre.
13. En tant que fan, je veux savoir quel rallye est en cours, afin de suivre l'actualité immédiate.
14. En tant que fan, je veux savoir quel était le dernier rallye disputé, afin de retrouver ses résultats.
15. En tant que fan, je veux connaître le statut de chaque rallye (passé, en cours, à venir), afin de situer la saison.
16. En tant que fan, je veux que le calendrier soit présenté tel que la source le publie, sans complément de mémoire, afin qu'il ne contienne pas d'erreurs.
17. En tant que fan, entre la fin d'une saison et le début de la suivante, je veux que « la saison en cours » reste celle qui vient de finir jusqu'à la publication du nouveau calendrier, afin d'obtenir des réponses cohérentes.

### Classement du rallye

18. En tant que fan, je veux connaître le classement du rallye à l'arrivée, afin de savoir qui l'a gagné.
19. En tant que fan, je veux connaître le classement du rallye après une spéciale donnée, afin de revivre son déroulement.
20. En tant que fan, pendant un rallye, je veux le classement du rallye le plus récent possible, afin de suivre l'épreuve presque en direct.
21. En tant que fan, je veux pouvoir filtrer le classement du rallye par catégorie (WRC1 ou WRC2), afin de suivre la catégorie qui m'intéresse.
22. En tant que fan, je veux connaître les écarts entre équipages, au leader et au précédent, afin de mesurer la bagarre.
23. En tant que fan, je veux que les pénalités soient incluses dans le classement du rallye et signalées, afin de comprendre un écart surprenant.
24. En tant que fan, je veux que les équipages repartis sous le règlement Super Rally soient signalés, afin de ne pas confondre leur position avec une performance normale.
25. En tant que fan, je veux connaître la liste des abandons d'un rallye avec la spéciale où chacun s'est produit, afin de savoir qui est sorti et quand.

### Temps de spéciale

26. En tant que fan, je veux connaître les temps sur une spéciale donnée, afin de savoir qui a été le plus rapide.
27. En tant que fan, je veux connaître le vainqueur d'une spéciale, afin de saluer la performance.
28. En tant que fan, je veux connaître les écarts sur une spéciale, afin de mesurer la domination ou la bagarre.
29. En tant que fan, je veux filtrer les temps d'une spéciale par catégorie, afin de suivre WRC2 séparément.
30. En tant que fan, je veux connaître les temps de la Power Stage, afin de savoir qui a pris les points bonus.
31. En tant que fan, je veux désigner une spéciale par son numéro (« l'ES7 ») ou par des mots-clés (« la dernière spéciale », « la Power Stage »), afin de parler naturellement.

### Classement du championnat

32. En tant que fan, je veux connaître le classement du championnat des pilotes WRC1, afin de suivre la course au titre.
33. En tant que fan, je veux connaître le classement du championnat des copilotes, afin de ne pas oublier la moitié de l'équipage.
34. En tant que fan, je veux connaître le classement du championnat des constructeurs WRC1, afin de suivre la bataille des marques.
35. En tant que fan, je veux connaître le classement du championnat des pilotes et des copilotes WRC2, afin de suivre la catégorie inférieure.
36. En tant que fan, je veux connaître les points marqués par un pilote rallye par rallye, afin de comprendre sa saison.
37. En tant que fan, je veux connaître le détail des points d'un rallye (classement du dimanche, classement final, Power Stage, par exemple « 25 + 5 + 4 »), afin de comprendre d'où viennent les points.
38. En tant que fan, je veux connaître l'écart de points entre deux pilotes au classement du championnat, afin d'évaluer la course au titre.

### Engagés et pilotes

39. En tant que fan, je veux connaître la liste des équipages engagés sur un rallye, avec leur voiture et leur catégorie, afin de savoir qui court.
40. En tant que fan, je veux connaître la fiche d'un pilote (nationalité, voiture, constructeur ou équipe, position au classement du championnat), afin d'en savoir plus sur lui.
41. En tant que fan, je veux connaître le copilote d'un pilote, afin de connaître l'équipage complet.
42. En tant que fan, je veux pouvoir compléter la fiche d'un pilote avec de la culture rallye (carrière, titres), présentée comme venant de la mémoire du chatbot, afin d'avoir un portrait plus riche.

### Désignation naturelle

43. En tant que fan, je veux désigner un rallye par son pays, sa ville ou son nom usuel (« le Portugal », « le Monte-Carlo »), afin de ne pas connaître de nom officiel.
44. En tant que fan, je veux désigner un rallye par un repère relatif (« ce week-end », « le dernier », « le prochain »), afin de parler naturellement.
45. En tant que fan, je veux désigner un pilote par son prénom, son nom ou son surnom courant, avec ou sans accents (« Kalle », « Rovanpera »), afin de ne pas avoir à épeler.
46. En tant que fan, quand ma désignation est ambiguë, je veux que le chatbot me propose les candidats possibles, afin de préciser ma demande plutôt que de recevoir une mauvaise réponse.

### Fraîcheur et fiabilité

47. En tant que fan, je veux que chaque donnée soit accompagnée de sa fraîcheur (après quelle spéciale, à quelle heure), afin de savoir si elle est à jour.
48. En tant que fan, pendant un rallye, je veux que les données du rallye ne datent pas de plus d'environ une minute quand je pose ma question, afin de suivre l'épreuve presque en direct.
49. En tant que fan, je veux que les données peu changeantes (calendrier, classement du championnat, engagés) ne soient pas redemandées à la source plus d'une fois par jour, afin de rester discret vis-à-vis de la source.
50. En tant que fan, quand la source est injoignable ou a changé, je veux que le chatbot me donne la dernière donnée connue en précisant qu'elle date, afin d'avoir quand même une réponse honnête.
51. En tant que fan, quand la source est injoignable et qu'aucune donnée n'est connue, je veux que le chatbot me dise qu'il n'a pas la donnée, afin de ne jamais recevoir une donnée inventée.

### Développeur

52. En tant que développeur, je veux que tout l'accès à la source soit isolé derrière un seul module, afin de n'avoir qu'un endroit à réécrire si l'API change ou ferme.
53. En tant que développeur, je veux que la clé de l'API Anthropic soit lue depuis un fichier local non versionné, afin de ne jamais la publier.
54. En tant que développeur, je veux pouvoir tester les outils sans réseau, afin d'avoir des tests rapides et stables.
55. En tant que développeur, je veux une liste de questions types à repasser avant chaque changement important, afin de vérifier le comportement conversationnel.

## Implementation Decisions

### Architecture d'ensemble

- Application Python, lancée en local, avec une interface de chat Streamlit très fine.
- Le modèle de langage est Claude via l'API Anthropic, utilisé en mode « tool use » : le modèle ne reçoit pas les données dans son prompt, il appelle des outils qui les lui renvoient. Le choix précis du modèle (rapport qualité/prix) se fait au moment de l'implémentation, en consultant la documentation à jour.
- La clé API est lue depuis un fichier d'environnement local, exclu du dépôt.
- La mémoire de conversation est l'historique des messages de la session en cours, sans persistance.

### Source de données (voir ADR 0001)

- Source unique : l'API JSON non documentée utilisée par wrc.com, sans authentification. Points d'entrée repérés : liste des saisons, détail d'une saison (calendrier et identifiants des championnats), classement du championnat, détail du championnat (pilotes, nationalités, constructeurs, équipes), spéciales d'un rallye, temps d'une spéciale, résultats cumulés après une spéciale, engagés, vainqueurs de spéciale, pénalités, abandons.
- Seuls les championnats suivants sont utilisés : pilotes WRC1, copilotes WRC1, constructeurs WRC1, pilotes WRC2, copilotes WRC2.

### Modules

1. **Module source WRC** (module profond) : seul module qui connaît l'API et son format JSON. Il expose des objets du domaine (rallye, spéciale, équipage, classements) et masque les identifiants et la structure de l'API. Il dépend de deux adaptateurs injectés :
   - un **transport HTTP** (en production : de vraies requêtes ; en test : des fixtures JSON enregistrées ou une panne simulée) ;
   - une **horloge** (en production : l'heure réelle ; en test : une heure fixée).
2. **Cache** : stocke localement les réponses de la source avec leur heure de récupération. Il est rafraîchi à la demande, sans tâche de fond. Durées de validité :
   - environ 1 minute pour les données d'un rallye en cours (temps de spéciale, classement du rallye, abandons, pénalités) pendant une journée de rallye ;
   - 24 heures pour le reste (calendrier, classement du championnat, engagés, fiches pilotes, rallyes terminés).

   Si la source échoue, le cache renvoie la dernière donnée connue, même périmée, marquée comme telle.
3. **Résolution des désignations** : convertit le texte libre en entités du domaine, de façon déterministe et testable. Elle couvre :
   - pour les rallyes : nom, pays, ville, et les mots-clés « en cours », « dernier », « prochain », « ce week-end » ;
   - pour les spéciales : « ES7 », « dernière », « Power Stage » ;
   - pour les pilotes : prénom, nom, surnom, recherche insensible aux accents et approchée.

   Quand la désignation est ambiguë ou introuvable, elle renvoie la liste des candidats plutôt qu'un choix arbitraire.
4. **Outils** : les six fonctions exposées à Claude. Elles acceptent du texte libre, s'appuient sur la résolution et la source, et renvoient un résultat structuré qui contient toujours les éléments suivants :
   - les données ;
   - la fraîcheur (après quelle spéciale et heure de la donnée) ;
   - un indicateur de donnée périmée ou de source injoignable ;
   - le cas échéant, la liste des candidats en cas d'ambiguïté.
5. **Agent conversationnel** : orchestre la boucle avec Claude (prompt système, déclaration des outils, appel des outils, historique de conversation).
6. **Interface Streamlit** : affiche la conversation et transmet les messages à l'agent.

### Interface des outils

- `calendrier()` : les rallyes de la saison en cours avec leurs dates et leur statut (passé, en cours, à venir).
- `classement_championnat(categorie, type)` : catégorie WRC1 ou WRC2 ; type pilotes, copilotes ou constructeurs (constructeurs en WRC1 seulement). Le résultat inclut les points par rallye et leur détail (dimanche, final, Power Stage).
- `classement_rallye(rallye, apres_speciale, categorie)` : `apres_speciale` est optionnel (par défaut : la dernière spéciale disputée). Le résultat inclut les pénalités, signale les équipages repartis en Super Rally et liste les abandons à part, avec leur spéciale.
- `temps_speciale(rallye, speciale, categorie)` : les temps, les positions et les écarts sur une spéciale.
- `engages(rallye)` : les équipages (pilote, copilote), leur voiture, leur catégorie, leur constructeur ou leur équipe.
- `fiche_pilote(nom)` : nationalité, voiture, constructeur ou équipe, copilote, position au classement du championnat.

### Saison en cours

- La saison en cours est celle de l'année civile. Tant que son calendrier n'est pas publié (début janvier), c'est la saison précédente.
- Elle ne bascule sur la saison suivante qu'une fois **tous ses rallyes passés** et le calendrier de la suivante publié. Un calendrier suivant publié en cours de saison ne fait donc pas basculer.
- Juste après le basculement, le chatbot peut encore répondre sur la saison qui vient de se terminer (par exemple « le dernier rallye »).
- Le calendrier est présenté tel que la source le publie, sans être complété de mémoire.

### Règles de comportement (prompt système)

- Il parle français, tutoie, se montre enthousiaste mais factuel, reste neutre envers les pilotes, et explique le jargon si besoin.
- Il ne donne une donnée (temps, écart, points, position, date) que si elle provient d'un outil. Sinon, il dit qu'il ne sait pas.
- La culture rallye de mémoire est autorisée, toujours présentée comme telle, et jamais utilisée pour donner une donnée.
- Il indique toujours la fraîcheur de la donnée. Si la donnée est périmée ou que la source est injoignable, il le dit explicitement.
- En cas d'ambiguïté signalée par un outil, il demande à l'utilisateur de choisir parmi les candidats.
- Il recentre gentiment, avec humour, les questions hors sujet, sans y répondre sur le fond.
- Il utilise le vocabulaire du glossaire : classement du rallye et classement du championnat, constructeur plutôt qu'écurie, WRC1 et WRC2.

## Testing Decisions

- **Ce qu'est un bon test ici** : il passe par l'interface des outils, comme le ferait Claude, et vérifie uniquement le résultat observable (données renvoyées, fraîcheur, indicateurs, candidats). Il ne teste ni les fonctions internes, ni la structure du cache, ni le format de l'API.
- **Une seule couture automatisée : les six outils.** Les tests y injectent :
  - un faux transport HTTP qui sert des fixtures JSON réelles, enregistrées une fois depuis l'API (au moins un rallye terminé complet, un rallye en cours de déroulement, la saison et les championnats), ou qui simule une panne ou un format inattendu ;
  - une fausse horloge, pour placer le test pendant un rallye, entre deux rallyes ou entre deux saisons, et pour faire vieillir le cache.
- **Comportements couverts par ces tests :**
  - résolution des désignations, y compris l'ambiguïté et les mots-clés relatifs ;
  - classement du rallye, avec les pénalités, le Super Rally et les abandons ;
  - temps de spéciale et classement du championnat, avec le détail des points ;
  - durées de validité du cache et rafraîchissement à la demande ;
  - repli sur la donnée périmée et absence de donnée en cas de panne ;
  - basculement de saison.
- **Non testé automatiquement :**
  - l'agent conversationnel (personnalité, choix des outils, recentrage hors sujet, respect de la règle « pas de donnée inventée ») : il est vérifié par une liste de questions types repassée à la main avant chaque changement important ;
  - l'interface Streamlit, trop fine pour justifier des tests.
- **Prior art** : aucun, le dépôt ne contient pas encore de code. Ces tests établiront le modèle.

## Out of Scope

- Historique précis avant la saison 2026 (seule la culture rallye de mémoire est possible).
- Temps intermédiaires (« splits ») en cours de spéciale.
- Catégories WRC2 Challenger, WRC3, Junior et Masters.
- Championnat des équipes.
- Shakedown.
- Source complémentaire pour les pilotes (Wikipédia ou autre).
- Hébergement en ligne et accès multi-utilisateurs.
- Bot Discord ou Telegram.
- Persistance des conversations entre les sessions.

## Further Notes

- La source n'est ni documentée ni licenciée (ADR 0001). Elle peut changer ou exiger une clé sans prévenir : un outil de fans qui l'utilise a récemment ajouté la gestion d'une clé API. L'isolation dans le module source WRC et le repli sur la donnée périmée sont les protections prévues. L'usage reste personnel et non commercial.
- Le quasi-direct n'a pas pu être vérifié pendant un rallye en cours. Il faudra le confirmer lors du premier rallye suivant la mise en service. Si les données n'arrivent qu'en fin de journée, la durée de validité courte reste inoffensive.
- La source ne listait que 13 rallyes pour 2026 au moment de la recherche. Le chatbot doit présenter ce qu'elle publie, sans le compléter de mémoire.
- Le projet RallyDataJunkie (wrc-shinylive) est une bonne référence pour découvrir les points d'entrée de l'API, mais il ne doit pas devenir une dépendance.
