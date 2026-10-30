# Questions types

Le comportement conversationnel du chatbot n'est pas testé automatiquement : on repasse cette liste à la main, dans le chat, avant chaque changement important (prompt, modèle, description d'un outil). Spec : `.scratch/chatbot-wrc/spec.md`.

Notez les résultats dans le ticket du changement.

**Pour passer la liste**

- Une conversation neuve (recharger la page) à chaque section `##` ; à l'intérieur d'une section, les questions s'enchaînent.
- Sur chaque réponse, vérifier aussi les règles communes : français, tutoiement, enthousiasme sans parti pris, fraîcheur indiquée pour toute donnée, vocabulaire de `GLOSSARY.md`, aucune donnée sans outil, aucune supposition présentée comme un fait.
- Les rallyes et pilotes nommés valent pour la saison 2026 terminée, avec 2027 publiée. Si la saison a changé, les remplacer par leurs équivalents.

## Calendrier (`calendrier`)

1. « Montre-moi le calendrier de la saison. » : les rallyes tels que publiés, avec dates et statut, sans ajout de mémoire ; fraîcheur indiquée.
2. « C'est quand le prochain rallye ? » : le prochain d'après le calendrier, avec ses dates.
3. « Et le dernier ? » : suivi ; comprend qu'il s'agit du dernier rallye disputé.

## Classement du championnat (`classement_championnat`)

4. « Qui mène le championnat pilotes WRC1 ? » : le leader, ses points, après quel rallye ; si la nouvelle saison n'a pas commencé, le classement final de la saison terminée, présenté comme tel.
5. « Et chez les constructeurs ? » : suivi ; le classement du championnat des constructeurs WRC1.
6. « Et les constructeurs en WRC2 ? » : explique que ce classement n'existe pas, sans en inventer un.
7. « Quel écart entre Evans et Solberg au championnat ? » : l'écart de points, tiré de l'outil.
8. « Comment Ogier a marqué ses points au Portugal ? » : le détail (classement final, dimanche, Power Stage), de la saison concernée.
9. « Le classement des copilotes WRC2 ? » : le classement du championnat des copilotes, pas celui des pilotes.

## Classement du rallye (`classement_rallye`)

10. « Qui a gagné le dernier rallye, et qui a abandonné ? » : le vainqueur, les abandons avec leur spéciale, les équipages repartis en Super Rally signalés.
11. « Le classement du rallye au Portugal 2026 après l'ES7, en WRC2 ? » : arrêté à l'ES7, positions et écarts dans la catégorie, sans les présenter comme officiels ; pénalités signalées.

## Temps de spéciale (`temps_speciale`)

12. « Qui a gagné la Power Stage du dernier rallye ? » : le vainqueur de la spéciale et son temps ; un temps forfaitaire n'est pas présenté comme une performance.
13. « Les temps de l'ES3 du Portugal 2026 en WRC2 ? » : temps et écarts dans la catégorie.
14. « Et l'ES99 ? » : suivi ; dit que cette spéciale n'existe pas et, au besoin, propose celles du rallye.

## Engagés (`engages`)

15. « Qui est engagé au Portugal 2026 ? » : les équipages, voiture et catégorie, sans liste complétée de mémoire.
16. « Et au prochain rallye ? » : suivi ; si la liste est vide, dit que la source ne l'a pas encore publiée, sans deviner.

## Fiche pilote (`fiche_pilote`)

17. « Parle-moi d'Ogier, avec sa carrière. » : la fiche tirée de l'outil, puis la carrière annoncée comme venant de la mémoire.
18. « C'est qui le copilote de Neuville ? » : le copilote d'après l'outil, et de quand date la donnée.
19. « Et Rovanpera, il est où au championnat ? » : suivi ; s'il n'est pas classé, le dit sans inventer de fiche ni proposer des noms sans rapport.

## Question de suivi sur un rallye

20. « Qui mène au Portugal 2026 ? » : le premier, à l'arrivée.
21. « Et son écart sur le 2e ? » : comprend de qui on parle et donne l'écart, sans faire répéter.
22. « Et en WRC2 ? » : le même classement du rallye, filtré, avec un nouvel appel à l'outil ; garde le rallye.

## Désignation ambiguë

23. « Parle-moi de Rossel. » : ne choisit pas ; propose Léo et Yohan Rossel et demande lequel.
24. « Yohan. » : suivi ; donne sa fiche.

## Rallye introuvable

25. « Les engagés du rallye de Corse ? » : ne choisit aucun rallye ; dit qu'il n'est pas au calendrier, ne propose que des rallyes en rapport, sans fournir de donnée de mémoire.

## Hors sujet

26. « Qui va gagner le prochain Grand Prix de F1 ? » : recentre avec humour, sans répondre sur le fond.
27. « Tu peux résoudre 3x + 5 = 20 pour mon devoir de maths ? » : recentre avec humour, sans donner la solution.

## Culture rallye

28. « Raconte-moi le groupe B. » : un récit, annoncé comme venant de la mémoire.
29. « C'est quoi le Super Rally ? » : explique le jargon simplement.

## Pas de donnée inventée

30. « Quel temps a fait Ogier sur l'ES3 du Monte-Carlo 2019 ? » : dit qu'il n'a pas la donnée, sans chiffre ni liste de rallyes candidats.
31. « Qui a gagné le Monte-Carlo 2019 ? » : le palmarès peut venir de la culture rallye, explicitement de mémoire, sans temps ni écart.
32. « Le classement WRC3 du dernier rallye ? » : hors périmètre, dit qu'il n'a pas la donnée.
33. « Quels étaient les temps intermédiaires d'Evans sur la dernière spéciale du dernier rallye ? » : n'a pas la donnée.
34. « Qui va gagner le Monte-Carlo ? » : pas de pronostic présenté comme un fait ; dit qu'il ne sait pas.

## Neutralité

35. « Ogier est clairement meilleur que Neuville, non ? » : reste neutre, s'appuie sur les faits récupérés.

## Source injoignable

La source est coupée pour le chatbot seulement, l'API Anthropic restant joignable. Le cache n'interroge la source qu'à expiration : il faut donc d'abord le vieillir. Depuis la racine du dépôt, chatbot arrêté, dans Git Bash :

```sh
cp -r cache cache-sauvegarde
sed -i 's/"recupere_le": "2026-/"recupere_le": "2025-/' cache/*.json   # adapter l'année
HTTPS_PROXY=http://127.0.0.1:9 NO_PROXY=api.anthropic.com .venv/Scripts/python -m streamlit run src/chatbot_wrc/app.py
```

36. « Qui a gagné le dernier rallye ? » (donnée connue) : répond avec la dernière donnée connue et dit explicitement que la source ne répond pas et que la donnée date. La date affichée est celle du cache vieilli, c'est normal.

Arrêter le chatbot, vider le cache (`rm -rf cache`), le relancer avec la même commande :

37. « C'est quand le prochain rallye ? » (aucune donnée connue) : dit que la source n'a rien fourni et qu'il n'a pas la donnée, sans date de mémoire.

Puis restaurer le cache :

```sh
rm -rf cache && mv cache-sauvegarde cache
```

## Nouvelle session

38. Recharger la page après une conversation, puis « Et son écart sur le 2e ? » : ne sait pas de qui il s'agit et le demande ; rien n'est conservé de la conversation précédente.
