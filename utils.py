"""Shared display helpers used across ChoirApp pages."""

import pandas as pd
import streamlit as st

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


@st.dialog("Επιβεβαίωση Διαγραφής")
def confirm_delete_dialog(message, on_confirm):
    """Εκτελεί το `on_confirm` μόνο μετά από επιβεβαίωση.

    Το Streamlit δεν επιτρέπει dialog μέσα σε dialog: μέσα σε popup χρησιμοποιείται st.popover."""
    st.warning(message)
    col_yes, col_no = st.columns(2)
    if col_yes.button("🗑️ Διαγραφή", key="confirm_delete_yes", type="primary", width="stretch"):
        on_confirm()
        st.toast("Διαγράφηκε.")
        st.rerun()
    if col_no.button("Ακύρωση", key="confirm_delete_no", width="stretch"):
        st.rerun()


def select_folder(initialdir=None):
    """Native folder picker (tkinter) στον υπολογιστή που τρέχει το Streamlit app.

    Επιστρέφει (διαδρομή ή None, μήνυμα σφάλματος ή None)."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askdirectory(title="Επιλογή φακέλου", initialdir=initialdir)
        root.destroy()
        return path, None
    except Exception as e:
        return None, str(e)


def open_folder(path):
    """Ανοίγει τον φάκελο στον Explorer. Επιστρέφει (ok, μήνυμα σφάλματος)."""
    import os

    try:
        os.startfile(path)
        return True, None
    except FileNotFoundError:
        return False, (
            f"Δεν βρέθηκε ο φάκελος «{path}». Ελέγξτε ότι υπάρχει "
            "και ότι ο δίσκος (π.χ. δικτυακός δίσκος) είναι συνδεδεμένος σε αυτόν τον υπολογιστή."
        )
    except OSError:
        return False, f"Δεν ήταν δυνατό να ανοίξει ο «{path}»."
