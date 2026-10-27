"""Agent conversationnel : la boucle avec Claude en mode tool use.

L'historique de la conversation vit dans l'agent, le temps de la session seulement.
"""

import json
from typing import Any

import anthropic
from anthropic.types.beta import BetaMessageParam, BetaToolResultBlockParam

from chatbot_wrc.outils import DEFINITIONS, Outils
from chatbot_wrc.prompt import PROMPT_SYSTEME

MODELE_PAR_DEFAUT = "claude-opus-5-5"

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
        self._messages: list[BetaMessageParam] = []

    def repondre(self, question: str) -> str:
        debut_du_tour = len(self._messages)
        self._messages.append({"role": "user", "content": question})
        while True:
            reponse = self._client.beta.messages.create(
                model=self._modele,
                max_tokens=16000,
                system=PROMPT_SYSTEME,
                tools=DEFINITIONS,
                messages=self._messages,
                # Un échange de chat : l'effort bas suffit et réduit le coût et la latence.
                output_config={"effort": "low"},
                # Si un classifieur de sécurité refuse, l'API réessaie sur le modèle recommandé.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
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
