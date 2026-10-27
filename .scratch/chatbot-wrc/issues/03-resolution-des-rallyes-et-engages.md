# 03: Résolution des rallyes et engagés

**What to build:** Je demande « Qui est engagé au Portugal ? », « Les engagés WRC2 du Monte-Carlo ? » ou « Qui court ce week-end ? ». Le chatbot comprend de quel rallye je parle, que je le désigne par son nom, son pays, sa ville ou un repère relatif (« en cours », « dernier », « prochain », « ce week-end »), et me donne la liste des équipages engagés avec leur voiture, leur catégorie et leur constructeur ou leur équipe. Si ma désignation est ambiguë ou introuvable, il me propose les candidats possibles.

Spec : `.scratch/chatbot-wrc/spec.md`.

**Blocked by:** 01 (Tracer bullet : le calendrier, de bout en bout)

**Status:** ready-for-agent

- [ ] La résolution des rallyes convertit du texte libre en rallye de la saison en cours : nom, pays, ville, recherche insensible aux accents et à la casse, et repères relatifs selon l'horloge (« en cours », « dernier », « prochain », « ce week-end »).
- [ ] Quand la désignation est ambiguë ou introuvable, la résolution renvoie la liste des candidats plutôt qu'un choix arbitraire.
- [ ] L'outil `engages(rallye)` renvoie les équipages (pilote, copilote), leur voiture, leur catégorie (WRC1 ou WRC2, les autres catégories étant filtrées), leur constructeur ou leur équipe, ainsi que la fraîcheur et l'indicateur de donnée périmée.
- [ ] Les engagés suivent la durée de validité de 24 heures et le repli sur donnée périmée du ticket 01.
- [ ] L'outil est déclaré à l'agent, et le chatbot demande à l'utilisateur de choisir quand l'outil renvoie des candidats.
- [ ] Des fixtures JSON réelles des engagés d'au moins un rallye sont enregistrées.
- [ ] Des tests automatiques, sans réseau, passent par l'outil et couvrent chaque forme de désignation, les repères relatifs à différentes dates de la fausse horloge, l'ambiguïté, l'introuvable et le filtrage des catégories.
- [ ] Démonstration : dans le chat, « Qui est engagé au Portugal ? » renvoie la liste des équipages.
