# Chatbot WRC

Un chatbot passionné de rallye qui répond en français sur la saison en cours du WRC. Voir `GLOSSARY.md` pour le vocabulaire, `docs/adr/` pour les décisions et `.scratch/chatbot-wrc/spec.md` pour la spec.

## Utilisation

Le chatbot est déployé sur Streamlit : https://wrc-chatbot-lmdarajjaderzrsdlm2thw.streamlit.app/

## Développement local

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"   # sous Linux/macOS : .venv/bin/python
cp .env.example .env                               # puis renseigne ANTHROPIC_API_KEY
.venv/Scripts/python -m streamlit run src/chatbot_wrc/app.py
```

Le chat s'ouvre dans le navigateur. Les réponses de la source sont gardées dans `cache/` (non versionné) : 24 heures en général, 1 minute pour les temps de spéciale et le classement d'un rallye en cours.

## Tests et vérification des types

```sh
.venv/Scripts/python -m pytest
.venv/Scripts/python -m mypy
```

Les tests passent par les outils exposés à Claude, avec un faux transport HTTP (fixtures JSON réelles dans `tests/fixtures/`) et une fausse horloge : aucun accès réseau.

Le comportement conversationnel se vérifie à la main, avec `docs/questions-types.md`, avant chaque changement important.
