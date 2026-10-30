"""Agent conversationnel : la boucle avec Claude en mode tool use.

L'historique de la conversation vit dans l'agent, le temps de la session seulement.
"""

import json
import threading
from typing import Any

import anthropic
from anthropic.types.beta import BetaMessageParam, BetaToolResultBlockParam

from chatbot_wrc.outils import DEFINITIONS, Outils
from chatbot_wrc.prompt import PROMPT_SYSTEME

MODELE_PAR_DEFAUT = "claude-haiku-5-5"

# Si un classifieur de sécurité refuse, l'API réessaie sur le modèle recommandé. Pas sur Haiku.
MODELES_AVEC_RATTRAPAGE = {
    "claude-fable-5-1",
    "claude-opus-5-5",
    "claude-opus-5",
    "claude-sonnet-5-5",
}
RATTRAPAGE: dict[str, Any] = {
    "betas": ["server-side-fallback-2026-07-01"],
    "fallbacks": "default",
}

REPONSE_REFUS = (
    "Oups, je ne peux pas répondre à ça. Pose-moi plutôt une question sur la saison de WRC !"
)


class Agent:
    def __init__(
        self, client: anthropic.Anthropic, outils: Outils, modele: str = MODELE_PAR_DEFAUT
    ) -> None:
        self._client = client
        self._outils = outils
        self._modele = modele
        self._rattrapage = RATTRAPAGE if modele in MODELES_AVEC_RATTRAPAGE else {}
        self._messages: list[BetaMessageParam] = []
        self._verrou = threading.Lock()

    def repondre(self, question: str) -> str:
        # Streamlit peut lancer une 2e question pendant que la 1re attend sa réponse :
        # l'API refuse un historique où leurs appels d'outils s'entremêlent.
        with self._verrou:
            return self._repondre(question)

    def _repondre(self, question: str) -> str:
        debut_du_tour = len(self._messages)
        self._messages.append({"role": "user", "content": question})
        while True:
            reponse = self._client.beta.messages.create(
                model=self._modele,
                max_tokens=16000,
                system=PROMPT_SYSTEME,
                tools=DEFINITIONS,
                messages=self._messages,
                # D'après la documentation, à low, un long prompt peut faire sauter une recherche.
                output_config={"effort": "medium"},
                **self._rattrapage,
            )
            if reponse.stop_reason == "refusal":
                # On retire ce tour de l'historique pour que la conversation reste utilisable.
                del self._messages[debut_du_tour:]
                return REPONSE_REFUS

            self._messages.append({"role": "assistant", "content": reponse.content})
            appels = [b for b in reponse.content if b.type == "tool_use"]
            if reponse.stop_reason != "tool_use" or not appels:
                return "".join(b.text for b in reponse.content if b.type == "text")

            resultats: list[BetaToolResultBlockParam] = [
                {
                    "type": "tool_result",
                    "tool_use_id": appel.id,
                    "content": self._executer(appel.name, appel.input),
                }
                for appel in appels
            ]
            self._messages.append({"role": "user", "content": resultats})

    def _executer(self, nom: str, arguments: Any) -> str:
        resultat = self._outils.executer(nom, arguments if isinstance(arguments, dict) else {})
        return json.dumps(resultat, ensure_ascii=False)
