# 07: Comportement conversationnel et questions types

**What to build:** Le chatbot se comporte comme le passionné fiable décrit dans la spec, sur l'ensemble des outils. Il recentre gentiment et avec humour les questions hors sujet, raconte de la culture rallye en la présentant comme venant de sa mémoire, ne donne jamais une donnée qu'il n'a pas récupérée, me demande de choisir quand un outil signale une ambiguïté, dit clairement quand une donnée est périmée ou indisponible, enchaîne les questions de suivi grâce à l'historique, et utilise le vocabulaire du glossaire. Une liste de questions types permet de vérifier tout cela à la main avant chaque changement important.

Spec : `.scratch/chatbot-wrc/spec.md`. Vocabulaire : `GLOSSARY.md`.

**Blocked by:** 04 (Résolution des pilotes et fiche pilote), 06 (Classement du rallye)

**Status:** ready-for-agent

- [x] Le prompt système couvre toutes les règles de comportement de la spec : personnalité, donnée uniquement issue d'un outil, culture rallye signalée, fraîcheur toujours indiquée, donnée périmée ou indisponible dite explicitement, choix parmi les candidats en cas d'ambiguïté, recentrage des questions hors sujet, vocabulaire du glossaire (classement du rallye et classement du championnat, constructeur plutôt qu'écurie, WRC1 et WRC2).
- [x] Une liste de questions types est versionnée dans le dépôt, avec pour chacune le comportement attendu ; elle couvre au moins chaque outil, une question de suivi, une désignation ambiguë, une question hors sujet, une question de culture rallye, une question à laquelle le chatbot ne doit pas répondre par une donnée inventée (par exemple un temps d'un rallye de 2019), et une source injoignable.
- [x] Un premier passage complet de la liste est fait, et ses résultats sont notés dans le ticket (section Comments) ; les écarts constatés sont corrigés ou consignés.

## Comments

**Liste** : `docs/questions-types.md` (38 questions ; la 38 a été ajoutée après ce passage).

**Passage du 30 octobre 2026** : dans l'agent réel (hors Streamlit), avec la vraie API et `claude-opus-5-5`, sur une copie du cache. Les questions 1 à 35 sont passées avec la première version du prompt modifié. Leurs chiffres ont été comparés aux résultats bruts des outils pour les questions 4, 5, 8 à 13, 15 et 20 à 22.

- **Conformes** : 1 à 12, 18 à 21, 23 à 34. Notamment : fraîcheur indiquée à chaque donnée, classement final 2026 présenté comme tel, suivi sans redite, Rossel non choisi, hors sujet recentré sans réponse (la solution de l'équation n'est pas donnée), culture signalée, rien d'inventé sur 2019, WRC3 ou les temps intermédiaires, aucun pronostic.
- **Q14** : réponse juste, mais la liste des spéciales est regroupée selon des critères absents de l'outil (« Jeudi », « Région d'Arganil »).
- **Q16** : « la liste sera sûrement publiée » : petite supposition.
- **Q13** : écart. Sélection « Les Français » faite de mémoire : `temps_speciale` ne donne pas la nationalité.
- **Q15** : trois écarts. « Moteur hybride » pour les Rally1 dit de mémoire sans le signaler, et à vérifier ; regroupements « Les Français », « Les Portugais » et « semi-officielles » absents de l'outil ; 43 équipages WRC2 annoncés pour 42 renvoyés.
- **Q17 et Q35** : « 8 titres » pour Ogier, signalé comme de la mémoire. Je le crois dépassé (9 titres, à vérifier) : la culture rallye peut être fausse sur les années récentes.
- **Q22** : réponse juste, mais déduite du classement précédent, sans rappeler l'outil avec WRC2.
- **Q35** : « pour l'instant » et « cette saison » sur une saison terminée.

**Corrections du prompt après ce passage, pas encore revérifiées** : rappeler l'outil quand un suivi change de rallye, de spéciale ou de catégorie ; annoncer comme venant de la mémoire tout ce qui n'est pas dans un résultat, sans regrouper selon un critère absent ; nommer la saison terminée ; prudence sur la mémoire des dernières années. Le ticket 06 notait déjà les suppositions glissées dans les réponses : le prompt les interdit maintenant. Après la revue de code, le prompt a aussi changé sur les candidats (ambigu ou introuvable traités à part), les commentaires de mémoire (ni donnée, ni jargon), le palmarès ancien et `donnee_disponible` faux.

**Reste à faire** : le crédit de l'API Anthropic a été épuisé juste après ces 35 questions (`credit balance is too low`), avant toute réponse du second passage. Il faudra :
1. repasser les questions 13 à 17, 19, 22, 25, 28 à 35 avec le prompt corrigé ;
2. passer les questions 36 à 38 : jamais posées au modèle, et la 38 dans le chat Streamlit.

**Source injoignable, vérifié sans le modèle** : avec la procédure de la liste (proxy, `NO_PROXY=api.anthropic.com`), `calendrier` et `classement_rallye` renvoient `donnee_perimee: true` sur le cache vieilli, et `donnee_disponible: false` sur un cache vide. L'API Anthropic répond bien avec ce proxy (c'est elle qui a renvoyé le refus de crédit).

