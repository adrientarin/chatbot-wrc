# 04: Résolution des pilotes et fiche pilote

**What to build:** Je demande « Parle-moi de Kalle », « Qui est le copilote de Rovanpera ? » ou « Où en est Tänak au championnat ? ». Le chatbot retrouve le pilote, que je le désigne par son prénom, son nom ou un surnom courant, avec ou sans accents, et me donne sa fiche : nationalité, voiture, constructeur ou équipe, copilote, position au classement du championnat. Il peut compléter avec de la culture rallye (carrière, titres), en précisant que ça vient de sa mémoire. Si ma désignation est ambiguë, il me propose les candidats.

Spec : `.scratch/chatbot-wrc/spec.md`.

**Blocked by:** 02 (Classement du championnat), 03 (Résolution des rallyes et engagés)

**Status:** ready-for-agent

- [x] La résolution des pilotes convertit du texte libre en pilote WRC1 ou WRC2 de la saison en cours : prénom, nom, surnom courant, recherche insensible aux accents et à la casse, et approchée (une faute de frappe légère est tolérée).
- [x] Quand la désignation est ambiguë ou introuvable, la résolution renvoie la liste des candidats.
- [x] L'outil `fiche_pilote(nom)` renvoie la nationalité, la voiture, le constructeur ou l'équipe, le copilote, la catégorie et la position au classement du championnat, ainsi que la fraîcheur et l'indicateur de donnée périmée.
- [x] L'outil est déclaré à l'agent ; le prompt système précise que la culture rallye peut compléter une fiche, toujours présentée comme venant de la mémoire du chatbot et jamais pour une donnée.
- [x] Des fixtures JSON réelles du détail des championnats (pilotes, nationalités, constructeurs, équipes) sont enregistrées.
- [x] Des tests automatiques, sans réseau, passent par l'outil et couvrent prénom, nom, absence d'accents, faute de frappe légère, ambiguïté, introuvable, un pilote WRC1 et un pilote WRC2.
- [x] Démonstration : dans le chat, « Qui est le copilote de Rovanpera ? » renvoie le bon copilote.

## Comments

**Sources de la fiche** : le classement du championnat des pilotes WRC1 et WRC2 (nom, nationalité, constructeur, équipe, position, points), et les engagés du dernier rallye du pilote, soit le plus récent de ses rallyes au classement du championnat (voiture, copilote, constructeur et équipe à jour, catégorie par la priorité FIA). Sans ces engagés, la fiche reste donnée sans voiture ni copilote. Aucune fixture nouvelle : celles du détail des championnats 2026 (tickets 02 et 03) suffisent.

**Catégorie** : le classement du championnat des pilotes WRC1 classe aussi les pilotes WRC2 qui y marquent des points (Mikkelsen, Suninen, Greensmith…). La fiche donne donc ses positions dans chaque classement où il figure (`championnats`), et la catégorie de son dernier engagement ; à défaut, WRC2 s'il est classé en WRC2.

**Basculement** : à partir du 5 octobre 2026, le calendrier est passé à 2027, où personne n'est encore classé. La fiche porte alors sur la saison qui vient de se terminer.

**Résolution des pilotes** :
- Chaque mot doit désigner un mot du nom (prénom ou nom), sans accents ni casse ; à défaut, à une faute de frappe près (distance de Damerau-Levenshtein ≤ 1 dès 4 lettres, ≤ 2 dès 8 ; aucune faute sous 4 lettres).
- Surnoms courants : Seb (Ogier), Taka (Katsuta), JML (Latvala), Olly (Solberg), Elf (Evans).
- Ambiguïté (« Rossel ») : les candidats ; introuvable : les 5 noms les plus proches, qui peuvent n'avoir aucun rapport. Le prompt dit alors au chatbot que le pilote n'est pas classé cette saison.

**Démonstration** : Kalle Rovanperä (et Ott Tänak) ne courent pas en 2026 ; « Qui est le copilote de Rovanpera ? » doit donc répondre qu'il n'est pas classé cette saison, sans inventer de copilote. Pour le cas nominal : « Qui est le copilote d'Ogier ? » → Vincent Landais.

**Connu, non traité** :
- Le dernier rallye est le plus récent du pilote au classement du championnat, pas forcément son dernier engagement : Yamamoto, engagé en Sardaigne sans y figurer au classement, a la fiche du Chili (copilote Topi Luhtinen au lieu de James Fulton).
- Pas de préfixes ni de diminutifs hors de la table des surnoms (« Josh » ne trouve pas McErlean).

**Vérifié pendant l'implémentation** : l'outil contre la vraie API (Ogier, Mikkelsen, Yamamoto, Rovanpera). Reste la démonstration dans le chat, avec la clé.
