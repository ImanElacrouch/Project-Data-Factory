"""
Calcul des KPI métier du projet Airbnb NYC — Coupe du Monde 2026.

Chaque KPI est calculé à partir des données réelles (zone Gold), jamais
codé en dur. Les définitions, formules et interprétations métier sont
documentées dans le README et rappelées dans l'aide contextuelle du
dashboard.
"""
from __future__ import annotations

import pandas as pd

# Seuil "logement disponible longtemps" = ouvert > 180 jours/an.
SEUIL_DISPO_LONGUE = 180


def compute_kpis(df: pd.DataFrame) -> dict:
    """Retourne le dictionnaire des KPI affichés dans les cartes du haut."""
    if df.empty:
        return {
            "n_logements": 0,
            "prix_moyen": 0.0,
            "prix_median": 0.0,
            "dispo_moyenne": 0.0,
            "occupation_moyenne": 0.0,
            "reviews_moyen": 0.0,
            "n_dispo_longue": 0,
            "quartier_moins_cher": "—",
            "quartier_plus_cher": "—",
        }

    # Prix médian par quartier (>= 30 annonces pour être statistiquement fiable).
    par_quartier = (
        df.groupby("neighbourhood")
        .agg(n=("id", "size"), prix_median=("price", "median"))
        .query("n >= 30")
        .sort_values("prix_median")
    )

    quartier_moins_cher = (
        par_quartier.index[0] if not par_quartier.empty else "—"
    )
    quartier_plus_cher = (
        par_quartier.index[-1] if not par_quartier.empty else "—"
    )

    return {
        "n_logements": int(len(df)),
        "prix_moyen": float(df["price"].mean()),
        "prix_median": float(df["price"].median()),
        "dispo_moyenne": float(df["availability_365"].mean()),
        "occupation_moyenne": float(df["occupancy_rate"].mean() * 100),
        "reviews_moyen": float(df["number_of_reviews"].mean()),
        "n_dispo_longue": int((df["availability_365"] > SEUIL_DISPO_LONGUE).sum()),
        "quartier_moins_cher": quartier_moins_cher,
        "quartier_plus_cher": quartier_plus_cher,
        "prix_moins_cher": (
            float(par_quartier["prix_median"].iloc[0])
            if not par_quartier.empty
            else 0.0
        ),
        "prix_plus_cher": (
            float(par_quartier["prix_median"].iloc[-1])
            if not par_quartier.empty
            else 0.0
        ),
    }


def prix_par_arrondissement(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("neighbourhood_group")
        .agg(
            prix_median=("price", "median"),
            prix_moyen=("price", "mean"),
            n=("id", "size"),
        )
        .reset_index()
        .sort_values("prix_median")
    )
    return out


def prix_par_type(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("room_type")
        .agg(
            prix_median=("price", "median"),
            prix_moyen=("price", "mean"),
            n=("id", "size"),
            dispo_moyenne=("availability_365", "mean"),
        )
        .reset_index()
        .sort_values("prix_median")
    )
    return out


def top_quartiers(df: pd.DataFrame, n: int = 10, cheapest: bool = True,
                  min_listings: int = 30) -> pd.DataFrame:
    """Top N quartiers les moins (ou plus) chers, filtrés sur un nombre
    minimal d'annonces pour rester fiable."""
    base = (
        df.groupby(["neighbourhood", "neighbourhood_group"])
        .agg(
            prix_median=("price", "median"),
            dispo_moyenne=("availability_365", "mean"),
            occupation=("occupancy_rate", "mean"),
            n=("id", "size"),
        )
        .reset_index()
        .query("n >= @min_listings")
        .sort_values("prix_median", ascending=cheapest)
    )
    return base.head(n)


def score_compromis(df: pd.DataFrame, min_listings: int = 30) -> pd.DataFrame:
    """
    Score 'meilleur compromis' par quartier pour la Coupe du Monde.

    Combine 3 dimensions normalisées (0-1) :
      - prix médian bas         (poids 0.5)  -> abordabilité
      - disponibilité élevée     (poids 0.3)  -> on trouve encore de la place
      - popularité (reviews)     (poids 0.2)  -> séjours éprouvés / fiables

    Score = 0.5*(1-prix_norm) + 0.3*dispo_norm + 0.2*reviews_norm
    Plus le score est haut, meilleur est le compromis.
    """
    base = (
        df.groupby(["neighbourhood", "neighbourhood_group"])
        .agg(
            prix_median=("price", "median"),
            dispo_moyenne=("availability_365", "mean"),
            reviews_moyen=("number_of_reviews", "mean"),
            occupation=("occupancy_rate", "mean"),
            n=("id", "size"),
        )
        .reset_index()
        .query("n >= @min_listings")
    )
    if base.empty:
        base["score"] = []
        return base

    def _norm(s: pd.Series) -> pd.Series:
        rng = s.max() - s.min()
        return (s - s.min()) / rng if rng else 0.0

    prix_norm = _norm(base["prix_median"])
    dispo_norm = _norm(base["dispo_moyenne"])
    reviews_norm = _norm(base["reviews_moyen"])

    base["score"] = (
        0.5 * (1 - prix_norm) + 0.3 * dispo_norm + 0.2 * reviews_norm
    ).round(3)
    return base.sort_values("score", ascending=False)


def estimer_prix(df: pd.DataFrame, arrondissement: str, room_type: str) -> dict:
    """
    Estimateur de prix simple (baseline) à partir des données Gold.

    Renvoie une fourchette basée sur les logements comparables
    (même arrondissement + même type). Sert de point de départ : le
    modèle de Machine Learning de la zone gold/ml peut remplacer cette
    fonction sans rien changer à l'interface.
    """
    sub = df[(df["neighbourhood_group"] == arrondissement)
             & (df["room_type"] == room_type)]
    if sub.empty:
        sub = df[df["neighbourhood_group"] == arrondissement]
    if sub.empty:
        return {"estimation": float(df["price"].median()),
                "bas": float(df["price"].quantile(0.25)),
                "haut": float(df["price"].quantile(0.75)), "n": int(len(df))}
    return {
        "estimation": float(sub["price"].median()),
        "bas": float(sub["price"].quantile(0.25)),
        "haut": float(sub["price"].quantile(0.75)),
        "n": int(len(sub)),
    }
