# 06: Classement du rallye

**What to build:** Je demande « Qui mène au Portugal ? », « Le classement après l'ES12 ? », « Qui a gagné le Monte-Carlo en WRC2 ? » ou « Qui a abandonné ? ». Le chatbot donne le classement du rallye à l'instant demandé (après une spéciale, ou à l'arrivée), avec les écarts au leader et au précédent. Il signale les pénalités incluses et les équipages repartis en Super Rally, et liste les abandons à part, avec la spéciale où ils se sont produits.

Spec : `.scratch/chatbot-wrc/spec.md`.

**Blocked by:** 05 (Temps de spéciale et quasi-direct)

**Status:** ready-for-agent

- [x] L'outil `classement_rallye(rallye, apres_speciale, categorie)` renvoie le classement du rallye après la spéciale demandée, ou après la dernière spéciale disputée si aucune n'est précisée, filtrable par catégorie WRC1 ou WRC2.
- [x] Chaque position contient le temps cumulé, l'écart au leader et au précédent ; les pénalités sont incluses dans le cumul et signalées avec leur durée.
- [x] Les équipages repartis sous le règlement Super Rally sont signalés comme tels.
- [x] Les abandons sont listés à part, chacun avec la spéciale où il s'est produit.
- [x] Le résultat contient la fraîcheur (après quelle spéciale, heure de la donnée) et l'indicateur de donnée périmée ; la durée de validité courte s'applique pendant un rallye en cours, comme pour le ticket 05.
- [x] L'outil est déclaré à l'agent.
- [x] Des fixtures JSON réelles des résultats cumulés, des pénalités et des abandons d'au moins un rallye, idéalement avec un cas de Super Rally, sont enregistrées.
- [x] Des tests automatiques, sans réseau, passent par l'outil et couvrent le classement après une spéciale donnée et à l'arrivée, le filtrage par catégorie, une pénalité, un Super Rally et un abandon.
- [x] Démonstration : dans le chat, « Qui a gagné le dernier rallye, et qui a abandonné ? » renvoie le vainqueur et les abandons.

## Comments

**Points d'entrée** : `events/{id}/stages/{id}/results.json?rallyId={id}` (cumul après une spéciale), `events/{id}/retirements.json` (abandons) et `events/{id}/itineraries/{id}.json` (tous les contrôles, dans l'ordre ; l'identifiant vient de l'événement). `rallies/{id}/results.json` vaut les résultats de la dernière spéciale : inutile. Schéma validé sur le Portugal et la Sardaigne, à chaque spéciale.

**Pénalités** : `penaltyTimeMs` du cumul suffit (cumulé, déjà inclus, juste à chaque spéciale). `penalties.json` existe mais n'est pas lu : il n'apporterait que le motif, pas demandé. Les fixtures de pénalités sont donc celles des résultats cumulés.

**Abandons et Super Rally** : l'état d'un équipage se lit dans la chronologie des abandons, pas dans les résultats. Ceux d'une spéciale passée sont réécrits après coup : un équipage reparti plus tard y a un cumul même pour une spéciale où il était à l'arrêt.
- À l'arrêt après la spéciale : dans `abandons`, hors du classement du rallye. C'est aussi le cas d'un équipage qui a fini la spéciale et s'arrête juste après (les 8 du vendredi soir au Portugal sont donc rattachés à l'ES10 et ne sont plus classés après l'ES10, alors que la source les y garde).
- Une ligne `Rejoined` se note toujours sur un contrôle de fin d'étape (vérifié sur tout le Portugal et la Sardaigne) : le retour prend effet à la spéciale suivante.
- La spéciale et le motif sont ceux du début de l'arrêt : un `Temporary` à SF3 devenu `Permanent` à TC7D reste un abandon à l'ES3.
- Un contrôle hors spéciale se rattache à la spéciale qui le précède.
- Sur la dernière spéciale disputée, toutes les lignes comptent, y compris un abandon au contrôle de la spéciale suivante.

**Positions** : recalculées dans la sélection, comme au ticket 05. Avec `toutes`, les autres catégories sont retirées : les positions diffèrent de l'officiel dès qu'un équipage non suivi est intercalé (Daprà 25e contre 27e au Portugal). Le prompt demande de ne pas les présenter comme officielles.

**À confirmer au premier rallye suivi** (rien n'est en cours à l'implémentation ; le rallye en cours des tests est simulé) :
- la réponse de `retirements.json` tant qu'il n'y a aucun abandon : si c'est un 404 plutôt qu'une liste vide, le classement du rallye sera indisponible jusqu'au premier abandon ;
- la publication des résultats pendant qu'une spéciale se court : le classement s'arrête à la dernière spéciale `Completed` ou `Interrupted`.

**Connu, non traité** :
- Le motif est celui de la source, en anglais et brut : `CPR` n'est pas expliqué (les 7 équipages concernés s'arrêtent tous le vendredi soir au Portugal), et la source publie `MNECHANICAL`.
- Les non-partants et les cas de force majeure n'ont pas de ligne d'abandon : ils ne sont ni classés ni dans `abandons`.
- `peut_repartir` reste vrai jusqu'à la fin de la date de fin du rallye, donc le dimanche soir.
- Depuis le basculement sur 2027, « le Monte-Carlo » désigne le rallye 2027 à venir, comme le veut la spec ; le prompt fait rappeler l'outil avec l'année (« Monte-Carlo 2026 »).

**Démonstration** : faite dans l'agent réel (hors Streamlit), avec la clé et la vraie API. « Qui a gagné le dernier rallye, et qui a abandonné ? » donne Oliver Solberg en Sardaigne et les 9 abandons. « Qui a gagné le Monte-Carlo en WRC2 ? » donne Léo Rossel via le Monte-Carlo 2026.

**`apres_speciale` obligatoire pour Claude** : la spec le veut optionnel, et l'outil Python le reste (sans lui, la dernière spéciale disputée). Mais déclaré facultatif dans le schéma, Claude l'omettait à chaque fois, même pour « après l'ES7 », et recevait le classement à l'arrivée. Il est donc requis dans le schéma, comme `speciale` dans `temps_speciale`, avec « la dernière » par défaut.

Note pour le ticket 07 : les réponses de l'agent glissent parfois une supposition non issue d'un outil (« il n'avait sans doute pas besoin de prendre de risques »).
