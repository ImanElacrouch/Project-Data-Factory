"""Page Carte : localisation des logements et densité des prix."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.topnav import render_topnav
from utils.data_loader import load_data
from utils.theme import setup_page, PRICE_SCALE, ROOM_TYPE_FR

# MetLife Stadium (East Rutherford, NJ) — finale Coupe du Monde, 19 juillet 2026
STADE = dict(lat=40.8136, lon=-74.0744, nom="MetLife Stadium")
TIMES_SQUARE = dict(lat=40.7580, lon=-73.9855, nom="Times Square")

setup_page()
render_topnav()
df = load_data()
dff = df

st.header("🗺️ Carte interactive de New York")
st.caption(
    "Chaque point est un logement. La couleur indique le prix : "
    "vert = abordable, rouge = cher. Les repères 🏟️ MetLife Stadium et "
    "📍 Times Square aident à se situer. Zoomez et survolez pour explorer."
)

if dff.empty:
    st.warning("Aucun logement ne correspond aux filtres.")
    st.stop()

mode = st.radio(
    "Type de carte",
    ["Logements (points)", "Densité des prix (heatmap)"],
    horizontal=True,
)

center = dict(lat=dff["latitude"].mean(), lon=dff["longitude"].mean())

if mode.startswith("Logements"):
    # Échantillonnage pour garder la carte fluide au-delà de ~6000 points.
    plot_df = dff.sample(min(6000, len(dff)), random_state=42).copy()
    plot_df["type_fr"] = plot_df["room_type"].map(ROOM_TYPE_FR).fillna(plot_df["room_type"])
    fig = px.scatter_map(
        plot_df,
        lat="latitude",
        lon="longitude",
        color="price",
        range_color=(plot_df["price"].quantile(0.02), plot_df["price"].quantile(0.95)),
        color_continuous_scale=PRICE_SCALE,
        size_max=8,
        zoom=10,
        center=center,
        hover_name="neighbourhood",
        hover_data={
            "type_fr": True, "price": ":.0f", "availability_365": True,
            "latitude": False, "longitude": False,
        },
        labels={"price": "Prix ($)", "type_fr": "Type",
                "availability_365": "Dispo (j/an)"},
        opacity=0.6,
    )
    fig.update_layout(coloraxis_colorbar_title="Prix / nuit ($)")
    note = (
        f"{len(plot_df):,}".replace(",", " ")
        + f" logements affichés sur {len(dff):,}".replace(",", " ")
        + " (échantillon pour la fluidité)."
    )
else:
    fig = px.density_map(
        dff,
        lat="latitude",
        lon="longitude",
        z="price",
        radius=12,
        center=center,
        zoom=10,
        color_continuous_scale=PRICE_SCALE,
        labels={"price": "Prix ($)"},
    )
    fig.update_layout(coloraxis_colorbar_title="Prix / nuit ($)")
    note = "Les zones rouges concentrent les logements les plus chers (cœur de Manhattan)."

fig.update_layout(map_style="carto-positron", height=620,
                  margin=dict(l=0, r=0, t=10, b=0))

# --- Repères (halo blanc + marqueur) placés AU-DESSUS des points -----------
def _ajoute_repere(lat, lon, couleur, label, hover):
    # halo blanc dessous pour faire ressortir le repère
    fig.add_trace(go.Scattermap(
        lat=[lat], lon=[lon], mode="markers",
        marker=dict(size=30, color="white"),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scattermap(
        lat=[lat], lon=[lon], mode="markers+text",
        marker=dict(size=22, color=couleur),
        text=[label], textposition="top center",
        textfont=dict(size=15, color=couleur),
        hovertext=[hover], hoverinfo="text", showlegend=False,
    ))

_ajoute_repere(STADE["lat"], STADE["lon"], "#0F2A4A", "🏟️ MetLife Stadium",
               "🏟️ MetLife Stadium — Finale Coupe du Monde, 19 juillet 2026")
_ajoute_repere(TIMES_SQUARE["lat"], TIMES_SQUARE["lon"], "#7C3AED", "📍 Times Square",
               "📍 Times Square — cœur touristique de Manhattan")

st.plotly_chart(fig, width="stretch")

st.markdown(
    f"""<div class="insight">📍 {note} Le dégradé met immédiatement en évidence
    le contraste entre le sud de Manhattan (cher) et les arrondissements
    périphériques, bien plus accessibles.</div>""",
    unsafe_allow_html=True,
)