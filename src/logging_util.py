from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


def setup_logging(niveau: str = "INFO", log_bestand: Optional[Path] = None) -> None:
    """Configureer de root logger voor de CLI applicatie.

    Parameters
    ----------
    niveau:
        Het logging niveau uitgedrukt als tekst (bijv. ``"INFO"`` of ``"DEBUG"``).
    log_bestand:
        Optioneel pad naar een log bestand waar berichten naartoe geschreven worden
        naast stderr. Wanneer weggelaten wordt alleen stderr logging ingeschakeld.
    """

    log_niveau = getattr(logging, niveau.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]
    if log_bestand:
        handlers.append(logging.FileHandler(log_bestand))

    logging.basicConfig(
        level=log_niveau,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=handlers,
    )


__all__ = ["setup_logging"]