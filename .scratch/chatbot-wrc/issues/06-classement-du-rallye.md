# 06: Classement du rallye

**What to build:** Je demande « Qui mène au Portugal ? », « Le classement après l'ES12 ? », « Qui a gagné le Monte-Carlo en WRC2 ? » ou « Qui a abandonné ? ». Le chatbot donne le classement du rallye à l'instant demandé (après une spéciale, ou à l'arrivée), avec les écarts au leader et au précédent. Il signale les pénalités incluses et les équipages repartis en Super Rally, et liste les abandons à part, avec la spéciale où ils se sont produits.

Spec : `.scratch/chatbot-wrc/spec.md`.

**Blocked by:** 05 (Temps de spéciale et quasi-direct)

**Status:** ready-for-agent

- [ ] L'outil `classement_rallye(rallye, apres_speciale, categorie)` renvoie le classement du rallye après la spéciale demandée, ou après la dernière spéciale disputée si aucune n'est précisée, filtrable par catégorie WRC1 ou WRC2.
- [ ] Chaque position contient le temps cumulé, l'écart au leader et au précédent ; les pénalités sont incluses dans le cumul et signalées avec leur durée.
- [ ] Les équipages repartis sous le règlement Super Rally sont signalés comme tels.
- [ ] Les abandons sont listés à part, chacun avec la spéciale où il s'est produit.
- [ ] Le résultat contient la fraîcheur (après quelle spéciale, heure de la donnée) et l'indicateur de donnée périmée ; la durée de validité courte s'applique pendant un rallye en cours, comme pour le ticket 05.
- [ ] L'outil est déclaré à l'agent.
- [ ] Des fixtures JSON réelles des résultats cumulés, des pénalités et des abandons d'au moins un rallye, idéalement avec un cas de Super Rally, sont enregistrées.
- [ ] Des tests automatiques, sans réseau, passent par l'outil et couvrent le classement après une spéciale donnée et à l'arrivée, le filtrage par catégorie, une pénalité, un Super Rally et un abandon.
- [ ] Démonstration : dans le chat, « Qui a gagné le dernier rallye, et qui a abandonné ? » renvoie le vainqueur et les abandons.
