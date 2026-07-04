"""Prix & prédiction : l'essentiel, plus un estimateur de prix."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from components.topnav import render_topnav
from utils.data_loader import load_data
from utils.predict import load_model, predict_price
from utils.theme import setup_page, PRICE_SCALE, ROOM_TYPE_FR

setup_page()
render_topnav()
df = load_data()
dff = df

st.header("💰 Prix & prédiction")

if dff.empty:
    st.warning("Aucun logement ne correspond aux filtres.")
    st.stop()

# --- 1. Heatmap prix : arrondissement x type -------------------------------
st.markdown("##### Combien coûte chaque type de logement, par arrondissement ?")
d = dff.copy()
d["type_fr"] = d["room_type"].map(ROOM_TYPE_FR).fillna(d["room_type"])
pivot = d.pivot_table(index="neighbourhood_group", columns="type_fr",
                      values="price", aggfunc="median")
fig = px.imshow(pivot, text_auto=".0f", color_continuous_scale=PRICE_SCALE,
                aspect="auto", labels=dict(color="Prix médian ($)", x="", y=""))
fig.update_layout(height=320, coloraxis_colorbar_title="Prix ($)")
st.plotly_chart(fig, width="stretch")

# --- 2. Distribution des prix ----------------------------------------------
st.markdown("##### La majorité des logements se situe sous 200 $/nuit")
figd = px.histogram(dff[dff["price"] <= 500], x="price", nbins=40,
                    color_discrete_sequence=["#16A34A"],
                    labels={"price": "Prix / nuit ($)"})
med = dff["price"].median()
figd.add_vline(x=med, line_dash="dash", line_color="#DC2626",
               annotation_text=f"Médiane {med:.0f} $", annotation_position="top")
figd.update_layout(height=300, yaxis_title="Nombre de logements")
st.plotly_chart(figd, width="stretch")

st.divider()

# --- 3. Prédiction de prix (modèle Gradient Boosting) ----------------------
st.markdown("### 🔮 Prédire le prix d'un logement")
st.caption("Modèle de Machine Learning (Gradient Boosting) entraîné sur les "
           "données Gold, méthodologie de l'équipe Data Science : cible "
           "log(prix).")

bundle = load_model()
if bundle is None:
    st.warning(
        "Modèle introuvable. Lancez d'abord l'entraînement : "
        "`python train_model.py` (génère models/price_model.joblib)."
    )
else:
    cc1, cc2, cc3 = st.columns(3)
    arr = cc1.selectbox("Arrondissement", sorted(df["neighbourhood_group"].unique()))
    # Les quartiers proposés dépendent de l'arrondissement choisi (cascade)
    quartiers = sorted(df[df["neighbourhood_group"] == arr]["neighbourhood"].unique())
    quartier = cc2.selectbox("Quartier", quartiers)
    rt = cc3.selectbox("Type de logement", sorted(df["room_type"].unique()),
                       format_func=lambda x: ROOM_TYPE_FR.get(x, x))

    nuits = st.number_input("Nombre de nuits de séjour", min_value=1,
                            max_value=60, value=7, step=1)

    # Disponibilité non demandée à l'utilisateur : on utilise une valeur
    # représentative (médiane du jeu de données) pour le modèle.
    dispo = int(df["availability_365"].median())

    res = predict_price(bundle, quartier, rt, dispo)

    m1, m2, m3 = st.columns(3)
    m1.metric("💵 Prix prédit / nuit", f"{res['prix']:.0f} $")
    m2.metric("Fourchette basse", f"{res['bas']:.0f} $")
    m3.metric("Fourchette haute", f"{res['haut']:.0f} $")

    total = res["prix"] * nuits
    total_bas = res["bas"] * nuits
    total_haut = res["haut"] * nuits
    st.metric(f"🧳 Coût total estimé pour {nuits} nuits", f"{total:,.0f} $".replace(",", " "),
              f"entre {total_bas:,.0f} $ et {total_haut:,.0f} $".replace(",", " "),
              delta_color="off")
