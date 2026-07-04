"""Chiffres clés : KPI métier + 2 repères essentiels."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from components.topnav import render_topnav
from components.kpi_cards import render_kpi_cards
from utils.data_loader import load_data
from utils.kpis import prix_par_arrondissement, prix_par_type
from utils.theme import setup_page, BOROUGH_COLORS, ROOM_TYPE_FR, PRICE_SCALE

setup_page()
render_topnav()
df = load_data()
dff = df

st.header("📊 Le marché Airbnb new-yorkais en un coup d’œil")

if dff.empty:
    st.warning("Aucun logement ne correspond aux filtres.")
    st.stop()

render_kpi_cards(dff)
st.divider()

c1, c2 = st.columns(2)
with c1:
    st.markdown("##### Manhattan coûte près du double des autres arrondissements")
    par_arr = prix_par_arrondissement(dff)
    fig = px.bar(par_arr, x="prix_median", y="neighbourhood_group", orientation="h",
                 color="neighbourhood_group", color_discrete_map=BOROUGH_COLORS,
                 text="prix_median",
                 labels={"prix_median": "Prix médian / nuit ($)", "neighbourhood_group": ""})
    fig.update_traces(texttemplate="%{text:.0f} $", textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False, height=300)
    st.plotly_chart(fig, width="stretch")

with c2:
    st.markdown("##### Une chambre partagée coûte 2 à 3× moins cher qu'un logement entier")
    par_type = prix_par_type(dff).copy()
    par_type["type_fr"] = par_type["room_type"].map(ROOM_TYPE_FR).fillna(par_type["room_type"])
    fig2 = px.bar(par_type, x="prix_median", y="type_fr", orientation="h",
                  color="prix_median", color_continuous_scale=PRICE_SCALE, text="prix_median",
                  labels={"prix_median": "Prix médian / nuit ($)", "type_fr": ""})
    fig2.update_traces(texttemplate="%{text:.0f} $", textposition="outside", cliponaxis=False)
    fig2.update_layout(showlegend=False, height=300, coloraxis_showscale=False)
    st.plotly_chart(fig2, width="stretch")

st.markdown(
    """<div class="insight">💡 <b>À retenir :</b> viser une <b>chambre privée hors de
    Manhattan</b> divise la facture par deux tout en restant proche du métro.</div>""",
    unsafe_allow_html=True,
)