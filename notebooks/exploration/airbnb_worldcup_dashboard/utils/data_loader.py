"""
Chargement des données depuis la zone GOLD (architecture Medallion).

Le dashboard lit en priorité la zone Gold ML sur S3/MinIO
(s3://<bucket>/gold/ml/airbnb_features/), exactement la sortie du pipeline
Bronze -> Silver -> Gold. Repli automatique sur le CSV local si S3 n'est
pas accessible (utile en local ou pour la soutenance).

Ordre de résolution :
  1. S3 Gold   -> variable AIRBNB_GOLD_S3 (ex: s3://ielacrouch/gold/ml/airbnb_features/)
  2. CSV       -> variable AIRBNB_DATA_PATH
  3. CSV local -> ./data/airbnb_features.csv

Sur Onyxia (service VSCode/Jupyter), les identifiants MinIO sont injectés
automatiquement (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN,
AWS_S3_ENDPOINT) : aucune configuration supplémentaire n'est nécessaire.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

USED_COLUMNS = [
    "id", "neighbourhood_group", "neighbourhood", "room_type", "price",
    "minimum_nights", "number_of_reviews", "reviews_per_month",
    "calculated_host_listings_count", "availability_365", "occupancy_rate",
    "zone_avg_price", "price_vs_zone_pct", "zone_type_avg_price",
    "latitude", "longitude",
]


def _s3_storage_options() -> dict:
    """Construit les options S3 à partir des variables Onyxia/MinIO."""
    endpoint = os.environ.get("AWS_S3_ENDPOINT", "minio.lab.sspcloud.fr")
    opts = {"client_kwargs": {"endpoint_url": f"https://{endpoint}"}}
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        opts["key"] = os.environ["AWS_ACCESS_KEY_ID"]
    if os.environ.get("AWS_SECRET_ACCESS_KEY"):
        opts["secret"] = os.environ["AWS_SECRET_ACCESS_KEY"]
    if os.environ.get("AWS_SESSION_TOKEN"):
        opts["token"] = os.environ["AWS_SESSION_TOKEN"]
    return opts


def _read_raw() -> tuple[pd.DataFrame, str]:
    """Lit les données brutes Gold (S3) ou CSV. Renvoie (df, source)."""
    gold_uri = os.environ.get("AIRBNB_GOLD_S3", "").strip()
    if gold_uri:
        try:
            df = pd.read_parquet(gold_uri, storage_options=_s3_storage_options())
            return df, f"Zone Gold (S3) : {gold_uri}"
        except Exception as exc:  # repli silencieux sur CSV
            st.warning(f"Lecture S3 Gold impossible ({exc}). Repli sur le CSV local.")

    csv_candidates = [
        os.environ.get("AIRBNB_DATA_PATH", ""),
        str(Path(__file__).resolve().parents[1] / "data" / "airbnb_features.csv"),
        "airbnb_features.csv",
    ]
    for cand in csv_candidates:
        if cand and Path(cand).is_file():
            return pd.read_csv(cand), f"CSV local : {cand}"

    raise FileNotFoundError(
        "Aucune source de données. Définissez AIRBNB_GOLD_S3 (zone Gold) ou "
        "placez airbnb_features.csv dans ./data/."
    )


@st.cache_data(show_spinner="Chargement des données Gold…")
def load_data() -> pd.DataFrame:
    df, source = _read_raw()
    st.session_state["data_source"] = source

    keep = [c for c in USED_COLUMNS if c in df.columns]
    df = df[keep].copy()

    df = df[(df["price"] > 0) & (df["price"] <= 2000)].copy()
    df["dispo_longue"] = df["availability_365"] > 180
    df["occupancy_pct"] = (df["occupancy_rate"] * 100).round(1)
    return df.reset_index(drop=True)


def get_bounds(df: pd.DataFrame) -> dict:
    return {
        "price_min": int(df["price"].min()),
        "price_max": int(df["price"].quantile(0.99)),
        "price_hard_max": int(df["price"].max()),
    }
