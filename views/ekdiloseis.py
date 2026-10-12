import zlib

import pandas as pd
import streamlit as st

from database import (
    add_kommati_se_ekdilosi,
    add_prova,
    add_synavlia,
    delete_ekdilosi,
    fetch_atoma,
    fetch_atoma_energa,
    fetch_ekdiloseis,
    fetch_kommatia,
    fetch_kommatia_ekdilosis,
    fetch_symmetoxes,
    remove_kommati_apo_ekdilosi,
    set_parousia,
    update_ekdilosi,
)
from utils import GREEK_MONTHS, format_date, open_folder, person_label, select_folder

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

    df_atoma = fetch_atoma_energa().sort_values(
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


def _edit_form(ekdilosi_id, row, is_prova):
    k = f"edit_{ekdilosi_id}"
    imerominia = st.date_input("Ημερομηνία", value=row["Imerominia"], format="DD/MM/YYYY", key=f"{k}_date")
    typos_options = ["Κανονική", "Προγενική", "Γενική"]
    if is_prova:
        current = row["TyposProvas"]
        typos = st.radio(
            "Τύπος Πρόβας",
            typos_options,
            index=typos_options.index(current) if current in typos_options else 0,
            horizontal=True,
            key=f"{k}_typos",
        )
    else:
        titlos = st.text_input("Τίτλος Συναυλίας", value=row["Titlos"] or "", key=f"{k}_titlos")
        xoros = st.text_input(
            "Χώρος Διεξαγωγής", value=row["Xoros"] if pd.notnull(row["Xoros"]) else "", key=f"{k}_xoros"
        )
        db_folder = row["FolderSynavlias"] if pd.notnull(row["FolderSynavlias"]) else ""
        # Η τιμή της βάσης μπαίνει στο key, ώστε το πεδίο να ξαναρχικοποιείται όποτε αλλάζει (όχι μπαγιάτικη τιμή).
        folder_key = f"{k}_folder_{zlib.crc32(db_folder.encode())}"
        if folder_key not in st.session_state:
            st.session_state[folder_key] = db_folder

        def _pick_folder():
            # Callback: τρέχει πριν το text_input ξαναδημιουργηθεί, άρα επιτρέπεται η εγγραφή στο key του.
            path, err = select_folder(initialdir=st.session_state[folder_key] or None)
            if path:
                st.session_state[folder_key] = path
            elif err:
                st.toast(f"Δεν ήταν δυνατή η επιλογή φακέλου: {err}")

        folder = st.text_input("Φάκελος Συναυλίας", key=folder_key)
        st.button("📁 Επιλογή Φακέλου", key=f"{k}_pick_folder", on_click=_pick_folder)
    extra_info = st.text_area(
        "Σχόλια", value=row["ExtraInfo"] if pd.notnull(row["ExtraInfo"]) else "", key=f"{k}_extra"
    )

    if st.button("💾 Αποθήκευση Αλλαγών", key=f"{k}_save", type="primary"):
        if is_prova:
            update_ekdilosi(ekdilosi_id, imerominia, extra_info or None, typos_provas=typos)
        else:
            if not titlos:
                st.error("Ο τίτλος της συναυλίας είναι υποχρεωτικός.")
                st.stop()
            update_ekdilosi(ekdilosi_id, imerominia, extra_info or None, titlos=titlos, xoros=xoros or None,
                            folder=folder.strip() or None)
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
        if pd.notnull(row["FolderSynavlias"]):
            col_folder, col_open = st.columns([4, 1])
            col_folder.write(f"**Φάκελος Συναυλίας:** {row['FolderSynavlias']}")
            if col_open.button("📂 Άνοιγμα", key=f"open_folder_{ekdilosi_id}"):
                ok, err = open_folder(row["FolderSynavlias"])
                if not ok:
                    st.error(err)
    if pd.notnull(row["ExtraInfo"]):
        st.write(f"**Σχόλια:** {row['ExtraInfo']}")

    tab_parousies, tab_repertorio = st.tabs(["✅ Συμμετέχοντες", "🎼 Κομμάτια"])

    with tab_parousies:
        df_symmetoxes = fetch_symmetoxes(ekdilosi_id)
        participant_ids = set(df_symmetoxes.loc[df_symmetoxes["Parousia"] == True, "AtomoID"])  # noqa: E712
        df_atoma = fetch_atoma().sort_values(
            by=["FoniSortOrder", "Eponymo"], kind="stable", na_position="last"
        )

        # Προσθήκη: μόνο ενεργοί χορωδοί που δεν συμμετέχουν ήδη
        df_available = df_atoma[
            df_atoma["ImerominiaApoxorisis"].isnull() & ~df_atoma["AtomoID"].isin(participant_ids)
        ]
        atomo_options = {_atomo_label_eponymo_prota(r): int(r["AtomoID"]) for _, r in df_available.iterrows()}
        selected_atoma = st.multiselect(
            "Άτομα που συμμετείχαν", options=list(atomo_options.keys()), key=f"add_atoma_ms_{ekdilosi_id}"
        )
        if st.button("➕ Προσθήκη Συμμετεχόντων", key=f"add_atoma_btn_{ekdilosi_id}", disabled=not selected_atoma):
            for label in selected_atoma:
                set_parousia(ekdilosi_id, atomo_options[label], True)
            st.rerun()

        # Πίνακας: μόνο οι συμμετέχοντες
        df_part = df_atoma[df_atoma["AtomoID"].isin(participant_ids)].reset_index(drop=True)
        if df_part.empty:
            st.caption("Δεν έχουν προστεθεί συμμετέχοντες ακόμα.")
        else:
            event = st.dataframe(
                df_part[["Eponymo", "Onoma", "FoniDescr"]],
                column_config={
                    "Eponymo": "Επώνυμο",
                    "Onoma": "Όνομα",
                    "FoniDescr": "Φωνή",
                },
                hide_index=True,
                width="stretch",
                on_select="rerun",
                selection_mode="multi-row",
                key=f"view_parousies_{ekdilosi_id}",
            )
            selected_rows = event.selection["rows"]
            if st.button(
                "🗑️ Αφαίρεση επιλεγμένων", key=f"rm_parousies_{ekdilosi_id}", disabled=not selected_rows
            ):
                for i in selected_rows:
                    set_parousia(ekdilosi_id, int(df_part.loc[i, "AtomoID"]), False)
                st.rerun()

        with st.container(horizontal_alignment="right"):
            st.metric("Σύνολο Συμμετεχόντων", len(df_part), width="content")

    with tab_repertorio:
        df_kommatia = fetch_kommatia()
        df_linked = fetch_kommatia_ekdilosis(ekdilosi_id)
        linked_ids = set(df_linked["KommatiID"]) if not df_linked.empty else set()
        available = df_kommatia[~df_kommatia["KommatiID"].isin(linked_ids)]

        kommati_options = {r["Titlos"]: int(r["KommatiID"]) for _, r in available.iterrows()}
        selected_kommatia = st.multiselect(
            "Κομμάτια", options=list(kommati_options.keys()), key=f"add_kommatia_ms_{ekdilosi_id}"
        )
        if st.button("➕ Προσθήκη Κομματιών", key=f"add_kommatia_btn_{ekdilosi_id}", disabled=not selected_kommatia):
            for label in selected_kommatia:
                add_kommati_se_ekdilosi(ekdilosi_id, kommati_options[label])
            st.rerun()

        if df_linked.empty:
            st.caption("Δεν έχουν προστεθεί κομμάτια ακόμα.")
        else:
            for _, r in df_linked.iterrows():
                col_a, col_b = st.columns([5, 1])
                col_a.write(r["Titlos"])
                if col_b.button("🗑️", key=f"rm_kommati_{ekdilosi_id}_{r['KommatiEkdilosiID']}"):
                    remove_kommati_apo_ekdilosi(ekdilosi_id, int(r["KommatiID"]))
                    st.rerun()

        with st.container(horizontal_alignment="right"):
            st.metric("Σύνολο Κομματιών", len(df_linked), width="content")

    st.divider()
    label = "Πρόβας" if is_prova else "Συναυλίας"
    # Το body του popover ακολουθεί το πλάτος του κουμπιού, γι' αυτό πλήρες πλάτος σε δική τους γραμμή.
    with st.popover("✏️ Επεξεργασία", width="stretch"):
        _edit_form(ekdilosi_id, row, is_prova)
    with st.popover(f"🗑️ Διαγραφή {label}", width="stretch"):
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
                "Φάκελος": d["FolderSynavlias"],
            },
            "Δεν υπάρχουν ακόμα συναυλίες.",
            "συναυλίας",
        )
