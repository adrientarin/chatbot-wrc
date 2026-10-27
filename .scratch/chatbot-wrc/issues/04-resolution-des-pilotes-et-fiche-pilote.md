# 04: Résolution des pilotes et fiche pilote

**What to build:** Je demande « Parle-moi de Kalle », « Qui est le copilote de Rovanpera ? » ou « Où en est Tänak au championnat ? ». Le chatbot retrouve le pilote, que je le désigne par son prénom, son nom ou un surnom courant, avec ou sans accents, et me donne sa fiche : nationalité, voiture, constructeur ou équipe, copilote, position au classement du championnat. Il peut compléter avec de la culture rallye (carrière, titres), en précisant que ça vient de sa mémoire. Si ma désignation est ambiguë, il me propose les candidats.

Spec : `.scratch/chatbot-wrc/spec.md`.

**Blocked by:** 02 (Classement du championnat), 03 (Résolution des rallyes et engagés)

**Status:** ready-for-agent

- [ ] La résolution des pilotes convertit du texte libre en pilote WRC1 ou WRC2 de la saison en cours : prénom, nom, surnom courant, recherche insensible aux accents et à la casse, et approchée (une faute de frappe légère est tolérée).
- [ ] Quand la désignation est ambiguë ou introuvable, la résolution renvoie la liste des candidats.
- [ ] L'outil `fiche_pilote(nom)` renvoie la nationalité, la voiture, le constructeur ou l'équipe, le copilote, la catégorie et la position au classement du championnat, ainsi que la fraîcheur et l'indicateur de donnée périmée.
- [ ] L'outil est déclaré à l'agent ; le prompt système précise que la culture rallye peut compléter une fiche, toujours présentée comme venant de la mémoire du chatbot et jamais pour une donnée.
- [ ] Des fixtures JSON réelles du détail des championnats (pilotes, nationalités, constructeurs, équipes) sont enregistrées.
- [ ] Des tests automatiques, sans réseau, passent par l'outil et couvrent prénom, nom, absence d'accents, faute de frappe légère, ambiguïté, introuvable, un pilote WRC1 et un pilote WRC2.
- [ ] Démonstration : dans le chat, « Qui est le copilote de Rovanpera ? » renvoie le bon copilote.
