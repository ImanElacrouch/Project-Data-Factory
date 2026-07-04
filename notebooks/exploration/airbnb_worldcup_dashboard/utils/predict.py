"""
Prédiction de prix — chargement du modèle Gradient Boosting (joblib) et
prédiction à partir d'une saisie simple de l'utilisateur.

Le modèle est entraîné par `train_model.py` (méthodologie du Data Scientist :
cible log(prix), variables de fuite exclues). Aucune dépendance Spark.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "price_model.joblib"


@st.cache_resource(show_spinner="Chargement du modèle de prédiction…")
def load_model():
    """Charge le bundle joblib (modèle + métadonnées). None si absent."""
    if not MODEL_PATH.is_file():
        return None
    import joblib
    return joblib.load(MODEL_PATH)


def model_available() -> bool:
    return MODEL_PATH.is_file()


def predict_price(bundle, neighbourhood: str, room_type: str,
                  availability: int) -> dict:
    """Prédit le prix/nuit pour un logement décrit par l'utilisateur.

    Les variables non demandées (avis, nuits min, occupation…) sont
    pré-remplies avec la médiane du quartier (ou médiane globale).
    """
    geo = bundle["geo"]
    cent = bundle["centroids"]
    row_c = cent[cent["neighbourhood"] == neighbourhood]
    if not row_c.empty:
        lat = float(row_c["latitude"].iloc[0])
        lon = float(row_c["longitude"].iloc[0])
    else:
        lat = cent["latitude"].mean()
        lon = cent["longitude"].mean()

    med = bundle["medians_by_zone"]
    sub = med[(med["neighbourhood"] == neighbourhood) & (med["room_type"] == room_type)]
    g = bundle["global_medians"]

    def pick(col):
        if not sub.empty and pd.notna(sub[col].iloc[0]):
            return float(sub[col].iloc[0])
        return float(g[col])

    feat = {
        "room_type": room_type,
        "neighbourhood": neighbourhood,
        "availability_365": float(availability),
        "number_of_reviews": pick("number_of_reviews"),
        "reviews_per_month": pick("reviews_per_month"),
        "calculated_host_listings_count": pick("calculated_host_listings_count"),
        "minimum_nights": pick("minimum_nights"),
        "occupancy_rate": pick("occupancy_rate"),
        "latitude": lat,
        "longitude": lon,
        "distance_center": np.sqrt((lat - geo["lat_center"]) ** 2
                                   + (lon - geo["lon_center"]) ** 2),
        "distance_jfk": np.sqrt((lat - geo["lat_jfk"]) ** 2
                                + (lon - geo["lon_jfk"]) ** 2),
    }
    X = pd.DataFrame([feat])[bundle["cat"] + bundle["num"]]
    log_pred = float(bundle["pipeline"].predict(X)[0])
    price = float(np.exp(log_pred))
    # Fourchette ± erreur moyenne du modèle
    mae = bundle["metrics"]["mae"]
    return {"prix": price, "bas": max(0, price - mae), "haut": price + mae}
