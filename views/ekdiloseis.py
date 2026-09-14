import pandas as pd
import streamlit as st

from database import (
    add_kommati_se_ekdilosi,
    add_prova,
    add_synavlia,
    delete_ekdilosi,
    fetch_atoma,
    fetch_ekdiloseis,
    fetch_kommatia,
    fetch_kommatia_ekdilosis,
    fetch_symmetoxes,
    remove_kommati_apo_ekdilosi,
    set_parousia,
)
from utils import GREEK_MONTHS, format_date, person_label

st.title("📅 Πρόβες & Συναυλίες")


def _atomo_label(row):
    return person_label(row["Onoma"], row["Eponymo"])


@st.dialog("➕ Εισαγωγή Πρόβας / Συναυλίας", width="large")
def new_ekdilosi_dialog():
    event_type = st.radio("Τύπος", ["Πρόβα", "Συναυλία"], horizontal=True)

    col1, col2 = st.columns(2)
    with col1:
        imerominia = st.date_input("Ημερομηνία", format="DD/MM/YYYY")
    with col2:
        titlos = st.text_input("Τίτλος Συναυλίας") if event_type == "Συναυλία" else None

    xoros = st.text_input("Χώρος Διεξαγωγής") if event_type == "Συναυλία" else None
    extra_info = st.text_area("Σχόλια")

    st.divider()
    st.markdown("**Μαζική εισαγωγή συμμετεχόντων και ρεπερτορίου**")

    df_atoma = fetch_atoma()
    atomo_options = {_atomo_label(row): row["AtomoID"] for _, row in df_atoma.iterrows()}
    selected_atoma = st.multiselect("Άτομα που συμμετείχαν", options=list(atomo_options.keys()))

    df_kommatia = fetch_kommatia()
    kommati_options = {row["Titlos"]: row["KommatiID"] for _, row in df_kommatia.iterrows()}
    selected_kommatia = st.multiselect("Κομμάτια", options=list(kommati_options.keys()))

    if st.button("💾 Δημιουργία", width="stretch"):
        if event_type == "Συναυλία" and not titlos:
            st.error("Ο τίτλος της συναυλίας είναι υποχρεωτικός.")
            st.stop()

        if event_type == "Πρόβα":
            ekdilosi_id = add_prova(imerominia, extra_info or None)
        else:
            ekdilosi_id = add_synavlia(imerominia, titlos, xoros or None, extra_info or None)

        for label in selected_atoma:
            set_parousia(ekdilosi_id, atomo_options[label], True)
        for label in selected_kommatia:
            add_kommati_se_ekdilosi(ekdilosi_id, kommati_options[label])

        st.success("Η εγγραφή δημιουργήθηκε!")
        st.rerun()


