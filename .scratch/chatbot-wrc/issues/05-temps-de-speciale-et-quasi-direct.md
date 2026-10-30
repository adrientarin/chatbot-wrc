# 05: Temps de spéciale et quasi-direct

**What to build:** Je demande « Qui a gagné l'ES7 au Portugal ? », « Les temps de la dernière spéciale ? », « Les temps WRC2 de la Power Stage ? ». Le chatbot comprend de quelle spéciale je parle et me donne les temps, les positions et les écarts, avec la fraîcheur de la donnée (« après l'ES7, données de 14h32 »). Pendant une journée de rallye, la donnée ne date pas de plus d'environ une minute au moment de ma question.

Spec : `.scratch/chatbot-wrc/spec.md`.

**Blocked by:** 03 (Résolution des rallyes et engagés)

**Status:** ready-for-agent

- [x] La résolution des spéciales convertit du texte libre en spéciale d'un rallye : numéro (« ES7 », « spéciale 7 »), « la dernière » (la dernière spéciale disputée) et « la Power Stage » ; une spéciale inexistante ou pas encore disputée est signalée.
- [x] L'outil `temps_speciale(rallye, speciale, categorie)` renvoie les temps, les positions et les écarts (au meilleur et au précédent), filtrables par catégorie WRC1 ou WRC2, ainsi que la fraîcheur et l'indicateur de donnée périmée.
- [x] Les données d'un rallye en cours (temps de spéciale) ont une durée de validité d'environ 1 minute pendant une journée de rallye ; les données d'un rallye terminé gardent la durée de 24 heures.
- [x] L'outil est déclaré à l'agent, et le chatbot indique toujours après quelle spéciale et à quelle heure date la donnée.
- [x] Des fixtures JSON réelles des spéciales et des temps d'au moins un rallye terminé, et si possible d'un rallye en cours, sont enregistrées.
- [x] Des tests automatiques, sans réseau, passent par l'outil et couvrent chaque forme de désignation de spéciale, le filtrage par catégorie, la durée de validité courte pendant un rallye en cours et longue pour un rallye terminé (via la fausse horloge), et la spéciale pas encore disputée.
- [x] Démonstration : dans le chat, « Qui a gagné la Power Stage au dernier rallye ? » renvoie le bon équipage.

## Comments

**Points d'entrée** : `events/{id}/stages.json` (spéciales) et `events/{id}/stages/{id}/stagetimes.json?rallyId={id}` (temps). Schéma validé sur Monte-Carlo, la Suède et le Portugal 2026 ; le relevé des 13 rallyes a été abandonné.

**Fixtures** : spéciales du Portugal et de la Sardaigne, temps de l'ES1, ES2, ES7 et de la Power Stage du Portugal, Power Stage de la Sardaigne. Aucun rallye n'est en cours à l'implémentation (dernier rallye fini le 4 octobre 2026, prochain en janvier 2027) : le rallye en cours des tests est simulé à partir des fixtures du Portugal.

**À confirmer au premier rallye suivi** : le quasi-direct n'a jamais été observé. Les statuts d'une spéciale à venir ou en cours sont inconnus (`ToRun` et `Running` des tests sont des hypothèses), comme la réponse de la source pour une spéciale sans temps (liste vide ou 404). Le code ne repose que sur `Completed` et `Interrupted`, et, pour le reste, sur la présence de temps.

**Positions et écarts** : recalculés dans la sélection (catégorie demandée, ou WRC1 et WRC2 avec `toutes`). Ceux de l'API portent sur tout le plateau, donc faux pour un filtre. Un même temps donne une même position.

**Temps non réalisés sur la route** : `Notional` (forfaitaire), `Assessed` (attribué) et `Rally2` (Super Rally) sont signalés par `nature_du_temps`. Sur l'ES7 du Portugal, seuls 10 équipages sur 67 ont un vrai temps : en WRC2, tous ont le même forfait et il n'y a pas de vainqueur sur la route.

**Validité** : les spéciales et les temps sont gardés 1 minute pendant le rallye (dates du calendrier, fuseau local) et 24 heures sinon. Une réponse lue pendant le rallye n'est pas reprise une fois celui-ci terminé, sans quoi une lecture du dimanche passerait pour définitive le lundi (`pas_avant` dans le cache). Le calendrier et les engagés restent à 24 heures et ne comptent pas dans la fraîcheur des temps.

**Connu, non traité** :
- Les spéciales ne se désignent pas par leur nom (« Fafe 2 ») : `speciale_non_resolue` et les candidats, parmi lesquels Claude retrouve le numéro.
- Un rallye fini un dimanche soir après minuit à Paris (fuseau lointain) serait compté comme terminé trop tôt.

**Vérifié pendant l'implémentation** : l'outil contre la vraie API (Power Stage de la Sardaigne : Neuville ; ES7 WRC2 du Portugal ; Monte-Carlo 2027 sans spéciales publiées). Démonstration faite avec le ticket 06, dans l'agent réel : Neuville et Wydaeghe sur la Power Stage de la Sardaigne.
