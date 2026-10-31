import streamlit as st

from database import (
    fetch_atoma,
    fetch_ekdiloseis,
    fetch_kommatia,
    restore_atomo,
    restore_ekdilosi,
    restore_kommati,
)

st.title("🗑️ Σβησμένες Εγγραφές")


def _deleted_table(df, id_col, columns, restore, key, column_config=None):
    """Πίνακας σβησμένων εγγραφών με επαναφορά επιλεγμένων γραμμών."""
    if df.empty:
        st.caption("Δεν υπάρχουν σβησμένες εγγραφές.")
        return

    df = df.reset_index(drop=True)
    event = st.dataframe(
        df.rename(columns=columns)[list(columns.values())],
        column_config=column_config,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="multi-row",
        key=key,
    )
    selected_rows = event.selection["rows"]
    if st.button("♻️ Επαναφορά Επιλεγμένων", key=f"restore_{key}", disabled=not selected_rows):
        for i in selected_rows:
            restore(int(df.loc[i, id_col]))
        st.session_state.pop(key, None)
        st.toast("Η επαναφορά ολοκληρώθηκε.")
        st.rerun()


tab_ekdiloseis, tab_atoma, tab_kommatia = st.tabs(["📅 Εκδηλώσεις", "🧑‍🤝‍🧑 Άτομα", "🎼 Κομμάτια"])

with tab_ekdiloseis:
    df_ekd = fetch_ekdiloseis(deleted=True)
    df_ekd["Τύπος"] = df_ekd["EventType"].map({"P": "Πρόβα", "S": "Συναυλία"})
    _deleted_table(
        df_ekd,
        "EkdilosiID",
        {"Imerominia": "Ημερομηνία", "Τύπος": "Τύπος", "Titlos": "Τίτλος", "Xoros": "Χώρος", "ExtraInfo": "Σχόλια"},
        restore_ekdilosi,
        "deleted_ekdiloseis",
        {"Ημερομηνία": st.column_config.DateColumn("Ημερομηνία", format="DD/MM/YYYY")},
    )

with tab_atoma:
    _deleted_table(
        fetch_atoma(deleted=True),
        "AtomoID",
        {"Eponymo": "Επώνυμο", "Onoma": "Όνομα", "FoniDescr": "Φωνή", "KinitoTilefono": "Κινητό", "Email": "Email"},
        restore_atomo,
        "deleted_atoma",
    )

with tab_kommatia:
    _deleted_table(
        fetch_kommatia(deleted=True),
        "KommatiID",
        {"Titlos": "Τίτλος", "Xronia": "Έτος", "Synthetes": "Συνθέτες", "Stixourgoi": "Στιχουργοί", "ExtraInfo": "Σχόλια"},
        restore_kommati,
        "deleted_kommatia",
    )
