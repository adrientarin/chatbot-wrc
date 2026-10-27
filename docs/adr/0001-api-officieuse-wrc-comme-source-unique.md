# L'API officieuse de wrc.com comme source unique des données

Toutes les données (calendrier, classements, temps de spéciale, engagés) viennent de l'API JSON non documentée qu'utilise wrc.com (`https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api/`), sans clé. Aucune source officielle licenciée n'offre de temps par spéciale. Sportradar est payant et ne publie qu'après l'épreuve, et ewrc-results.com interdit l'usage par des agents d'IA. On accepte trois risques : l'API n'est pas licenciée, elle peut changer ou exiger une clé sans prévenir, et le direct n'est pas garanti. On les limite de trois façons : tout l'accès passe par un seul module, les réponses sont mises en cache et l'API est interrogée rarement. Le projet reste un usage personnel, non commercial.

## Options écartées

- **Sportradar Rally API** : payante, résultats seulement après l'épreuve, couverture des spéciales et de WRC2 non confirmée.
- **ewrc-results.com** : son robots.txt bloque explicitement les agents d'IA et interdit la réutilisation.
- **Feuilles de temps PDF de la FIA (Sportity)** : officielles, mais sans API. À réserver à la vérification d'un résultat contesté.
- **L'ancienne `api.wrc.com`** : n'existe plus (le nom de domaine ne répond plus).
