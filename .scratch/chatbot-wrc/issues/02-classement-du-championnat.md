# 02: Classement du championnat

**What to build:** Je demande « Où en est le championnat WRC1 ? », « Et chez les constructeurs ? », « Le championnat des copilotes WRC2 ? » ou « Combien de points a marqué Evans en Suède, et d'où viennent-ils ? ». Le chatbot donne le classement du championnat demandé, les écarts de points, les points rallye par rallye et leur détail (classement du dimanche, classement final, Power Stage, par exemple « 25 + 5 + 4 »), avec la fraîcheur de la donnée.

Spec : `.scratch/chatbot-wrc/spec.md`.

**Blocked by:** 01 (Tracer bullet : le calendrier, de bout en bout)

**Status:** ready-for-agent

- [ ] L'outil `classement_championnat(categorie, type)` accepte la catégorie WRC1 ou WRC2 et le type pilotes, copilotes ou constructeurs (constructeurs en WRC1 seulement) ; une combinaison invalide est signalée clairement.
- [ ] Le résultat contient, pour chaque position, les points totaux, les points par rallye et leur détail, ainsi que la fraîcheur de la donnée et l'indicateur de donnée périmée.
- [ ] Seuls les cinq championnats retenus par la spec sont utilisés ; le championnat des équipes et les autres catégories sont ignorés.
- [ ] Les données du classement du championnat suivent la durée de validité de 24 heures et le repli sur donnée périmée mis en place dans le ticket 01.
- [ ] L'outil est déclaré à l'agent, et le chatbot peut répondre aux questions de classement du championnat et d'écart de points.
- [ ] Des fixtures JSON réelles des classements du championnat (WRC1 pilotes, copilotes, constructeurs ; WRC2 pilotes, copilotes) sont enregistrées.
- [ ] Des tests automatiques, sans réseau, passent par l'outil et couvrent chaque catégorie et chaque type, le détail des points par rallye et la combinaison invalide.
- [ ] Démonstration : dans le chat, « Où en est le championnat des constructeurs ? » renvoie le bon classement avec la fraîcheur.
