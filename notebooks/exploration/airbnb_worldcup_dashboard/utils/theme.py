"""
Identité visuelle du dashboard — thème "Coupe du Monde 2026 à New York".

Palette sobre et professionnelle (vert gazon + bleu nuit + accents),
réutilisée par toutes les pages pour garantir la cohérence visuelle
exigée dans la grille de notation.
"""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

# --- Palette ----------------------------------------------------------------
PITCH_GREEN = "#16A34A"   # vert gazon (accent principal)
NIGHT_BLUE = "#0F2A4A"    # bleu nuit (texte / structure)
SKY = "#2563EB"           # bleu
AMBER = "#F59E0B"         # ambre (alertes prix élevés)
RED = "#DC2626"           # rouge (à éviter)
TEAL = "#0D9488"
SLATE = "#64748B"
LIGHT = "#F1F5F9"

# Échelle continue prix : du vert (abordable) au rouge (cher).
PRICE_SCALE = [
    [0.0, "#16A34A"],
    [0.35, "#84CC16"],
    [0.6, "#F59E0B"],
    [0.8, "#F97316"],
    [1.0, "#DC2626"],
]

# Couleurs fixes par arrondissement (lisibilité / mémorisation).
BOROUGH_COLORS = {
    "Manhattan": "#DC2626",
    "Brooklyn": "#2563EB",
    "Queens": "#16A34A",
    "Bronx": "#F59E0B",
    "Staten Island": "#7C3AED",
}

ROOM_TYPE_FR = {
    "Entire home/apt": "Logement entier",
    "Private room": "Chambre privée",
    "Shared room": "Chambre partagée",
}


def _base_template() -> go.layout.Template:
    tpl = go.layout.Template()
    tpl.layout.font = dict(
        family="Inter, Segoe UI, system-ui, sans-serif",
        size=14,
        color=NIGHT_BLUE,
    )
    tpl.layout.paper_bgcolor = "rgba(0,0,0,0)"
    tpl.layout.plot_bgcolor = "rgba(0,0,0,0)"
    tpl.layout.colorway = [PITCH_GREEN, SKY, AMBER, TEAL, RED, "#7C3AED"]
    tpl.layout.title = dict(font=dict(size=18, color=NIGHT_BLUE), x=0.0, xanchor="left")
    tpl.layout.xaxis = dict(gridcolor="#E2E8F0", zerolinecolor="#E2E8F0")
    tpl.layout.yaxis = dict(gridcolor="#E2E8F0", zerolinecolor="#E2E8F0")
    tpl.layout.margin = dict(l=10, r=10, t=50, b=10)
    return tpl


def register_theme() -> None:
    """À appeler une fois par page pour activer le thème Plotly."""
    pio.templates["worldcup"] = _base_template()
    pio.templates.default = "worldcup"


def inject_css() -> None:
    """Injecte la feuille de style maison (idempotent par page)."""
    import streamlit as st
    from pathlib import Path

    css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
    if css_path.is_file():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def setup_page() -> None:
    """Bootstrap commun à toutes les pages : thème Plotly + CSS."""
    register_theme()
    inject_css()
