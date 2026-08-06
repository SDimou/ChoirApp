import pandas as pd
import streamlit as st
from sqlalchemy.exc import IntegrityError

from database import (
    add_foni,
    add_stixourgos,
    add_synthetis,
    delete_foni,
    delete_stixourgos,
    delete_synthetis,
    fetch_foni,
    fetch_stixourgoi,
    fetch_synthetes,
    update_foni,
)

st.title("⚙️ Στοιχεία Αναφοράς")

tab_foni, tab_synthetes, tab_stixourgoi = st.tabs(["🎤 Φωνές", "🎹 Συνθέτες", "✍️ Στιχουργοί"])

with tab_foni:
    df = fetch_foni()
    edited = st.data_editor(
        df,
        column_config={
            "FoniID": None,
            "FoniSynt": st.column_config.TextColumn("Συντομογραφία", required=True),
            "FoniDescr": st.column_config.TextColumn("Περιγραφή"),
        },
        num_rows="dynamic",
        width="stretch",
        key="foni_editor",
    )
    if st.button("💾 Αποθήκευση Φωνών"):
        current_ids = set(df["FoniID"])
        edited_ids = set(edited["FoniID"].dropna())
        try:
            for foni_id in current_ids - edited_ids:
                delete_foni(int(foni_id))
        except IntegrityError:
            st.error("Δεν μπορεί να διαγραφεί φωνή που χρησιμοποιείται ήδη από χορωδό.")
            st.stop()

        for _, row in edited.iterrows():
            if not row["FoniSynt"]:
                continue
            descr = None if pd.isnull(row["FoniDescr"]) else row["FoniDescr"]
            if pd.isnull(row["FoniID"]):
                add_foni(row["FoniSynt"], descr)
            else:
                update_foni(int(row["FoniID"]), row["FoniSynt"], descr)
        st.success("Οι φωνές αποθηκεύτηκαν!")
        st.rerun()

with tab_synthetes:
    df = fetch_synthetes()
    st.dataframe(
        df.rename(columns={"SynthetisEponymo": "Επώνυμο", "SynthetisOnoma": "Όνομα"})[["Επώνυμο", "Όνομα"]],
        width="stretch",
        hide_index=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        new_eponymo = st.text_input("Επώνυμο Συνθέτη")
    with col2:
        new_onoma = st.text_input("Όνομα Συνθέτη")
    if st.button("➕ Προσθήκη Συνθέτη", disabled=not new_eponymo):
        add_synthetis(new_eponymo, new_onoma or None)
        st.success("Ο συνθέτης προστέθηκε!")
        st.rerun()

    if not df.empty:
        label = lambda r: f"{r['SynthetisEponymo']} {r['SynthetisOnoma'] or ''}".strip()
        options = {label(row): row["SynthetisID"] for _, row in df.iterrows()}
        to_delete = st.selectbox("Διαγραφή συνθέτη:", list(options.keys()), key="del_synthetis_sb")
        if st.button("🗑️ Διαγραφή Συνθέτη"):
            try:
                delete_synthetis(options[to_delete])
                st.success("Ο συνθέτης διαγράφηκε!")
                st.rerun()
            except IntegrityError:
                st.error("Δεν μπορεί να διαγραφεί — ο συνθέτης χρησιμοποιείται σε κάποιο κομμάτι.")

with tab_stixourgoi:
    df = fetch_stixourgoi()
    st.dataframe(
        df.rename(columns={"StixourgosEponymo": "Επώνυμο", "StixourgosOnoma": "Όνομα"})[["Επώνυμο", "Όνομα"]],
        width="stretch",
        hide_index=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        new_eponymo = st.text_input("Επώνυμο Στιχουργού")
    with col2:
        new_onoma = st.text_input("Όνομα Στιχουργού")
    if st.button("➕ Προσθήκη Στιχουργού", disabled=not new_eponymo):
        add_stixourgos(new_eponymo, new_onoma or None)
        st.success("Ο στιχουργός προστέθηκε!")
        st.rerun()

    if not df.empty:
        label = lambda r: f"{r['StixourgosEponymo']} {r['StixourgosOnoma'] or ''}".strip()
        options = {label(row): row["StixourgosID"] for _, row in df.iterrows()}
        to_delete = st.selectbox("Διαγραφή στιχουργού:", list(options.keys()), key="del_stixourgos_sb")
        if st.button("🗑️ Διαγραφή Στιχουργού"):
            try:
                delete_stixourgos(options[to_delete])
                st.success("Ο στιχουργός διαγράφηκε!")
                st.rerun()
            except IntegrityError:
                st.error("Δεν μπορεί να διαγραφεί — ο στιχουργός χρησιμοποιείται σε κάποιο κομμάτι.")
