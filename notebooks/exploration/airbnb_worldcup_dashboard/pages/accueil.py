"""Page de garde : l'idée du projet, simple et visuelle."""
from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import streamlit as st

from utils.theme import setup_page
from components.topnav import render_topnav

setup_page()

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def _find(*patterns: str):
    """Renvoie le premier fichier d'asset correspondant à l'un des motifs."""
    for pat in patterns:
        hits = sorted(ASSETS.glob(pat))
        if hits:
            return hits[0]
    return None


def _img_tag(path, height: int) -> str:
    """Construit une balise <img> en base64 (ou chaîne vide si absent)."""
    if not path:
        return ""
    data = base64.b64encode(Path(path).read_bytes()).decode()
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    return f'<img src="data:{mime};base64,{data}" style="height:{height}px;width:auto;">'


# --- Logos en haut : Airbnb à gauche, Coupe du Monde à droite ---------------
# Dépose tes fichiers dans assets/ (ex. airbnb.png et worldcup.png) : ils
# s'afficheront automatiquement ici. Sans fichiers, la rangée reste vide.
airbnb_logo = _find("airbnb*.png", "airbnb*.jpg", "airbnb*.jpeg", "airbnb*.webp", "airbnb*.svg")
wc_logo = _find("worldcup*.*", "world_cup*.*", "wc*.*", "2026*.*", "fifa*.*", "coupe*.*")

st.markdown(
    f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                margin:4px 2px 16px;">
      <div>{_img_tag(airbnb_logo, 56)}</div>
      <div>{_img_tag(wc_logo, 90)}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Bandeau principal : l'idée en une phrase -------------------------------
st.markdown(
    """
    <div class="hero">
      <span class="badge">⚽ FIFA World Cup 2026 · New York / New Jersey</span>
      <h1>Se loger à New York pendant la Coupe du Monde, sans se ruiner</h1>
      <p>Le MetLife Stadium accueille 8 matchs jusqu'à la finale du 19 juillet 2026.
      Des milliers de supporters arrivent : <b>où trouver un logement Airbnb abordable
      et de qualité ?</b> Ce tableau de bord répond à la question.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

# --- Boutons de navigation (sous le bandeau) --------------------------------
render_topnav(include_home=False)
