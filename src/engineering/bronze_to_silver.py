"""
============================================================================
 bronze_to_silver.py  -  Data Factory M2 IMSD  -  Data Engineer
============================================================================
Pipeline de nettoyage Bronze -> Silver pour le dataset Airbnb NYC 2019.

Role :
    Lit le CSV brut depuis la zone Bronze (S3), applique un nettoyage
    documente et justifie, ecrit le resultat en Parquet partitionne dans
    la zone Silver, et produit un rapport qualite (avant / apres).

Proprietes du pipeline :
    - 100% PySpark (aucun pandas) -> traitement distribue.
    - Idempotent : mode("overwrite") -> relancable sans duplication.
    - Aucun credential en dur : le username vient d'une variable d'env,
      l'acces S3 est gere par la session Spark d'Onyxia (variables AWS_*).

Usage :
    python src/engineering/bronze_to_silver.py
    (ou bien : USERNAME=monuser python src/engineering/bronze_to_silver.py)
============================================================================
"""

import os
import json
import datetime

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DoubleType


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
# Le username est lu depuis l'environnement pour ne RIEN coder en dur.
# Valeur par defaut = username Onyxia du proprietaire du bucket.
USERNAME = os.environ.get("S3_USERNAME", "ekouraogo")

BRONZE_PATH = f"s3a://{USERNAME}/bronze/airbnb/AB_NYC_2019.csv"
SILVER_PATH = f"s3a://{USERNAME}/silver/airbnb/cleaned/"
REPORT_PATH = f"s3a://{USERNAME}/silver/airbnb/_quality_report/"

# Seuils de nettoyage (centralises ici pour etre facilement justifiables
# et ajustables lors de la defense technique).
PRICE_MIN = 1          # un logement a 0 EUR n'a pas de sens pour une prediction de prix
MIN_NIGHTS_MAX = 365   # au-dela d'un an de minimum, la donnee est aberrante


# ---------------------------------------------------------------------------
# FONCTIONS DE QUALITE (reutilisables / partageables entre Engineers)
# ---------------------------------------------------------------------------
def compute_null_rates(df: DataFrame) -> dict:
    """Retourne le nombre et le taux de nulls (ou chaines vides) par colonne.

    Une seule passe Spark via une aggregation, plutot qu'un count() par
    colonne -> beaucoup plus efficace sur gros volume.
    """
    total = df.count()
    if total == 0:
        return {"total_rows": 0, "columns": {}}

    exprs = []
    for c in df.columns:
        is_missing = F.col(c).isNull() | (F.trim(F.col(c).cast("string")) == "")
        exprs.append(F.sum(is_missing.cast("int")).alias(c))

    row = df.select(*exprs).collect()[0].asDict()
    cols = {
        c: {"nulls": int(row[c]), "null_rate_pct": round(row[c] / total * 100, 2)}
        for c in df.columns
    }
    return {"total_rows": total, "columns": cols}


def print_null_report(title: str, report: dict) -> None:
    """Affiche un rapport de nulls lisible dans les logs."""
    print(f"\n--- {title} (total = {report['total_rows']} lignes) ---")
    print(f"    {'colonne':<35}{'nulls':>10}{'taux':>10}")
    for c, stats in report["columns"].items():
        print(f"    {c:<35}{stats['nulls']:>10}{stats['null_rate_pct']:>9}%")


# ---------------------------------------------------------------------------
# ETAPES DU PIPELINE
# ---------------------------------------------------------------------------
def read_bronze(spark: SparkSession) -> DataFrame:
    """Lit le CSV brut depuis la zone Bronze.

    multiLine + quote/escape : certains champs `name` contiennent des
    virgules et des retours a la ligne entre guillemets. Sans ces options,
    Spark casserait ces lignes en plusieurs enregistrements corrompus.
    """
    print(f"\n[1/6] Lecture Bronze : {BRONZE_PATH}")
    df = (
        spark.read
        .option("header", "true")
        .option("multiLine", "true")
        .option("quote", '"')
        .option("escape", '"')
        .csv(BRONZE_PATH)
    )
    print(f"      Lignes lues : {df.count()}  |  colonnes : {len(df.columns)}")
    return df


def cast_types(df: DataFrame) -> DataFrame:
    """Corrige les types : tout est lu en string par defaut depuis un CSV.

    On force les colonnes numeriques pour permettre filtres, agregations
    et modelisation en aval (le Data Scientist a besoin de vrais nombres).
    """
    print("\n[3/6] Correction des types...")
    int_cols = [
        "id", "host_id", "price", "minimum_nights", "number_of_reviews",
        "calculated_host_listings_count", "availability_365",
    ]
    double_cols = ["latitude", "longitude", "reviews_per_month"]

    for c in int_cols:
        df = df.withColumn(c, F.col(c).cast(IntegerType()))
    for c in double_cols:
        df = df.withColumn(c, F.col(c).cast(DoubleType()))
    return df


def handle_missing(df: DataFrame) -> DataFrame:
    """Traite les valeurs manquantes selon leur SIGNIFICATION metier.

    - name / host_name (~0.04%) -> "Unknown" : champ texte non critique,
      on conserve la ligne (l'info de prix/localisation reste valable).
    - reviews_per_month null (20.56%) -> 0.0 : un null ici ne signifie PAS
      une donnee manquante mais "aucune review" (parfaitement correle avec
      last_review null). Mettre 0 est donc la vraie valeur metier.
    - last_review null (20.56%) -> "No review" : meme logique.
    On NE supprime PAS ces 20% de lignes : ce sont des listings valides
    et recents sans avis, precieux pour la prediction.
    """
    print("\n[4/6] Traitement des valeurs manquantes...")
    df = df.fillna({"name": "Unknown", "host_name": "Unknown"})
    df = df.fillna({"reviews_per_month": 0.0})
    df = df.fillna({"last_review": "No review"})
    return df


