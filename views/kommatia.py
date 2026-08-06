import pandas as pd
import streamlit as st

from database import (
    add_kommati,
    delete_kommati,
    fetch_kommati_links,
    fetch_kommatia,
    fetch_stixourgoi,
    fetch_synthetes,
    update_kommati,
)

st.title("🎼 Μουσικά Κομμάτια")

df_kommatia = fetch_kommatia()

st.dataframe(
    df_kommatia.rename(
        columns={
            "Titlos": "Τίτλος",
            "Xronia": "Έτος",
            "Synthetes": "Συνθέτες",
            "Stixourgoi": "Στιχουργοί",
            "ExtraInfo": "Σχόλια",
        }
    )[["Τίτλος", "Έτος", "Συνθέτες", "Στιχουργοί", "Σχόλια"]],
    width="stretch",
    hide_index=True,
)

st.divider()
st.subheader("➕ Προσθήκη / ✏️ Επεξεργασία Κομματιού")

df_synthetes = fetch_synthetes()
df_stixourgoi = fetch_stixourgoi()


def _synthetis_label(row):
    return f"{row['SynthetisEponymo']} {row['SynthetisOnoma'] or ''}".strip()


def _stixourgos_label(row):
    return f"{row['StixourgosEponymo']} {row['StixourgosOnoma'] or ''}".strip()


synthetis_options = {_synthetis_label(row): row["SynthetisID"] for _, row in df_synthetes.iterrows()}
stixourgos_options = {_stixourgos_label(row): row["StixourgosID"] for _, row in df_stixourgoi.iterrows()}

kommati_options = ["-- Νέο κομμάτι --"] + df_kommatia["Titlos"].tolist()
selected_title = st.selectbox("Επιλογή κομματιού για επεξεργασία:", kommati_options)

is_new = selected_title == "-- Νέο κομμάτι --"
current = None
current_synthetis_ids, current_stixourgos_ids = [], []
if not is_new:
    current = df_kommatia[df_kommatia["Titlos"] == selected_title].iloc[0]
    current_synthetis_ids, current_stixourgos_ids = fetch_kommati_links(int(current["KommatiID"]))

col1, col2 = st.columns(2)
with col1:
    titlos = st.text_input("Τίτλος", value="" if is_new else current["Titlos"])
with col2:
    default_xronia = 0 if is_new or pd.isnull(current["Xronia"]) else int(current["Xronia"])
    xronia = st.number_input("Έτος", value=default_xronia, step=1, min_value=0)

extra_info = st.text_area("Σχόλια", value="" if is_new else (current["ExtraInfo"] or ""))

if not synthetis_options:
    st.caption("Δεν υπάρχουν ακόμα συνθέτες καταχωρημένοι — πρόσθεσέ τους στα Στοιχεία Αναφοράς.")
selected_synthetes = st.multiselect(
    "Συνθέτες",
    options=list(synthetis_options.keys()),
    default=[k for k, v in synthetis_options.items() if v in current_synthetis_ids],
)

if not stixourgos_options:
    st.caption("Δεν υπάρχουν ακόμα στιχουργοί καταχωρημένοι — πρόσθεσέ τους στα Στοιχεία Αναφοράς.")
selected_stixourgoi = st.multiselect(
    "Στιχουργοί",
    options=list(stixourgos_options.keys()),
    default=[k for k, v in stixourgos_options.items() if v in current_stixourgos_ids],
)

col_save, col_delete = st.columns(2)
with col_save:
    if st.button("💾 Αποθήκευση", width="stretch", disabled=not titlos):
        synthetis_ids = [synthetis_options[s] for s in selected_synthetes]
        stixourgos_ids = [stixourgos_options[s] for s in selected_stixourgoi]
        xronia_val = int(xronia) if xronia else None
        if is_new:
            add_kommati(titlos, xronia_val, extra_info or None, synthetis_ids, stixourgos_ids)
            st.success(f"Το κομμάτι '{titlos}' προστέθηκε!")
        else:
            update_kommati(int(current["KommatiID"]), titlos, xronia_val, extra_info or None,
                            synthetis_ids, stixourgos_ids)
            st.success("Οι αλλαγές αποθηκεύτηκαν!")
        st.rerun()
with col_delete:
    if not is_new and st.button("🗑️ Διαγραφή", width="stretch"):
        delete_kommati(int(current["KommatiID"]))
        st.success(f"Το κομμάτι '{selected_title}' διαγράφηκε!")
        st.rerun()
