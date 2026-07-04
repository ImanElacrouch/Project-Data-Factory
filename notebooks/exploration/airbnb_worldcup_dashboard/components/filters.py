"""
Filtres interactifs partagés (barre latérale).

Appelé en haut de chaque page : renvoie le DataFrame filtré selon les
choix de l'utilisateur. Les états sont conservés entre les pages grâce
aux `key` de session.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.data_loader import get_bounds


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    bounds = get_bounds(df)

    with st.sidebar:
        st.markdown("### 🎚️ Filtres")
        st.caption("Affinez la recherche de logement pour la Coupe du Monde.")

        arrondissements = sorted(df["neighbourhood_group"].unique())
        sel_arr = st.multiselect(
            "Arrondissement",
            options=arrondissements,
            default=arrondissements,
            key="f_arr",
        )

        df_arr = df[df["neighbourhood_group"].isin(sel_arr)] if sel_arr else df

        quartiers = sorted(df_arr["neighbourhood"].unique())
        sel_q = st.multiselect(
            "Quartier (optionnel)",
            options=quartiers,
            default=[],
            key="f_q",
            help="Laissez vide pour inclure tous les quartiers des arrondissements choisis.",
        )

        types = sorted(df["room_type"].unique())
        sel_type = st.multiselect(
            "Type de logement",
            options=types,
            default=types,
            key="f_type",
        )

        prix_max = st.slider(
            "Prix maximum / nuit ($)",
            min_value=bounds["price_min"],
            max_value=bounds["price_max"],
            value=min(250, bounds["price_max"]),
            step=10,
            key="f_prix",
        )

        dispo_min = st.slider(
            "Disponibilité minimale (jours/an)",
            min_value=0,
            max_value=365,
            value=0,
            step=15,
            key="f_dispo",
            help="Nombre minimum de jours où le logement est ouvert à la réservation.",
        )

        occ_min = st.slider(
            "Taux d'occupation minimum (%)",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
            key="f_occ",
            help="Filtre les logements les plus utilisés (gage de fiabilité).",
        )

        if st.button("♻️ Réinitialiser les filtres", width="stretch"):
            for k in ["f_arr", "f_q", "f_type", "f_prix", "f_dispo", "f_occ"]:
                st.session_state.pop(k, None)
            st.rerun()

    # --- Application des filtres ---
    mask = pd.Series(True, index=df.index)
    if sel_arr:
        mask &= df["neighbourhood_group"].isin(sel_arr)
    if sel_q:
        mask &= df["neighbourhood"].isin(sel_q)
    if sel_type:
        mask &= df["room_type"].isin(sel_type)
    mask &= df["price"] <= prix_max
    mask &= df["availability_365"] >= dispo_min
    mask &= df["occupancy_rate"] >= occ_min / 100

    filtered = df[mask].copy()

    with st.sidebar:
        st.divider()
        st.metric("Logements correspondants", f"{len(filtered):,}".replace(",", " "))
        if len(df):
            st.progress(len(filtered) / len(df))

    return filtered
