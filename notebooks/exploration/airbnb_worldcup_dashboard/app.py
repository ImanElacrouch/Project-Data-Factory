"""
Dashboard Airbnb NYC — « Où se loger pour la Coupe du Monde 2026 ? »
Point d'entrée + navigation. Lancer avec : streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Airbnb NYC · Coupe du Monde 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

pages = [
    st.Page("pages/accueil.py",         title="Accueil",            icon="🏟️", default=True),
    st.Page("pages/chiffres_cles.py",   title="Chiffres clés",      icon="📊"),
    st.Page("pages/carte.py",           title="Carte interactive",  icon="🗺️"),
    st.Page("pages/prix.py",            title="Prix & prédiction",  icon="💰"),
    st.Page("pages/quartiers.py",       title="Classement",         icon="🏆"),
    st.Page("pages/recommandations.py", title="Recommandations",    icon="📖"),
]

# Menu latéral masqué : la navigation se fait par la barre du haut
st.navigation(pages, position="hidden").run()