**Consignés, non corrigés** :
- Une erreur de l'API Anthropic (crédit, réseau) n'est pas interceptée par `Agent.repondre` : Streamlit afficherait une trace d'exception. Hors du périmètre de ce ticket.
- Le glossaire déconseille « équipe », alors que la spec et les outils s'en servent à côté de « constructeur » (engagés, fiche pilote) : à arbitrer avec le glossaire, qui dit aussi « après une étape » en déconseillant « étape ».
- Le nombre d'équipages n'est pas fourni par `engages` : le modèle le compte lui-même et peut se tromper (Q15).
- **À vérifier** : le chatbot dit Evans champion 2026 et la saison terminée, car la source ne publie que 13 rallyes pour 2026 et a publié 2027. De mémoire, le calendrier 2026 comptait aussi un rallye d'Arabie saoudite en novembre : si la source en a seulement omis la publication, « classement final » et « champion » sont faux, alors que le comportement suit la spec (présenter ce que la source publie).

**Changement de modèle** : le modèle par défaut passe à `claude-haiku-5-5` (0,10 $ / 0,50 $ par million de jetons jusqu'à 100 000 jetons de prompt, 0,50 $ / 2,50 $ au-delà, contre 4 $ / 20 $ pour Opus 5.5) pour réduire le coût. Ce modèle n'a pas de rattrapage des refus côté serveur : `fallbacks` et son beta sont retirés, un refus donne `REPONSE_REFUS`. L'effort passe de `low` à `medium`, car à `low` la documentation signale des appels d'outils sautés avec un long prompt.

**Passage complet sur Haiku** : les 38 questions, dans l'agent réel (hors Streamlit), avec la vraie API, l'effort `medium` et le prompt corrigé, sur une copie du cache. Questions 36 et 37 avec la procédure de panne ; question 38 dans une conversation neuve, sans passer par le chat. Coût : environ 0,12 $ (1,04 million de jetons en entrée, 28 000 en sortie, sans cache de prompt) ; plus gros prompt : 76 000 jetons, sous le seuil des 100 000. Les chiffres ont été comparés aux résultats bruts des outils pour les questions 4, 5, 8 à 13, 15 et 20 à 22 : tous exacts, sauf Q4.

- **Tiennent bien** : aucune donnée de saison ou d'une autre année inventée sur 2019, WRC3, les temps intermédiaires ou le pronostic (30 à 34) ; Rossel non choisi (23) ; hors sujet recentré sans répondre (26, 27) ; panne dite explicitement, et rien de mémoire sans donnée (36, 37) ; rien de conservé entre deux conversations (38) ; fraîcheur partout.
- **Corrections du prompt confirmées** : Q22 rappelle l'outil avec WRC2 ; Q13 et Q15 ne regroupent plus par nationalité et ne font plus d'ajout technique ; Q15 compte bien 42 équipages WRC2 ; Q35 nomme la saison 2026.
- **Q4, écart grave** : « Evans a fini sur le podium de 12 des 13 rallyes » est faux (6 d'après l'outil), et présenté comme un fait. Haiku s'est corrigé de lui-même en Q5, avec les 6 bons rallyes. Un décompte fait par le modèle n'est donc pas fiable. Dans le même message : « la saison 2027 vient de démarrer », faux.
- **Q18** : correction spontanée d'une réponse précédente qui n'en avait pas besoin.
- **Vocabulaire** : « au général » (Q10), « classement général » (Q22), « manche » (Q25), « course » (Q29), malgré le prompt.
- **Noms mal recopiés** : Domża{ł}a (Q10), Marúo (Q11), Dapràa (Q15) ; « sa copilote » supposé pour Janni Hussi (Q22).
- **Listes incomplètes** : pénalités de Q11 absentes (hors du top affiché) ; copilotes WRC2 absents de Q15.
- **Mémoire** : Ogier « sur Toyota » en 2019 (Q31, faux à ma connaissance : Citroën) ; « huit titres » (Q17, sans doute dépassé) ; Super Rally mal expliqué, « plus classé comme un équipage normal » (Q29), alors que le glossaire parle d'un retour avec pénalité. Tout est annoncé comme venant de la mémoire.
- **Ton** : tutoiement respecté, mais nettement moins d'enthousiasme et d'humour qu'avec Opus (spec, user story 2).
- **Fuite de vocabulaire interne** : « pas de nature de temps particulière » (Q12).
- **Q36** : filtre sur WRC1 sans qu'on le demande, et doute à tort du caractère définitif du classement du rallye à cause de la spéciale interrompue.

Ces écarts sont consignés, pas corrigés : le prompt n'a pas changé après ce passage.

**Revue de code du commit `a5cb62c` (30 octobre 2026)** :

- **Historique rétabli** : l'en-tête du passage sur Opus et le « Reste à faire » avaient été réécrits ; ils reviennent tels quels, et la case du passage complet est décochée. Le passage sur Haiku date aussi du 30 octobre.
- **« Reste à faire »** : le passage sur Haiku couvre le point 1 et les questions 36 et 37. Il manque la question 38 dans le chat Streamlit : une conversation neuve dans l'agent ne teste pas le rechargement de la page. Tout le passage sur Haiku s'est fait hors du chat, alors que la liste demande le chat.
- **Rattrapage des refus** : `fallbacks` et son beta reviennent pour Fable 5.1, Opus 5.5, Opus 5 et Sonnet 5.5 ; seul Haiku reste sans rattrapage, avec `REPONSE_REFUS`.
- **Effort** : la documentation ne constate pas d'appels sautés. Elle prévient qu'à `low`, avec un long prompt, le modèle risque davantage de sauter une recherche, et elle conseille `low` pour le chat. `medium` reste le défaut de Haiku, mais aucun essai à `low` n'a été mesuré.
- **Choix du modèle** : seul Haiku a été évalué, pas Sonnet 5.5 (2 $ / 10 $ par million de jetons). Le rapport qualité/prix demandé par la spec reste à arbitrer.
- **Prompt corrigé, pas encore revérifié** : décomptes absents de l'outil, démarrage d'une saison, pénalités hors des équipages cités, « au général » et « course », enthousiasme. À repasser : questions 4, 5, 10, 11, 22, 25 et 29.

**Question 38 (30 octobre 2026)** : validée à la main dans le chat Streamlit. Le passage complet est donc terminé, et sa case est cochée.

**Revérification du prompt corrigé (30 octobre 2026)** : questions 4, 5, 10, 11, 20 à 22, 25 et 29 sur `claude-haiku-5-5`, une seule fois chacune, dans l'agent réel (hors Streamlit), sur une copie du cache. Coût : environ 0,03 $. Les chiffres ont été comparés aux résultats bruts des outils pour 4, 5, 10, 11 et 20 à 22 : positions, temps, écarts, points, abandons, pénalités et Super Rally sont exacts.

- **Corrigés sur ce passage** : plus de décompte inventé ni de « saison 2027 démarrée » (Q4) ; pénalités de Q11 présentes, hors du top affiché ; plus de « au général » (Q10), de « classement général » (Q22) ni de « manche » (Q25) ; noms de Q11 bien recopiés.
- **Q10, nouvel écart** : « neuf équipages […] tous en WRC2 » est faux, car Sordo est en WRC1 (8 WRC2, 1 WRC1), et la même liste le dit. Un décompte reste donc possible malgré la règle.
- **Q4, nouvel écart** : « le championnat ne compte que des rallyes où le pilote a marqué des points » est absent de l'outil et présenté comme un fait.
- **Q21** : « cet écart vaut dans les deux catégories » est faux, car les deux pilotes sont en WRC1.
- **Vocabulaire encore présent** : « épreuve » (Q4), « course » (Q11, Q29).
- **Nom encore mal recopié** : Domżała (Q10).
- **Q29** : la pénalité du Super Rally n'est pas mentionnée, et « est repartis » est une faute.
- **Ton** : toujours sobre, sans gain net d'enthousiasme.
