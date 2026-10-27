# 07: Comportement conversationnel et questions types

**What to build:** Le chatbot se comporte comme le passionné fiable décrit dans la spec, sur l'ensemble des outils. Il recentre gentiment et avec humour les questions hors sujet, raconte de la culture rallye en la présentant comme venant de sa mémoire, ne donne jamais une donnée qu'il n'a pas récupérée, me demande de choisir quand un outil signale une ambiguïté, dit clairement quand une donnée est périmée ou indisponible, enchaîne les questions de suivi grâce à l'historique, et utilise le vocabulaire du glossaire. Une liste de questions types permet de vérifier tout cela à la main avant chaque changement important.

Spec : `.scratch/chatbot-wrc/spec.md`. Vocabulaire : `GLOSSARY.md`.

**Blocked by:** 04 (Résolution des pilotes et fiche pilote), 06 (Classement du rallye)

**Status:** ready-for-agent

- [ ] Le prompt système couvre toutes les règles de comportement de la spec : personnalité, donnée uniquement issue d'un outil, culture rallye signalée, fraîcheur toujours indiquée, donnée périmée ou indisponible dite explicitement, choix parmi les candidats en cas d'ambiguïté, recentrage des questions hors sujet, vocabulaire du glossaire (classement du rallye et classement du championnat, constructeur plutôt qu'écurie, WRC1 et WRC2).
- [ ] Une liste de questions types est versionnée dans le dépôt, avec pour chacune le comportement attendu ; elle couvre au moins chaque outil, une question de suivi, une désignation ambiguë, une question hors sujet, une question de culture rallye, une question à laquelle le chatbot ne doit pas répondre par une donnée inventée (par exemple un temps d'un rallye de 2019), et une source injoignable.
- [ ] Un premier passage complet de la liste est fait, et ses résultats sont notés dans le ticket (section Comments) ; les écarts constatés sont corrigés ou consignés.
