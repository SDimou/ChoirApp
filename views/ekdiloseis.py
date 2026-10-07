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


def _atomo_label_eponymo_prota(row):
    return f"{row['Eponymo'] or ''} {row['Onoma'] or ''}".strip()


@st.dialog("➕ Εισαγωγή Πρόβας / Συναυλίας", width="large")
def new_ekdilosi_dialog():
    event_type = st.radio("Τύπος", ["Πρόβα", "Συναυλία"], horizontal=True)
    typos_provas = (
        st.radio("Τύπος Πρόβας", ["Κανονική", "Προγενική", "Γενική"], horizontal=True)
        if event_type == "Πρόβα"
        else None
    )

    col1, col2 = st.columns(2)
    with col1:
        imerominia = st.date_input("Ημερομηνία", format="DD/MM/YYYY")
    with col2:
        titlos = st.text_input("Τίτλος Συναυλίας") if event_type == "Συναυλία" else None

    xoros = st.text_input("Χώρος Διεξαγωγής") if event_type == "Συναυλία" else None
    extra_info = st.text_area("Σχόλια")

    st.divider()
    st.markdown("**Μαζική εισαγωγή συμμετεχόντων και ρεπερτορίου**")

    df_atoma = fetch_atoma().sort_values(
        by=["FoniSortOrder", "Eponymo"], kind="stable", na_position="last"
    )
    atomo_options = {_atomo_label_eponymo_prota(row): row["AtomoID"] for _, row in df_atoma.iterrows()}
    selected_atoma = st.multiselect("Άτομα που συμμετείχαν", options=list(atomo_options.keys()))

    df_kommatia = fetch_kommatia()
    kommati_options = {row["Titlos"]: row["KommatiID"] for _, row in df_kommatia.iterrows()}
    selected_kommatia = st.multiselect("Κομμάτια", options=list(kommati_options.keys()))

    if st.button("💾 Δημιουργία", width="stretch"):
        if event_type == "Συναυλία" and not titlos:
            st.error("Ο τίτλος της συναυλίας είναι υποχρεωτικός.")
            st.stop()

        if event_type == "Πρόβα":
            ekdilosi_id = add_prova(imerominia, extra_info or None, typos_provas)
        else:
            ekdilosi_id = add_synavlia(imerominia, titlos, xoros or None, extra_info or None)

        for label in selected_atoma:
            set_parousia(ekdilosi_id, atomo_options[label], True)
        for label in selected_kommatia:
            add_kommati_se_ekdilosi(ekdilosi_id, kommati_options[label])

        st.success("Η εγγραφή δημιουργήθηκε!")
        st.rerun()


def view_ekdilosi_dialog(ekdilosi_id, row):
    # Ο τίτλος του dialog εξαρτάται από τον τύπο, άρα φτιάχνεται δυναμικά
    is_prova = row["EventType"] == "P"
    title = "🔎 Στοιχεία Πρόβας" if is_prova else "🔎 Στοιχεία Συναυλίας"
    st.dialog(title, width="large")(_view_ekdilosi_body)(ekdilosi_id, row, is_prova)


def _view_ekdilosi_body(ekdilosi_id, row, is_prova):
    st.write(f"**Ημερομηνία:** {format_date(row['Imerominia'])}")
    if is_prova:
        st.write(f"**Τύπος:** {row['TyposProvas']}")
    else:
        st.write(f"**Τίτλος:** {row['Titlos']}")
        if pd.notnull(row["Xoros"]):
            st.write(f"**Χώρος:** {row['Xoros']}")
    if pd.notnull(row["ExtraInfo"]):
        st.write(f"**Σχόλια:** {row['ExtraInfo']}")

    tab_parousies, tab_repertorio = st.tabs(["✅ Συμμετέχοντες", "🎼 Κομμάτια"])

    with tab_parousies:
        df_atoma = fetch_atoma().sort_values(
            by=["FoniSortOrder", "Eponymo"], kind="stable", na_position="last"
        )
        if df_atoma.empty:
            st.info("Δεν υπάρχουν καταχωρημένοι χορωδοί ακόμα.")
        else:
            df_symmetoxes = fetch_symmetoxes(ekdilosi_id)
            parousia_map = dict(zip(df_symmetoxes["AtomoID"], df_symmetoxes["Parousia"]))

            df_view = df_atoma[["AtomoID", "Eponymo", "Onoma"]].copy()
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

            col_save, col_total = st.columns(2)
            with col_total.container(horizontal_alignment="right"):
                st.metric("Σύνολο Συμμετεχόντων", int(edited["Συμμετείχε"].sum()), width="content")
            if col_save.button("💾 Αποθήκευση Συμμετεχόντων", key=f"save_parousies_{ekdilosi_id}"):
                for _, r in edited.iterrows():
                    set_parousia(ekdilosi_id, int(r["AtomoID"]), bool(r["Συμμετείχε"]))
                st.success("Αποθηκεύτηκε!")
                st.rerun()

    with tab_repertorio:
        df_kommatia = fetch_kommatia()
        df_linked = fetch_kommatia_ekdilosis(ekdilosi_id)
        linked_ids = set(df_linked["KommatiID"]) if not df_linked.empty else set()
        available = df_kommatia[~df_kommatia["KommatiID"].isin(linked_ids)]

        if df_linked.empty:
            st.caption("Δεν έχουν προστεθεί κομμάτια ακόμα.")
        else:
            for _, r in df_linked.iterrows():
                col_a, col_b = st.columns([5, 1])
                col_a.write(r["Titlos"])
                if col_b.button("🗑️", key=f"rm_kommati_{ekdilosi_id}_{r['KommatiEkdilosiID']}"):
                    remove_kommati_apo_ekdilosi(ekdilosi_id, int(r["KommatiID"]))
                    st.rerun()

        col_add, col_total = st.columns([3, 1])
        # Nested st.dialog δεν επιτρέπεται, γι' αυτό popover. Το body ακολουθεί το πλάτος του κουμπιού.
        with col_add.popover("➕ Προσθήκη Κομματιού", width="stretch"):
            if available.empty:
                st.caption("Όλα τα διαθέσιμα κομμάτια έχουν ήδη προστεθεί (ή δεν υπάρχουν κομμάτια ακόμα).")
            else:
                to_add = st.selectbox(
                    "Κομμάτι:", available["Titlos"].tolist(), key=f"add_kommati_sb_{ekdilosi_id}"
                )
                if st.button("➕ Προσθήκη", key=f"add_kommati_btn_{ekdilosi_id}"):
                    kommati_id = int(available[available["Titlos"] == to_add]["KommatiID"].iloc[0])
                    add_kommati_se_ekdilosi(ekdilosi_id, kommati_id)
                    st.rerun()
        with col_total.container(horizontal_alignment="right"):
            st.metric("Σύνολο Κομματιών", len(df_linked), width="content")

    st.divider()
    label = "Πρόβας" if is_prova else "Συναυλίας"
    _, col_del = st.columns([2, 1])
    with col_del.popover(f"🗑️ Διαγραφή {label}", width="stretch"):
        st.warning("Η διαγραφή είναι μόνιμη. Να συνεχίσω;")
        if st.button("✔️ Ναι, διαγραφή", key=f"confirm_delete_ekdilosi_{ekdilosi_id}", type="primary"):
            delete_ekdilosi(ekdilosi_id)
            st.rerun()


