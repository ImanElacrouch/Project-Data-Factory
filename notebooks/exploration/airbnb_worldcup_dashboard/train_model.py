"""
Entraîne le modèle de prédiction de prix (Gradient Boosting), dans l'esprit
du notebook du Data Scientist :
  - cible : log(prix)
  - features numériques + room_type + neighbourhood + distances géographiques
  - on EXCLUT les variables de fuite (price_vs_zone_pct, zone_avg_price)

Produit un bundle joblib autonome (modèle + métadonnées) chargé par le
dashboard, sans aucune dépendance Spark.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

ROOT = Path(__file__).resolve().parent
CSV = ROOT / "data" / "airbnb_features.csv"
OUT = ROOT / "models"
OUT.mkdir(exist_ok=True)

# Repères géographiques (identiques au notebook du Data Scientist)
LAT_CENTER, LON_CENTER = 40.7580, -73.9855   # Times Square / cœur Manhattan
LAT_JFK, LON_JFK = 40.6413, -73.7781         # aéroport JFK

CAT = ["room_type", "neighbourhood"]
NUM = [
    "availability_365", "number_of_reviews", "reviews_per_month",
    "calculated_host_listings_count", "minimum_nights", "occupancy_rate",
    "latitude", "longitude", "distance_center", "distance_jfk",
]
# Variables de fuite explicitement écartées (comme dans le notebook DS)
LEAKAGE = ["price", "price_vs_zone_pct", "zone_avg_price", "zone_type_avg_price"]


def add_geo(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["distance_center"] = np.sqrt(
        (df["latitude"] - LAT_CENTER) ** 2 + (df["longitude"] - LON_CENTER) ** 2
    )
    df["distance_jfk"] = np.sqrt(
        (df["latitude"] - LAT_JFK) ** 2 + (df["longitude"] - LON_JFK) ** 2
    )
    return df


def main() -> None:
    df = pd.read_csv(CSV)
    df = df[(df["price"] > 0) & (df["price"] <= 2000)].copy()
    df = add_geo(df)
    df = df.fillna({"reviews_per_month": 0.0})

    X = df[CAT + NUM]
    y = np.log(df["price"].values)

    pre = ColumnTransformer(
        transformers=[
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value",
                                   unknown_value=-1), CAT),
        ],
        remainder="passthrough",
    )
    # Les colonnes catégorielles sont les 2 premières après transformation.
    model = HistGradientBoostingRegressor(
        max_iter=400, max_depth=8, learning_rate=0.06,
        categorical_features=[0, 1], random_state=42,
    )
    pipe = Pipeline([("pre", pre), ("gbt", model)])

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    pipe.fit(Xtr, ytr)

    pred = pipe.predict(Xte)
    r2 = r2_score(yte, pred)
    # MAE en dollars (on repasse de log -> prix)
    mae = mean_absolute_error(np.exp(yte), np.exp(pred))

    # Médianes par (quartier, type) pour pré-remplir les champs non demandés
    med = (
        df.groupby(["neighbourhood", "room_type"])[
            ["number_of_reviews", "reviews_per_month",
             "calculated_host_listings_count", "minimum_nights", "occupancy_rate"]
        ].median().reset_index()
    )
    global_med = df[["number_of_reviews", "reviews_per_month",
                     "calculated_host_listings_count", "minimum_nights",
                     "occupancy_rate"]].median().to_dict()

    # Centroïdes géographiques par quartier
    centroids = (
        df.groupby("neighbourhood")[["latitude", "longitude"]]
        .mean().reset_index()
    )

    bundle = {
        "pipeline": pipe,
        "cat": CAT,
        "num": NUM,
        "geo": dict(lat_center=LAT_CENTER, lon_center=LON_CENTER,
                    lat_jfk=LAT_JFK, lon_jfk=LON_JFK),
        "medians_by_zone": med,
        "global_medians": global_med,
        "centroids": centroids,
        "metrics": dict(r2=round(float(r2), 3), mae=round(float(mae), 1),
                        n=int(len(df))),
        "leakage_excluded": LEAKAGE,
    }
    joblib.dump(bundle, OUT / "price_model.joblib")
    print(json.dumps(bundle["metrics"], indent=2))
    print("Modèle sauvegardé :", OUT / "price_model.joblib")


if __name__ == "__main__":
    main()
