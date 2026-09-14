"""Shared display helpers used across ChoirApp pages."""

import pandas as pd

GREEK_MONTHS = [
    "Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος",
    "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος",
]


def format_date(d):
    """Return a date/datetime as 'dd/mm/yy' for display. Empty string if missing."""
    if d is None or pd.isnull(d):
        return ""
    return d.strftime("%d/%m/%y")


def person_label(onoma, eponymo):
    """Return 'Onoma Eponymo' for display — name first, trimmed of stray whitespace."""
    return f"{onoma or ''} {eponymo or ''}".strip()
