# 02: Classement du championnat

**What to build:** Je demande « Où en est le championnat WRC1 ? », « Et chez les constructeurs ? », « Le championnat des copilotes WRC2 ? » ou « Combien de points a marqué Evans en Suède, et d'où viennent-ils ? ». Le chatbot donne le classement du championnat demandé, les écarts de points, les points rallye par rallye et leur détail (classement du dimanche, classement final, Power Stage, par exemple « 25 + 5 + 4 »), avec la fraîcheur de la donnée.

Spec : `.scratch/chatbot-wrc/spec.md`.

**Blocked by:** 01 (Tracer bullet : le calendrier, de bout en bout)

**Status:** ready-for-agent

- [x] L'outil `classement_championnat(categorie, type)` accepte la catégorie WRC1 ou WRC2 et le type pilotes, copilotes ou constructeurs (constructeurs en WRC1 seulement) ; une combinaison invalide est signalée clairement.
- [x] Le résultat contient, pour chaque position, les points totaux, les points par rallye et leur détail, ainsi que la fraîcheur de la donnée et l'indicateur de donnée périmée.
- [x] Seuls les cinq championnats retenus par la spec sont utilisés ; le championnat des équipes et les autres catégories sont ignorés.
- [x] Les données du classement du championnat suivent la durée de validité de 24 heures et le repli sur donnée périmée mis en place dans le ticket 01.
- [x] L'outil est déclaré à l'agent, et le chatbot peut répondre aux questions de classement du championnat et d'écart de points.
- [x] Des fixtures JSON réelles des classements du championnat (WRC1 pilotes, copilotes, constructeurs ; WRC2 pilotes, copilotes) sont enregistrées.
- [x] Des tests automatiques, sans réseau, passent par l'outil et couvrent chaque catégorie et chaque type, le détail des points par rallye et la combinaison invalide.
- [x] Démonstration : dans le chat, « Où en est le championnat des constructeurs ? » renvoie le bon classement avec la fraîcheur.

## Comments

**Points d'entrée** : `championship-detail.json` (participants et rallyes du championnat) et `championship-overall-results.json` (points totaux et par rallye), avec `championshipId` et `seasonId`. Les identifiants des championnats sont lus par leur nom dans le détail de la saison ; seuls les cinq championnats de la spec sont retenus.

**Sens du détail des points** (vérifié le 2026-10-29 sur les temps de la Power Stage du Rally Sweden 2026) : pour les pilotes et copilotes WRC1, « classement final + dimanche + Power Stage », le troisième terme n'étant publié que pour les cinq premiers de la Power Stage (Neuville, 7e et vainqueur de la Power Stage : « 6 + 0 + 5 »). En WRC2, un seul terme (classement final), et certains résultats sont décomptés (`compte` faux). Pour les constructeurs, le détail additionne les points de plusieurs équipages : il est donné tel quel, sans être nommé, et la position au rallye n'est pas reprise car la source la publie de façon incohérente.

**Saison** : le classement suit la saison en cours du calendrier. Au 2026-10-29 c'est 2027, dont les classements sont vides (et les championnats WRC2 pas encore créés, signalé par `championnat_publie` faux) ; le classement final 2026 est renvoyé dans `saison_terminee`, et le prompt système demande de le présenter comme tel.

**À surveiller** : un classement WRC2 fait environ 80 000 caractères (137 équipages avec leurs rallyes), soit de l'ordre de 25 000 jetons par appel. À réduire si le coût devient un sujet (par exemple en omettant les équipages sans point).

**Vérifié pendant l'implémentation** : l'outil contre la vraie API, pour les cinq championnats (2027 vide, 2026 complet en `saison_terminee`). Reste la démonstration dans le chat, avec la clé.