def filter_invalid(df: DataFrame) -> DataFrame:
    """Supprime les lignes aberrantes, en loggant chaque suppression.

    Chaque filtre est justifie et compte separement pour la transparence
    (et pour la defense technique devant le professeur).
    """
    print("\n[5/6] Filtrage des valeurs aberrantes...")

    n0 = df.count()

    # 1) Prix nul / manquant / <= 0  -> aberrant pour une prediction de prix
    df = df.filter(F.col("price").isNotNull() & (F.col("price") >= PRICE_MIN))
    n1 = df.count()
    print(f"      - prix < {PRICE_MIN} ou null  : {n0 - n1} lignes supprimees")

    # 2) minimum_nights aberrant (> 1 an)
    df = df.filter(
        F.col("minimum_nights").isNotNull()
        & (F.col("minimum_nights") >= 1)
        & (F.col("minimum_nights") <= MIN_NIGHTS_MAX)
    )
    n2 = df.count()
    print(f"      - minimum_nights hors [1..{MIN_NIGHTS_MAX}] : {n1 - n2} lignes supprimees")

    # 3) Coordonnees manquantes (necessaires pour le geospatial / dashboard)
    df = df.filter(F.col("latitude").isNotNull() & F.col("longitude").isNotNull())
    n3 = df.count()
    print(f"      - lat/long manquantes : {n2 - n3} lignes supprimees")

    # 4) Dedoublonnage sur la cle metier `id`.
    #    Le dataset n'a pas de doublons aujourd'hui, mais ce filtre garantit
    #    l'IDEMPOTENCE : si la source est re-ingeree avec des doublons, le
    #    pipeline reste correct.
    df = df.dropDuplicates(["id"])
    n4 = df.count()
    print(f"      - doublons sur id : {n3 - n4} lignes supprimees")

    print(f"      Lignes restantes : {n4}")
    return df


def write_silver(df: DataFrame) -> None:
    """Ecrit en Parquet partitionne par arrondissement.

    - Parquet : format colonne compresse, optimal pour Spark en aval.
    - partitionBy(neighbourhood_group) : les 5 arrondissements sont la
      dimension de filtrage la plus frequente (analyse par zone, prix par
      quartier) -> le partition pruning evitera de lire tout le dataset.
    - mode("overwrite") : rend le pipeline IDEMPOTENT (relancable sans
      dupliquer les donnees).
    """
    print(f"\n[6/6] Ecriture Silver (Parquet partitionne) : {SILVER_PATH}")
    (
        df.write
        .mode("overwrite")
        .partitionBy("neighbourhood_group")
        .parquet(SILVER_PATH)
    )
    print("      Ecriture terminee.")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main() -> None:
    spark = (
        SparkSession.builder
        .appName("bronze_to_silver_airbnb")
        .enableHiveSupport()
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    print("=" * 70)
    print(f" PIPELINE BRONZE -> SILVER  (user: {USERNAME})")
    print("=" * 70)

    # 1. Lecture
    df = read_bronze(spark)

    # 2. Rapport qualite AVANT
    print("\n[2/6] Rapport qualite AVANT nettoyage")
    report_before = compute_null_rates(df)
    print_null_report("Nulls AVANT", report_before)

    # 3-5. Nettoyage
    df = cast_types(df)
    df = handle_missing(df)
    df = filter_invalid(df)
    df = df.cache()  # reutilise pour rapport + ecriture

    # Rapport qualite APRES
    report_after = compute_null_rates(df)
    print_null_report("Nulls APRES", report_after)

    # 6. Ecriture
    write_silver(df)

    # Resume + rapport JSON consolide
    n_before = report_before["total_rows"]
    n_after = report_after["total_rows"]
    summary = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "username": USERNAME,
        "rows_bronze": n_before,
        "rows_silver": n_after,
        "rows_removed": n_before - n_after,
        "retention_pct": round(n_after / n_before * 100, 2),
        "nulls_before": report_before["columns"],
        "nulls_after": report_after["columns"],
        "cleaning_rules": {
            "price_min": PRICE_MIN,
            "minimum_nights_max": MIN_NIGHTS_MAX,
            "missing_value_strategy": {
                "name/host_name": "Unknown",
                "reviews_per_month": 0.0,
                "last_review": "No review",
            },
            "partitioned_by": "neighbourhood_group",
            "format": "parquet",
            "write_mode": "overwrite (idempotent)",
        },
    }

    print("\n" + "=" * 70)
    print(" RAPPORT QUALITE - RESUME")
    print("=" * 70)
    print(f"  Lignes Bronze   : {n_before}")
    print(f"  Lignes Silver   : {n_after}")
    print(f"  Lignes retirees : {n_before - n_after}")
    print(f"  Taux retention  : {summary['retention_pct']}%")

    # Sauvegarde locale du rapport (pour le rendu Git) + tentative S3.
    os.makedirs("reports", exist_ok=True)
    local_report = "reports/quality_report.json"
    with open(local_report, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n  Rapport JSON ecrit : {local_report}")

    try:
        report_df = spark.createDataFrame([(json.dumps(summary, ensure_ascii=False),)], ["report"])
        report_df.coalesce(1).write.mode("overwrite").json(REPORT_PATH)
        print(f"  Rapport JSON ecrit sur S3 : {REPORT_PATH}")
    except Exception as e:  # noqa: BLE001
        print(f"  (rapport S3 ignore : {e})")

    print("\n" + "=" * 70)
    print(" PIPELINE BRONZE -> SILVER TERMINE AVEC SUCCES")
    print("=" * 70)

    spark.stop()


if __name__ == "__main__":
    main()
