import streamlit as st

st.set_page_config(page_title="ChoirApp", page_icon="🎵", layout="wide")

pages = {
    "Χορωδία": [
        st.Page("views/xorodoi.py", title="Χορωδοί", icon="🧑‍🤝‍🧑"),
        st.Page("views/kommatia.py", title="Μουσικά Κομμάτια", icon="🎼"),
        st.Page("views/ekdiloseis.py", title="Πρόβες & Συναυλίες", icon="📅"),
    ],
    "Ρυθμίσεις": [
        st.Page("views/anafora_data.py", title="Στοιχεία Αναφοράς", icon="⚙️"),
    ],
}

nav = st.navigation(pages)
nav.run()
