"""Transport HTTP injecté dans le module source WRC."""

import urllib.request
from typing import Protocol


class ErreurTransport(Exception):
    """La requête HTTP n'a pas abouti (réseau, délai, code d'erreur)."""


class Transport(Protocol):
    def get(self, url: str) -> str:
        """Renvoie le corps de la réponse, ou lève `ErreurTransport`."""
        ...


class TransportHTTP:
    """Le transport de production : de vraies requêtes HTTP."""

    def __init__(self, delai_secondes: float = 15) -> None:
        self._delai = delai_secondes

    def get(self, url: str) -> str:
        requete = urllib.request.Request(url, headers={"User-Agent": "chatbot-wrc (usage personnel)"})
        try:
            with urllib.request.urlopen(requete, timeout=self._delai) as reponse:
                corps: bytes = reponse.read()
        except OSError as erreur:  # URLError, HTTPError et délais dépassés en héritent
            raise ErreurTransport(f"{url} : {erreur}") from erreur
        return corps.decode("utf-8")
