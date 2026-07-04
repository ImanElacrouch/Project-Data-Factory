"""Barre de navigation horizontale (vrais boutons, largeurs égales)."""
from __future__ import annotations

import streamlit as st

SECTIONS = [
    ("chiffres", "pages/chiffres_cles.py", "📊 Chiffres clés"),
    ("carte", "pages/carte.py", "🗺️ Carte interactive"),
    ("prix", "pages/prix.py", "💰 Prix & prédiction"),
    ("quartiers", "pages/quartiers.py", "🏆 Classement"),
    ("reco", "pages/recommandations.py", "📖 Recommandations"),
]


def render_topnav(include_home: bool = True) -> None:
    items = []
    if include_home:
        items.append(("home", "pages/accueil.py", "🏠 Accueil"))
    items += SECTIONS

    cols = st.columns(len(items), gap="medium")
    for col, (key, path, label) in zip(cols, items):
        with col:
            if st.button(label, key=f"nav_{key}", width="stretch"):
                st.switch_page(path)
    st.write("")
