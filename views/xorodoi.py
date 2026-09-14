import pandas as pd
import streamlit as st

from database import add_atomo, delete_atomo, fetch_atoma, fetch_foni, update_atomo

st.title("🧑‍🤝‍🧑 Χορωδοί")


def _clean(value):
    return None if pd.isnull(value) else value


df_foni = fetch_foni()
foni_options = {
    (row["FoniDescr"] or row["FoniSynt"]): row["FoniID"] for _, row in df_foni.iterrows()
}
foni_id_to_label = {v: k for k, v in foni_options.items()}

df_atoma = fetch_atoma()
df_atoma["Φωνή"] = df_atoma["FoniID"].map(foni_id_to_label)
df_atoma = df_atoma.sort_values(
    by="FoniSortOrder", kind="stable", na_position="last"
).reset_index(drop=True)

foni_filter = st.selectbox("Φίλτρο φωνής", ["Όλες"] + list(foni_options.keys()))
df_shown = df_atoma if foni_filter == "Όλες" else df_atoma[df_atoma["Φωνή"] == foni_filter]
df_shown = df_shown.reset_index(drop=True)

display_cols = ["AtomoID", "Onoma", "Eponymo", "Φωνή", "KinitoTilefono", "StatheroTilefono", "Email"]

edited = st.data_editor(
    df_shown[display_cols],
    column_config={
        "AtomoID": None,
        "Onoma": st.column_config.TextColumn("Όνομα", required=True),
        "Eponymo": st.column_config.TextColumn("Επώνυμο", required=True),
        "Φωνή": st.column_config.SelectboxColumn("Φωνή", options=list(foni_options.keys())),
        "KinitoTilefono": st.column_config.TextColumn("Κινητό"),
        "StatheroTilefono": st.column_config.TextColumn("Σταθερό"),
        "Email": st.column_config.TextColumn("Email"),
    },
    num_rows="dynamic",
    width="stretch",
    key="atoma_editor",
)

if st.button("💾 Αποθήκευση Αλλαγών"):
    current_ids = set(df_shown["AtomoID"])
    edited_ids = set(edited["AtomoID"].dropna())

    for atomo_id in current_ids - edited_ids:
        delete_atomo(int(atomo_id))

    for _, row in edited.iterrows():
        if not row["Eponymo"] or not row["Onoma"]:
            continue
        foni_id = foni_options.get(row["Φωνή"])
        args = (row["Eponymo"], row["Onoma"], _clean(row["KinitoTilefono"]),
                 _clean(row["StatheroTilefono"]), _clean(row["Email"]), foni_id)
        if pd.isnull(row["AtomoID"]):
            add_atomo(*args)
        else:
            update_atomo(int(row["AtomoID"]), *args)

    st.success("Οι αλλαγές αποθηκεύτηκαν!")
    st.rerun()