@st.dialog("🔎 Στοιχεία Εκδήλωσης", width="large")
def view_ekdilosi_dialog(ekdilosi_id, row):
    kind = "Πρόβα" if row["EventType"] == "P" else "Συναυλία"
    st.subheader(f"{kind} — {format_date(row['Imerominia'])}")
    if row["EventType"] == "S":
        st.write(f"**Τίτλος:** {row['Titlos']}")
        if pd.notnull(row["Xoros"]):
            st.write(f"**Χώρος:** {row['Xoros']}")
    if pd.notnull(row["ExtraInfo"]):
        st.write(f"**Σχόλια:** {row['ExtraInfo']}")

    tab_parousies, tab_repertorio = st.tabs(["✅ Συμμετέχοντες", "🎼 Κομμάτια"])

    with tab_parousies:
        df_atoma = fetch_atoma()
        if df_atoma.empty:
            st.info("Δεν υπάρχουν καταχωρημένοι χορωδοί ακόμα.")
        else:
            df_symmetoxes = fetch_symmetoxes(ekdilosi_id)
            parousia_map = dict(zip(df_symmetoxes["AtomoID"], df_symmetoxes["Parousia"]))

            df_view = df_atoma[["AtomoID", "Onoma", "Eponymo"]].copy()
            df_view["Συμμετείχε"] = df_view["AtomoID"].map(lambda x: bool(parousia_map.get(x, False)))

            edited = st.data_editor(
                df_view,
                column_config={
                    "AtomoID": None,
                    "Onoma": st.column_config.TextColumn("Όνομα", disabled=True),
                    "Eponymo": st.column_config.TextColumn("Επώνυμο", disabled=True),
                    "Συμμετείχε": st.column_config.CheckboxColumn("Συμμετείχε"),
                },
                hide_index=True,
                width="stretch",
                key=f"view_parousies_{ekdilosi_id}",
            )

            if st.button("💾 Αποθήκευση Συμμετεχόντων", key=f"save_parousies_{ekdilosi_id}"):
                for _, r in edited.iterrows():
                    set_parousia(ekdilosi_id, int(r["AtomoID"]), bool(r["Συμμετείχε"]))
                st.success("Αποθηκεύτηκε!")
                st.rerun()

    with tab_repertorio:
        df_kommatia = fetch_kommatia()
        df_linked = fetch_kommatia_ekdilosis(ekdilosi_id)

        if df_linked.empty:
            st.caption("Δεν έχουν προστεθεί κομμάτια ακόμα.")
        else:
            for _, r in df_linked.iterrows():
                col_a, col_b = st.columns([5, 1])
                col_a.write(r["Titlos"])
                if col_b.button("🗑️", key=f"rm_kommati_{ekdilosi_id}_{r['KommatiEkdilosiID']}"):
                    remove_kommati_apo_ekdilosi(ekdilosi_id, int(r["KommatiID"]))
                    st.rerun()

        linked_ids = set(df_linked["KommatiID"]) if not df_linked.empty else set()
        available = df_kommatia[~df_kommatia["KommatiID"].isin(linked_ids)]
        if available.empty:
            st.caption("Όλα τα διαθέσιμα κομμάτια έχουν ήδη προστεθεί (ή δεν υπάρχουν κομμάτια ακόμα).")
        else:
            to_add = st.selectbox(
                "Προσθήκη κομματιού:", available["Titlos"].tolist(), key=f"add_kommati_sb_{ekdilosi_id}"
            )
            if st.button("➕ Προσθήκη", key=f"add_kommati_btn_{ekdilosi_id}"):
                kommati_id = int(available[available["Titlos"] == to_add]["KommatiID"].iloc[0])
                add_kommati_se_ekdilosi(ekdilosi_id, kommati_id)
                st.rerun()

    st.divider()
    if st.button("🗑️ Διαγραφή Εκδήλωσης", key=f"delete_ekdilosi_{ekdilosi_id}"):
        delete_ekdilosi(ekdilosi_id)
        st.success("Η εκδήλωση διαγράφηκε!")
        st.rerun()


if st.button("➕ Εισαγωγή Πρόβας / Συναυλίας"):
    new_ekdilosi_dialog()

st.divider()
st.subheader("📋 Λίστα Προβών & Συναυλιών")

df_ekd = fetch_ekdiloseis()

type_filter = st.segmented_control(
    "Τύπος", ["Όλα", "Πρόβες", "Συναυλίες"], default="Όλα", key="ekd_type_filter"
)

month_options = ["Όλοι"]
if not df_ekd.empty:
    periods = sorted({(d.year, d.month) for d in df_ekd["Imerominia"]}, reverse=True)
    month_options += [f"{GREEK_MONTHS[m - 1]} {y}" for y, m in periods]
month_filter = st.selectbox("Μήνας", month_options, key="ekd_month_filter")

df_shown = df_ekd
if type_filter == "Πρόβες":
    df_shown = df_shown[df_shown["EventType"] == "P"]
elif type_filter == "Συναυλίες":
    df_shown = df_shown[df_shown["EventType"] == "S"]
if month_filter != "Όλοι":
    month_name, year_str = month_filter.rsplit(" ", 1)
    month_num = GREEK_MONTHS.index(month_name) + 1
    year_num = int(year_str)
    df_shown = df_shown[
        (df_shown["Imerominia"].apply(lambda d: d.year) == year_num)
        & (df_shown["Imerominia"].apply(lambda d: d.month) == month_num)
    ]

if df_shown.empty:
    st.info("Δεν υπάρχουν εκδηλώσεις για τα επιλεγμένα φίλτρα.")
else:
    for _, row in df_shown.iterrows():
        with st.container(border=True):
            cols = st.columns([1.3, 1.3, 2.5, 2, 1.4, 1.2, 1.4])
            kind_icon = "🎤" if row["EventType"] == "P" else "🎭"
            kind = "Πρόβα" if row["EventType"] == "P" else "Συναυλία"
            cols[0].markdown(f"{kind_icon} **{kind}**")
            cols[1].write(format_date(row["Imerominia"]))
            cols[2].write(row["Titlos"] if pd.notnull(row["Titlos"]) else "—")
            cols[3].write(row["Xoros"] if pd.notnull(row["Xoros"]) else "—")
            cols[4].write(f"👥 {int(row['ParousesCount'])}")
            cols[5].write(f"🎼 {int(row['KommatiaCount'])}")
            if cols[6].button("🔍 Προβολή", key=f"view_{row['EkdilosiID']}", width="stretch"):
                view_ekdilosi_dialog(int(row["EkdilosiID"]), row)
