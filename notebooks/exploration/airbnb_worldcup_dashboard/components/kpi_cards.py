"""Cartes KPI affichées en haut du dashboard."""
from __future__ import annotations

import streamlit as st

from utils.kpis import compute_kpis


def _fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def render_kpi_cards(df) -> None:
    k = compute_kpis(df)

    row1 = st.columns(4)
    row1[0].metric("🏠 Logements analysés", _fmt_int(k["n_logements"]))
    row1[1].metric("💵 Prix médian / nuit", f"{k['prix_median']:.0f} $")
    row1[2].metric("📊 Prix moyen / nuit", f"{k['prix_moyen']:.0f} $")
    row1[3].metric("🛏️ Occupation moyenne", f"{k['occupation_moyenne']:.0f} %")

    row2 = st.columns(4)
    row2[0].metric("📅 Dispo. moyenne", f"{k['dispo_moyenne']:.0f} j/an")
    row2[1].metric("⭐ Avis moyens / logement", f"{k['reviews_moyen']:.0f}")
    row2[2].metric(
        "✅ Quartier le + abordable",
        k["quartier_moins_cher"],
        f"{k['prix_moins_cher']:.0f} $ médian",
        delta_color="off",
    )
    row2[3].metric(
        "🚫 Quartier le + cher",
        k["quartier_plus_cher"],
        f"{k['prix_plus_cher']:.0f} $ médian",
        delta_color="off",
    )

    st.caption(
        f"📌 {_fmt_int(k['n_dispo_longue'])} logements sont disponibles plus de "
        "180 jours par an — une réserve de capacité clé pour absorber l'afflux "
        "de supporters pendant la Coupe du Monde."
    )
