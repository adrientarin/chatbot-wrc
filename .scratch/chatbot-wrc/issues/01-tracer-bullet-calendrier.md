# 01: Tracer bullet : le calendrier, de bout en bout

**What to build:** Je lance l'application en local, j'ouvre le chat dans mon navigateur et je demande « C'est quand le prochain rallye ? » ou « Montre-moi le calendrier de la saison ». Le chatbot répond en français, en me tutoyant, avec enthousiasme, à partir du calendrier publié par la source, et précise de quand date la donnée. Si la source est injoignable, il donne le dernier calendrier connu en disant qu'il date, ou dit qu'il n'a pas la donnée. Ce ticket pose les fondations de toute l'architecture décrite dans la spec : module source WRC (avec transport HTTP et horloge injectés), cache, outils, agent Claude en mode tool use et interface Streamlit.

Spec : `.scratch/chatbot-wrc/spec.md`. Source de données : ADR 0001.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Le projet Python s'installe et se lance en local, et l'application de chat Streamlit s'ouvre dans le navigateur.
- [ ] La clé de l'API Anthropic est lue depuis un fichier d'environnement local non versionné, et un modèle de ce fichier sans vraie clé est fourni.
- [ ] Le choix du modèle Claude est fait en consultant la documentation à jour, et il est justifié dans le ticket (section Comments).
- [ ] Le module source WRC est le seul à connaître l'API (adresse, identifiants, format JSON) ; il reçoit un transport HTTP et une horloge injectables.
- [ ] Le cache conserve chaque réponse de la source avec son heure de récupération, la réutilise pendant 24 heures, et ne rappelle la source qu'après expiration, à la demande, sans tâche de fond.
- [ ] Si la source échoue (panne ou format inattendu), le cache renvoie la dernière donnée connue, marquée comme périmée ; sans donnée connue, l'outil le signale explicitement.
- [ ] La saison en cours est celle de l'année civile jusqu'à ce que la source publie le calendrier de la saison suivante.
- [ ] L'outil `calendrier()` renvoie les rallyes de la saison en cours avec leurs dates, leur statut (passé, en cours, à venir), la fraîcheur de la donnée et l'indicateur de donnée périmée ; le calendrier n'est jamais complété de mémoire.
- [ ] L'agent conversationnel déclare l'outil à Claude, exécute ses appels et conserve l'historique de la conversation pendant la session uniquement.
- [ ] Le prompt système de base établit la personnalité (français, tutoiement, enthousiaste mais factuel, neutre) et la règle : une donnée ne vient que d'un outil, et sa fraîcheur est toujours indiquée.
- [ ] Des fixtures JSON réelles (liste des saisons, détail de la saison en cours) sont enregistrées une fois depuis l'API.
- [ ] Des tests automatiques, sans réseau, passent par l'outil `calendrier()` avec un faux transport et une fausse horloge, et couvrent : le statut des rallyes selon la date, le cache valide et expiré, le repli sur la donnée périmée, l'absence de donnée, le basculement de saison.
- [ ] Démonstration : dans le chat, « C'est quand le prochain rallye ? » renvoie le bon rallye avec la fraîcheur de la donnée.