if st.button("➕ Εισαγωγή Πρόβας / Συναυλίας"):
    new_ekdilosi_dialog()

st.divider()
st.subheader("📋 Λίστα Προβών & Συναυλιών")

df_ekd = fetch_ekdiloseis()


def _ekdiloseis_table(df_type, key, columns, empty_msg, noun):
    """Πίνακας εκδηλώσεων ενός τύπου με φίλτρο μήνα και κουμπί προβολής."""
    if df_type.empty:
        st.info(empty_msg)
        return

    periods = sorted({(d.year, d.month) for d in df_type["Imerominia"]}, reverse=True)
    month_options = ["Όλοι"] + [f"{GREEK_MONTHS[m - 1]} {y}" for y, m in periods]
    month_filter = st.selectbox("Μήνας", month_options, key=f"{key}_month_filter")

    df_shown = df_type
    if month_filter != "Όλοι":
        month_name, year_str = month_filter.rsplit(" ", 1)
        month_num = GREEK_MONTHS.index(month_name) + 1
        year_num = int(year_str)
        df_shown = df_shown[
            (df_shown["Imerominia"].apply(lambda d: d.year) == year_num)
            & (df_shown["Imerominia"].apply(lambda d: d.month) == month_num)
        ]

    df_shown = df_shown.sort_values("Imerominia", ascending=False).reset_index(drop=True)

    table_df = pd.DataFrame({"EkdilosiID": df_shown["EkdilosiID"], **columns(df_shown)})
    table_df["Συμμετέχοντες"] = df_shown["ParousesCount"].astype(int)
    table_df["Κομμάτια"] = df_shown["KommatiaCount"].astype(int)

    event = st.dataframe(
        table_df,
        column_config={
            "EkdilosiID": None,
            "Ημερομηνία": st.column_config.DateColumn("Ημερομηνία", format="DD/MM/YYYY"),
            "Συμμετέχοντες": st.column_config.NumberColumn("👥 Συμμετέχοντες"),
            "Κομμάτια": st.column_config.NumberColumn("🎼 Κομμάτια"),
        },
        hide_index=True,
        width="stretch",
        height=480,
        on_select="rerun",
        selection_mode="single-row",
        key=f"{key}_table",
    )

    selected_rows = event.selection["rows"]
    if selected_rows:
        sel_row = df_shown.iloc[selected_rows[0]]
        if st.button(f"🔍 Εμφάνιση επιλεγμένης {noun}", width="stretch", key=f"{key}_view_btn"):
            view_ekdilosi_dialog(int(sel_row["EkdilosiID"]), sel_row)


if df_ekd.empty:
    st.info("Δεν υπάρχουν ακόμα εκδηλώσεις.")
else:
    col_proves, col_synavlies = st.columns(2)
    with col_proves:
        st.markdown("#### 🎤 Πρόβες")
        _ekdiloseis_table(
            df_ekd[df_ekd["EventType"] == "P"],
            "prova",
            lambda d: {"Ημερομηνία": d["Imerominia"], "Τύπος": d["TyposProvas"]},
            "Δεν υπάρχουν ακόμα πρόβες.",
            "πρόβας",
        )
    with col_synavlies:
        st.markdown("#### 🎭 Συναυλίες")
        _ekdiloseis_table(
            df_ekd[df_ekd["EventType"] == "S"],
            "synavlia",
            lambda d: {
                "Ημερομηνία": d["Imerominia"],
                "Τίτλος": d["Titlos"],
                "Χώρος": d["Xoros"],
            },
            "Δεν υπάρχουν ακόμα συναυλίες.",
            "συναυλίας",
        )
