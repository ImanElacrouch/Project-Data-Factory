"""Page Recommandations : storytelling en 5 étapes + tableau final."""
from __future__ import annotations

import streamlit as st

from components.topnav import render_topnav
from utils.data_loader import load_data
from utils.kpis import compute_kpis, score_compromis
from utils.theme import setup_page, ROOM_TYPE_FR

setup_page()
render_topnav()
df = load_data()
dff = df

st.header("📖 De la donnée à la décision")
st.caption("L'histoire que racontent les données, en cinq étapes.")

if dff.empty:
    st.warning("Aucun logement ne correspond aux filtres.")
    st.stop()

k = compute_kpis(dff)

steps = [
    ("Le contexte",
     "Du 13 juin au 19 juillet 2026, le MetLife Stadium (New York / New Jersey) "
     "accueille 8 matchs de la Coupe du Monde, dont la finale. La région attend "
     "plus d'un million de visiteurs liés au tournoi."),
    ("Une demande de logement qui explose",
     "Hôtels saturés et prix des billets/transports en forte hausse poussent "
     "les supporters vers les locations courte durée. La question n'est plus "
     "« où dormir ? » mais « où dormir sans se ruiner ? »."),
    ("Ce que disent les données Airbnb",
     f"Sur {k['n_logements']:,}".replace(",", " ") +
     f" logements analysés, le prix médian est de {k['prix_median']:.0f} $/nuit, "
     f"mais Manhattan tire la moyenne vers le haut tandis que les arrondissements "
     f"périphériques restent abordables."),
    ("Les quartiers du meilleur compromis",
     f"En croisant prix, disponibilité et avis, des quartiers comme "
     f"{k['quartier_moins_cher']} offrent un excellent rapport qualité-prix "
     f"(≈ {k['prix_moins_cher']:.0f} $ médian), loin des "
     f"{k['prix_plus_cher']:.0f} $ de {k['quartier_plus_cher']}."),
    ("La recommandation",
     "Pour un séjour réussi et économique : privilégier une chambre privée "
     "hors de Manhattan, dans un quartier bien desservi par le métro, "
     "réservé tôt pour sécuriser la disponibilité."),
]

for i, (title, body) in enumerate(steps, 1):
    st.markdown(
        f"""<div class="step"><span class="num">{i}</span>
        <b>{title}</b><br>{body}</div>""",
        unsafe_allow_html=True,
    )

st.divider()

# --- Tableau de recommandations final ------------------------------------
st.subheader("🎯 Nos 8 quartiers recommandés pour la Coupe du Monde")

sc = score_compromis(dff).head(8).copy()
sc = sc.rename(columns={
    "neighbourhood": "Quartier",
    "neighbourhood_group": "Arrondissement",
    "prix_median": "Prix médian ($)",
    "dispo_moyenne": "Dispo (j/an)",
    "reviews_moyen": "Avis moyens",
    "occupation": "Occupation",
    "n": "Annonces",
    "score": "Score",
})
sc["Occupation"] = (sc["Occupation"] * 100).round(0)
sc["Prix médian ($)"] = sc["Prix médian ($)"].round(0)
sc["Dispo (j/an)"] = sc["Dispo (j/an)"].round(0)
sc["Avis moyens"] = sc["Avis moyens"].round(0)

st.dataframe(
    sc[["Quartier", "Arrondissement", "Prix médian ($)", "Dispo (j/an)",
        "Avis moyens", "Occupation", "Annonces", "Score"]],
    hide_index=True,
    width="stretch",
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Score compromis", min_value=0.0, max_value=1.0, format="%.2f"
        ),
        "Occupation": st.column_config.NumberColumn("Occupation (%)", format="%d %%"),
    },
)