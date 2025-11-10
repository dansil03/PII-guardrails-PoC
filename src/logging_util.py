# src/logging_util.py
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


def setup_logging(level: str = "INFO", log_bestand: Optional[Path] = None) -> None:
    """Configureer de root logger voor de CLI-applicatie.

    Parameters
    ----------
    level:
        Het loggingniveau uitgedrukt als tekst (bijv. ``"INFO"`` of ``"DEBUG"``).
    log_bestand:
        Optioneel pad naar een logbestand waar berichten naartoe geschreven worden
        naast stderr. Wanneer weggelaten, wordt alleen stderr-logging ingeschakeld.
    """

    log_niveau = getattr(logging, level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]
    if log_bestand:
        handlers.append(logging.FileHandler(log_bestand))

    logging.basicConfig(
        level=log_niveau,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=handlers,
    )


__all__ = ["setup_logging"]
