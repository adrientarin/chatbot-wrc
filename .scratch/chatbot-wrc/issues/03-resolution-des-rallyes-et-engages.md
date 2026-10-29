# 03: Résolution des rallyes et engagés

**What to build:** Je demande « Qui est engagé au Portugal ? », « Les engagés WRC2 du Monte-Carlo ? » ou « Qui court ce week-end ? ». Le chatbot comprend de quel rallye je parle, que je le désigne par son nom, son pays, sa ville ou un repère relatif (« en cours », « dernier », « prochain », « ce week-end »), et me donne la liste des équipages engagés avec leur voiture, leur catégorie et leur constructeur ou leur équipe. Si ma désignation est ambiguë ou introuvable, il me propose les candidats possibles.

Spec : `.scratch/chatbot-wrc/spec.md`.

**Blocked by:** 01 (Tracer bullet : le calendrier, de bout en bout)

**Status:** ready-for-agent

- [x] La résolution des rallyes convertit du texte libre en rallye de la saison en cours : nom, pays, ville, recherche insensible aux accents et à la casse, et repères relatifs selon l'horloge (« en cours », « dernier », « prochain », « ce week-end »).
- [x] Quand la désignation est ambiguë ou introuvable, la résolution renvoie la liste des candidats plutôt qu'un choix arbitraire.
- [x] L'outil `engages(rallye)` renvoie les équipages (pilote, copilote), leur voiture, leur catégorie (WRC1 ou WRC2, les autres catégories étant filtrées), leur constructeur ou leur équipe, ainsi que la fraîcheur et l'indicateur de donnée périmée.
- [x] Les engagés suivent la durée de validité de 24 heures et le repli sur donnée périmée du ticket 01.
- [x] L'outil est déclaré à l'agent, et le chatbot demande à l'utilisateur de choisir quand l'outil renvoie des candidats.
- [x] Des fixtures JSON réelles des engagés d'au moins un rallye sont enregistrées.
- [x] Des tests automatiques, sans réseau, passent par l'outil et couvrent chaque forme de désignation, les repères relatifs à différentes dates de la fausse horloge, l'ambiguïté, l'introuvable et le filtrage des catégories.
- [ ] Démonstration : dans le chat, « Qui est engagé au Portugal ? » renvoie la liste des équipages.

## Comments

**Points d'entrée** : `events/{eventId}.json` (le « rally » principal de l'événement, `isMain`) puis `events/{eventId}/rallies/{rallyId}/entries.json`. L'identifiant de l'événement est lu dans le détail de la saison, par le numéro du rallye.

**Catégorie** (vérifié sur le Monte-Carlo, le Portugal et la Sardaigne 2026) : elle se lit dans la priorité FIA de l'engagé. P1 correspond toujours à une Rally1 (WRC1), et P2 à une Rally2 inscrite en WRC2, y compris quand `eligibility` est vide (Yamamoto au Portugal, présent au championnat WRC2). Les Rally2 sans priorité (championnats nationaux, Masters) et les Rally3 et au-delà (WRC3, Junior) sont filtrées. Les non-partants et les forfaits restent dans la liste, sans indicateur : c'est la liste des engagés, pas celle des partants.

**Résolution des rallyes** :
- Recherche par mots entiers, sans accents, sans casse ni ponctuation. Tous les mots significatifs doivent apparaître dans le nom, le pays, le lieu ou les noms français ajoutés (Suède, Sardaigne, Acropole…).
- Les repères relatifs se combinent avec un nom : « le dernier Monte-Carlo ».
- Une année désigne la saison : « le Portugal 2026 ».
- Un rallye absent de la saison en cours est cherché dans la saison qui vient de se terminer.
- « Ce week-end » : la semaine du jour, du lundi au dimanche ; un lundi, il désigne donc le week-end à venir.
- Ambiguïté ou introuvable : aucun choix, les candidats sont renvoyés.

**Calendrier** (complète le ticket 01) : en janvier, avant le premier rallye, la saison précédente est renvoyée en `saison_terminee`, pour que « le dernier rallye » reste connu. Le classement du championnat en profite de la même façon.

**Connu, non traité** :
- « Toyota » désigne le Rally Japan, dont le lieu est Toyota City.
- La recherche ne tolère pas les fautes de frappe : la spec ne demande une recherche approchée que pour les pilotes.

**Vérifié pendant l'implémentation** : l'outil contre la vraie API (le Portugal 2026 donne 53 équipages ; « le prochain » donne le Monte-Carlo 2027, dont les engagés ne sont pas encore publiés). Reste la démonstration dans le chat, avec la clé.
