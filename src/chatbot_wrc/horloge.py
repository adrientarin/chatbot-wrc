"""Horloge injectée dans le module source WRC et le cache."""

from datetime import datetime
from typing import Protocol


class Horloge(Protocol):
    def maintenant(self) -> datetime:
        """L'heure courante, avec son fuseau."""
        ...


class HorlogeSysteme:
    """L'horloge de production : l'heure réelle, dans le fuseau local."""

    def maintenant(self) -> datetime:
        return datetime.now().astimezone()
