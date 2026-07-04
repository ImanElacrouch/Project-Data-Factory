"""Page Classement : quartiers les moins/plus chers et meilleur compromis."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from components.topnav import render_topnav
from utils.data_loader import load_data
from utils.kpis import top_quartiers, score_compromis
from utils.theme import setup_page, PITCH_GREEN, RED, PRICE_SCALE

setup_page()
render_topnav()
df = load_data()
dff = df

st.header("🏆 Classement des quartiers")
st.caption("Quartiers d'au moins 30 annonces, pour des moyennes fiables.")

if dff.empty:
    st.warning("Aucun logement ne correspond aux filtres.")
    st.stop()

c1, c2 = st.columns(2)

with c1:
    st.markdown("##### ✅ Top 10 des quartiers les plus abordables")
    cheap = top_quartiers(dff, n=10, cheapest=True)
    fig = px.bar(
        cheap.sort_values("prix_median", ascending=False),
        x="prix_median", y="neighbourhood", orientation="h",
        color_discrete_sequence=[PITCH_GREEN], text="prix_median",
        hover_data={"neighbourhood_group": True, "n": True},
        labels={"prix_median": "Prix médian / nuit ($)", "neighbourhood": ""},
    )
    fig.update_traces(texttemplate="%{text:.0f} $", textposition="outside",
                      cliponaxis=False)
    fig.update_layout(height=420)
    st.plotly_chart(fig, width="stretch")

with c2:
    st.markdown("##### 🚫 Top 10 des quartiers les plus chers (à éviter)")
    pricey = top_quartiers(dff, n=10, cheapest=False)
    fig2 = px.bar(
        pricey.sort_values("prix_median", ascending=True),
        x="prix_median", y="neighbourhood", orientation="h",
        color_discrete_sequence=[RED], text="prix_median",
        hover_data={"neighbourhood_group": True, "n": True},
        labels={"prix_median": "Prix médian / nuit ($)", "neighbourhood": ""},
    )
    fig2.update_traces(texttemplate="%{text:.0f} $", textposition="outside",
                       cliponaxis=False)
    fig2.update_layout(height=420)
    st.plotly_chart(fig2, width="stretch")

st.divider()

# --- Score compromis ------------------------------------------------------
st.markdown("##### 🎯 Le meilleur compromis prix / disponibilité / popularité")
st.caption(
    "Score = 50 % prix bas + 30 % disponibilité + 20 % popularité (avis). "
    "Plus le score est élevé, meilleur est le rapport qualité-prix pour un séjour Coupe du Monde."
)
sc = score_compromis(dff).head(12)
fig3 = px.bar(
    sc.sort_values("score"),
    x="score", y="neighbourhood", orientation="h",
    color="prix_median", color_continuous_scale=PRICE_SCALE,
    text="prix_median",
    hover_data={"neighbourhood_group": True, "dispo_moyenne": ":.0f",
                "reviews_moyen": ":.0f", "n": True, "prix_median": ":.0f"},
    labels={"score": "Score compromis", "neighbourhood": "",
            "prix_median": "Prix médian ($)"},
)
fig3.update_traces(texttemplate="%{text:.0f} $", textposition="outside",
                   cliponaxis=False)
fig3.update_layout(height=460, coloraxis_colorbar_title="Prix ($)")
st.plotly_chart(fig3, width="stretch")

if not sc.empty:
    best = sc.iloc[0]
    st.markdown(
        f"""<div class="insight">🏅 <b>{best['neighbourhood']}</b>
        ({best['neighbourhood_group']}) ressort comme le meilleur compromis :
        prix médian de <b>{best['prix_median']:.0f} $</b>, disponibilité moyenne
        de <b>{best['dispo_moyenne']:.0f} jours/an</b> et
        <b>{best['reviews_moyen']:.0f} avis</b> en moyenne par logement.</div>""",
        unsafe_allow_html=True,
    )