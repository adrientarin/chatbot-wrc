# 01: Tracer bullet : le calendrier, de bout en bout

**What to build:** Je lance l'application en local, j'ouvre le chat dans mon navigateur et je demande « C'est quand le prochain rallye ? » ou « Montre-moi le calendrier de la saison ». Le chatbot répond en français, en me tutoyant, avec enthousiasme, à partir du calendrier publié par la source, et précise de quand date la donnée. Si la source est injoignable, il donne le dernier calendrier connu en disant qu'il date, ou dit qu'il n'a pas la donnée. Ce ticket pose les fondations de toute l'architecture décrite dans la spec : module source WRC (avec transport HTTP et horloge injectés), cache, outils, agent Claude en mode tool use et interface Streamlit.

Spec : `.scratch/chatbot-wrc/spec.md`. Source de données : ADR 0001.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] Le projet Python s'installe et se lance en local, et l'application de chat Streamlit s'ouvre dans le navigateur.
- [x] La clé de l'API Anthropic est lue depuis un fichier d'environnement local non versionné, et un modèle de ce fichier sans vraie clé est fourni.
- [x] Le choix du modèle Claude est fait en consultant la documentation à jour, et il est justifié dans le ticket (section Comments).
- [x] Le module source WRC est le seul à connaître l'API (adresse, identifiants, format JSON) ; il reçoit un transport HTTP et une horloge injectables.
- [x] Le cache conserve chaque réponse de la source avec son heure de récupération, la réutilise pendant 24 heures, et ne rappelle la source qu'après expiration, à la demande, sans tâche de fond.
- [x] Si la source échoue (panne ou format inattendu), le cache renvoie la dernière donnée connue, marquée comme périmée ; sans donnée connue, l'outil le signale explicitement.
- [x] La saison en cours est celle de l'année civile jusqu'à ce que la source publie le calendrier de la saison suivante.
- [x] L'outil `calendrier()` renvoie les rallyes de la saison en cours avec leurs dates, leur statut (passé, en cours, à venir), la fraîcheur de la donnée et l'indicateur de donnée périmée ; le calendrier n'est jamais complété de mémoire.
- [x] L'agent conversationnel déclare l'outil à Claude, exécute ses appels et conserve l'historique de la conversation pendant la session uniquement.
- [x] Le prompt système de base établit la personnalité (français, tutoiement, enthousiaste mais factuel, neutre) et la règle : une donnée ne vient que d'un outil, et sa fraîcheur est toujours indiquée.
- [x] Des fixtures JSON réelles (liste des saisons, détail de la saison en cours) sont enregistrées une fois depuis l'API.
- [x] Des tests automatiques, sans réseau, passent par l'outil `calendrier()` avec un faux transport et une fausse horloge, et couvrent : le statut des rallyes selon la date, le cache valide et expiré, le repli sur la donnée périmée, l'absence de donnée, le basculement de saison.
- [ ] Démonstration : dans le chat, « C'est quand le prochain rallye ? » renvoie le bon rallye avec la fraîcheur de la donnée.

## Comments

**Choix du modèle Claude** (documentation à jour consultée le 2026-10-27) : `claude-opus-5-5`, le modèle par défaut recommandé par Anthropic, à 4 $ / 20 $ par million de jetons en entrée / sortie, soit moins que l'Opus précédent (5 $ / 25 $). Pour le rapport qualité/prix d'un chat, le levier choisi est l'effort `low`, que la documentation conseille pour la conversation, plutôt qu'un modèle plus petit : on garde la qualité d'Opus pour le choix des outils et le respect de la règle « pas de donnée inventée », tout en réduisant les jetons de réflexion et la latence. Le modèle reste réglable via `CLAUDE_MODELE` dans `.env` (par exemple `claude-sonnet-5-5`, 2 $ / 10 $) si le coût devient un sujet. Les refus des classifieurs de sécurité sont rattrapés côté serveur (`fallbacks: "default"`, beta `server-side-fallback-2026-07-01`).

**Interprétation du basculement de saison** : la saison en cours est celle de l'année civile. Si son calendrier n'est pas encore publié (début janvier), c'est la précédente. Elle ne cède la place à la suivante qu'une fois **tous ses rallyes passés** et la suivante publiée. Sans cette condition, le calendrier 2027 déjà publié par la source (15 rallyes) aurait fait basculer la saison en plein milieu de 2026. Au 2026-10-27, la source ne publie que 13 rallyes pour 2026, tous terminés (le dernier est la Sardaigne, 1er–4 octobre). Le chatbot considère donc 2027 comme la saison en cours, et le prochain rallye est le Monte-Carlo (21–24 janvier 2027). Juste après le basculement, l'outil renvoie aussi la saison qui vient de se terminer (`saison_terminee`), pour répondre à « le dernier rallye ». Règle validée le 2026-10-27 et reportée dans `spec.md` (section « Saison en cours »).

**Démonstration** : à faire à la main une fois la clé renseignée dans `.env` (aucune clé n'était disponible pendant l'implémentation). Vérifié pendant l'implémentation : l'outil `calendrier()` contre la vraie API (saison 2027, Monte-Carlo à venir), la boucle de l'agent avec un faux client (appel d'outil, historique, refus), et le démarrage de Streamlit (serveur lancé, `/_stcore/health` répond `ok`).
