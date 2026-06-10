"""
============================================================================
 silver_to_gold.py  -  Data Factory M2 IMSD  -  Data Engineer
============================================================================
Pipeline de transformation Silver -> Gold pour le dataset Airbnb NYC 2019.

Role :
    Lit les donnees nettoyees de la zone Silver (Parquet), construit des
    agregations et des features, et ecrit deux jeux de donnees Gold :
      - gold/ml/        : table enrichie au grain "listing" pour le Data
                          Scientist (prediction de prix).
      - gold/dashboard/ : KPI agreges par zone / type pour le Data Analyst.

Proprietes du pipeline :
    - 100% PySpark (aucun pandas) -> traitement distribue.
    - Idempotent : mode("overwrite") -> relancable sans duplication.
    - Aucun credential en dur (username via variable d'env, acces S3 gere
      par la session Spark d'Onyxia).
    - Alimente UNIQUEMENT depuis Silver (gouvernance Medallion respectee).

Usage :
    python src/engineering/silver_to_gold.py
============================================================================
"""

import os

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
USERNAME = os.environ.get("S3_USERNAME", "ekouraogo")

SILVER_PATH = f"s3a://{USERNAME}/silver/airbnb/cleaned/"
GOLD_ML_PATH = f"s3a://{USERNAME}/gold/ml/airbnb_features/"
GOLD_DASH_PATH = f"s3a://{USERNAME}/gold/dashboard/"


# ---------------------------------------------------------------------------
# ETAPE 1 : LECTURE SILVER
# ---------------------------------------------------------------------------
def read_silver(spark: SparkSession) -> DataFrame:
    print(f"\n[1/4] Lecture Silver : {SILVER_PATH}")
    df = spark.read.parquet(SILVER_PATH)
    print(f"      Lignes lues : {df.count()}  |  colonnes : {len(df.columns)}")
    return df


# ---------------------------------------------------------------------------
# ETAPE 2 : FEATURES POUR LE ML (gold/ml/)
# ---------------------------------------------------------------------------
def build_ml_features(df: DataFrame) -> DataFrame:
    """Enrichit la table au grain listing pour la prediction de prix.

    On AJOUTE des colonnes derivees utiles a la modelisation, sans changer
    le grain (1 ligne = 1 listing). Le Data Scientist part de cette table.
    """
    print("\n[2/4] Construction des features ML (grain listing)...")

    # Prix moyen de la zone (jointure auto via window) -> permet au modele
    # de situer un listing par rapport a son marche local.
    from pyspark.sql import Window
    w_zone = Window.partitionBy("neighbourhood_group")
    w_ntype = Window.partitionBy("neighbourhood_group", "room_type")

    feats = (
        df
        # log du prix : la cible price est tres asymetrique (max 10000),
        # le log stabilise la distribution pour la regression.
        .withColumn("price_log", F.round(F.log(F.col("price") + F.lit(1)), 4))
        # a-t-il deja recu des avis ? (feature binaire simple et forte)
        .withColumn("has_reviews", (F.col("number_of_reviews") > 0).cast("int"))
        # taux d'occupation approxime : 1 - dispo/365
        .withColumn(
            "occupancy_rate",
            F.round(1 - (F.col("availability_365") / F.lit(365)), 4),
        )
        # prix moyen de la zone et ecart relatif du listing a ce prix
        .withColumn("zone_avg_price", F.round(F.avg("price").over(w_zone), 2))
        .withColumn(
            "price_vs_zone_pct",
            F.round((F.col("price") - F.col("zone_avg_price"))
                    / F.col("zone_avg_price") * 100, 2),
        )
        # prix moyen zone x type de logement (segmentation plus fine)
        .withColumn("zone_type_avg_price", F.round(F.avg("price").over(w_ntype), 2))
    )

    print(f"      Features ajoutees : price_log, has_reviews, occupancy_rate,")
    print(f"                          zone_avg_price, price_vs_zone_pct, zone_type_avg_price")
    return feats


# ---------------------------------------------------------------------------
# ETAPE 3 : KPI POUR LE DASHBOARD (gold/dashboard/)
# ---------------------------------------------------------------------------
def build_dashboard_kpis(df: DataFrame) -> DataFrame:
    """Agrege les KPI par arrondissement x type de logement.

    Grain de sortie = (neighbourhood_group, room_type) -> petit tableau
    directement exploitable par le Data Analyst pour ses visualisations.
    """
    print("\n[3/4] Construction des KPI dashboard (grain zone x type)...")

    kpis = (
        df.groupBy("neighbourhood_group", "room_type")
        .agg(
            F.count("*").alias("nb_listings"),
            F.round(F.avg("price"), 2).alias("avg_price"),
            F.expr("percentile_approx(price, 0.5)").alias("median_price"),
            F.min("price").alias("min_price"),
            F.max("price").alias("max_price"),
            F.round(F.avg("availability_365"), 1).alias("avg_availability"),
            F.round(F.avg("number_of_reviews"), 1).alias("avg_reviews"),
            F.round(F.avg("reviews_per_month"), 2).alias("avg_reviews_per_month"),
        )
        .orderBy("neighbourhood_group", "room_type")
    )
    print(f"      Lignes KPI : {kpis.count()}")
    return kpis


# ---------------------------------------------------------------------------
# ETAPE 4 : ECRITURE GOLD
# ---------------------------------------------------------------------------
def write_gold(features: DataFrame, kpis: DataFrame) -> None:
    print(f"\n[4/4] Ecriture Gold...")

    # ML : partitionne par zone (filtrage frequent en modelisation par zone)
    (
        features.write
        .mode("overwrite")
        .partitionBy("neighbourhood_group")
        .parquet(GOLD_ML_PATH)
    )
    print(f"      gold/ml        -> {GOLD_ML_PATH}")

    # Dashboard : petit volume -> 1 seul fichier, plus simple a charger
    (
        kpis.coalesce(1).write
        .mode("overwrite")
        .parquet(GOLD_DASH_PATH)
    )
    print(f"      gold/dashboard -> {GOLD_DASH_PATH}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main() -> None:
    spark = (
        SparkSession.builder
        .appName("silver_to_gold_airbnb")
        .enableHiveSupport()
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    print("=" * 70)
    print(f" PIPELINE SILVER -> GOLD  (user: {USERNAME})")
    print("=" * 70)

    df = read_silver(spark)
    features = build_ml_features(df)
    kpis = build_dashboard_kpis(df)
    write_gold(features, kpis)

    print("\n" + "=" * 70)
    print(" APERCU KPI DASHBOARD")
    print("=" * 70)
    kpis.show(truncate=False)

    print("=" * 70)
    print(" PIPELINE SILVER -> GOLD TERMINE AVEC SUCCES")
    print("=" * 70)

    spark.stop()


if __name__ == "__main__":
    main()
