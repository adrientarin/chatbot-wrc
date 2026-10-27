# 05: Temps de spéciale et quasi-direct

**What to build:** Je demande « Qui a gagné l'ES7 au Portugal ? », « Les temps de la dernière spéciale ? », « Les temps WRC2 de la Power Stage ? ». Le chatbot comprend de quelle spéciale je parle et me donne les temps, les positions et les écarts, avec la fraîcheur de la donnée (« après l'ES7, données de 14h32 »). Pendant une journée de rallye, la donnée ne date pas de plus d'environ une minute au moment de ma question.

Spec : `.scratch/chatbot-wrc/spec.md`.

**Blocked by:** 03 (Résolution des rallyes et engagés)

**Status:** ready-for-agent

- [ ] La résolution des spéciales convertit du texte libre en spéciale d'un rallye : numéro (« ES7 », « spéciale 7 »), « la dernière » (la dernière spéciale disputée) et « la Power Stage » ; une spéciale inexistante ou pas encore disputée est signalée.
- [ ] L'outil `temps_speciale(rallye, speciale, categorie)` renvoie les temps, les positions et les écarts (au meilleur et au précédent), filtrables par catégorie WRC1 ou WRC2, ainsi que la fraîcheur et l'indicateur de donnée périmée.
- [ ] Les données d'un rallye en cours (temps de spéciale) ont une durée de validité d'environ 1 minute pendant une journée de rallye ; les données d'un rallye terminé gardent la durée de 24 heures.
- [ ] L'outil est déclaré à l'agent, et le chatbot indique toujours après quelle spéciale et à quelle heure date la donnée.
- [ ] Des fixtures JSON réelles des spéciales et des temps d'au moins un rallye terminé, et si possible d'un rallye en cours, sont enregistrées.
- [ ] Des tests automatiques, sans réseau, passent par l'outil et couvrent chaque forme de désignation de spéciale, le filtrage par catégorie, la durée de validité courte pendant un rallye en cours et longue pour un rallye terminé (via la fausse horloge), et la spéciale pas encore disputée.
- [ ] Démonstration : dans le chat, « Qui a gagné la Power Stage au dernier rallye ? » renvoie le bon équipage.
