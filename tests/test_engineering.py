"""
============================================================================
 test_engineering.py  -  Data Factory M2 IMSD  -  Data Engineer
============================================================================
Tests unitaires des fonctions cles du pipeline de nettoyage.

Strategie :
    On cree un PETIT DataFrame synthetique en memoire (quelques lignes),
    contenant volontairement tous les cas problematiques que le pipeline
    doit gerer : valeurs nulles, prix <= 0, minimum_nights aberrant,
    doublon sur id, types en chaine de caracteres.

    Chaque test verifie qu'UNE fonction transforme bien ce DataFrame
    comme attendu. Aucun acces a S3 : tout tourne en local (master[1]).

Lancement :
    pip install pytest
    pytest tests/ -v
============================================================================
"""

import sys
import os

import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Rendre le package src importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engineering.bronze_to_silver import (
    cast_types,
    handle_missing,
    filter_invalid,
    compute_null_rates,
)


# ---------------------------------------------------------------------------
# FIXTURES (objets partages entre les tests)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def spark():
    """Session Spark locale, partagee par tous les tests."""
    session = (
        SparkSession.builder
        .appName("tests_data_engineer")
        .master("local[1]")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


@pytest.fixture
def raw_df(spark):
    """Petit DataFrame synthetique imitant le CSV brut Airbnb.

    Toutes les colonnes sont en string (comme un CSV non type), et on
    injecte volontairement les cas a nettoyer :
      - id=4 est un DOUBLON de id=1
      - prix "0" et "-10" (invalides)
      - minimum_nights "400" (> 365, aberrant)
      - reviews_per_month / last_review nulls (listing sans avis)
      - name / host_name nulls
    """
    columns = [
        "id", "name", "host_id", "host_name", "neighbourhood_group",
        "neighbourhood", "latitude", "longitude", "room_type", "price",
        "minimum_nights", "number_of_reviews", "last_review",
        "reviews_per_month", "calculated_host_listings_count", "availability_365",
    ]
    data = [
        # ligne valide standard
        ("1", "Cosy loft", "101", "Alice", "Manhattan", "Harlem",
         "40.81", "-73.94", "Private room", "120", "2", "10",
         "2019-05-01", "0.5", "1", "200"),
        # listing valide SANS avis (nulls metier a remplir, pas a supprimer)
        ("2", "Sunny studio", "102", "Bob", "Brooklyn", "Bushwick",
         "40.70", "-73.92", "Entire home/apt", "90", "3", "0",
         None, None, "2", "0"),
        # prix invalide (0) -> doit etre supprime
        ("3", "Free spot", "103", "Carol", "Queens", "Astoria",
         "40.76", "-73.92", "Private room", "0", "1", "5",
         "2019-01-01", "1.0", "1", "100"),
        # DOUBLON de id=1 -> doit etre dedoublonne
        ("1", "Cosy loft", "101", "Alice", "Manhattan", "Harlem",
         "40.81", "-73.94", "Private room", "120", "2", "10",
         "2019-05-01", "0.5", "1", "200"),
        # minimum_nights aberrant (400 > 365) -> doit etre supprime
        ("5", "Long stay", "105", "Dan", "Bronx", "Mott Haven",
         "40.81", "-73.92", "Entire home/apt", "150", "400", "3",
         "2019-03-01", "0.3", "1", "50"),
        # name et host_name nulls -> doivent devenir "Unknown"
        ("6", None, "106", None, "Staten Island", "St. George",
         "40.64", "-74.07", "Private room", "70", "1", "8",
         "2019-02-01", "0.8", "1", "300"),
        # prix negatif -> doit etre supprime
        ("7", "Bad price", "107", "Eve", "Brooklyn", "Williamsburg",
         "40.71", "-73.95", "Private room", "-10", "2", "1",
         "2019-04-01", "0.2", "1", "120"),
    ]
    return spark.createDataFrame(data, columns)


# ---------------------------------------------------------------------------
# TESTS : cast_types
# ---------------------------------------------------------------------------
def test_cast_types_converts_numeric_columns(raw_df):
    """price, minimum_nights... doivent passer de string a numerique."""
    out = cast_types(raw_df)
    dtypes = dict(out.dtypes)
    assert dtypes["price"] == "int"
    assert dtypes["minimum_nights"] == "int"
    assert dtypes["number_of_reviews"] == "int"
    assert dtypes["availability_365"] == "int"
    assert dtypes["latitude"] == "double"
    assert dtypes["longitude"] == "double"
    assert dtypes["reviews_per_month"] == "double"


def test_cast_types_preserves_string_columns(raw_df):
    """Les colonnes texte doivent rester en string."""
    out = cast_types(raw_df)
    dtypes = dict(out.dtypes)
    assert dtypes["name"] == "string"
    assert dtypes["room_type"] == "string"
    assert dtypes["neighbourhood_group"] == "string"


def test_cast_types_keeps_correct_values(raw_df):
    """La conversion ne doit pas alterer les valeurs."""
    out = cast_types(raw_df)
    row = out.filter(F.col("id") == 1).first()
    assert row["price"] == 120
    assert row["minimum_nights"] == 2


# ---------------------------------------------------------------------------
# TESTS : handle_missing
# ---------------------------------------------------------------------------
def test_handle_missing_fills_reviews_per_month(raw_df):
    """reviews_per_month null -> 0.0 (et non supprime)."""
    out = handle_missing(cast_types(raw_df))
    row = out.filter(F.col("id") == 2).first()
    assert row["reviews_per_month"] == 0.0


def test_handle_missing_fills_last_review(raw_df):
    """last_review null -> 'No review'."""
    out = handle_missing(cast_types(raw_df))
    row = out.filter(F.col("id") == 2).first()
    assert row["last_review"] == "No review"


def test_handle_missing_fills_name_and_host(raw_df):
    """name / host_name nulls -> 'Unknown'."""
    out = handle_missing(cast_types(raw_df))
    row = out.filter(F.col("id") == 6).first()
    assert row["name"] == "Unknown"
    assert row["host_name"] == "Unknown"


def test_handle_missing_keeps_listing_without_review(raw_df):
    """Un listing sans avis ne doit PAS etre supprime (point metier cle)."""
    out = handle_missing(cast_types(raw_df))
    # id=2 (sans avis) doit toujours etre present
    assert out.filter(F.col("id") == 2).count() == 1


# ---------------------------------------------------------------------------
# TESTS : filter_invalid
# ---------------------------------------------------------------------------
def test_filter_invalid_removes_zero_and_negative_price(raw_df):
    """Les lignes prix=0 (id=3) et prix<0 (id=7) doivent disparaitre."""
    out = filter_invalid(handle_missing(cast_types(raw_df)))
    ids = {r["id"] for r in out.select("id").collect()}
    assert 3 not in ids   # prix = 0
    assert 7 not in ids   # prix = -10


def test_filter_invalid_removes_aberrant_minimum_nights(raw_df):
    """minimum_nights > 365 (id=5) doit etre supprime."""
    out = filter_invalid(handle_missing(cast_types(raw_df)))
    ids = {r["id"] for r in out.select("id").collect()}
    assert 5 not in ids


def test_filter_invalid_removes_duplicates(raw_df):
    """Le doublon sur id=1 doit etre dedoublonne (1 seule occurrence)."""
    out = filter_invalid(handle_missing(cast_types(raw_df)))
    assert out.filter(F.col("id") == 1).count() == 1


def test_filter_invalid_keeps_valid_rows(raw_df):
    """Apres nettoyage, il doit rester exactement les lignes valides.

    Lignes attendues : id 1 (dedoublonne), 2, 6.
    Supprimees : 3 (prix 0), 5 (min_nights 400), 7 (prix -10),
    et le doublon de 1.
    """
    out = filter_invalid(handle_missing(cast_types(raw_df)))
    ids = sorted(r["id"] for r in out.select("id").collect())
    assert ids == [1, 2, 6]


# ---------------------------------------------------------------------------
# TESTS : compute_null_rates
# ---------------------------------------------------------------------------
def test_compute_null_rates_counts_total_rows(raw_df):
    """Le rapport doit compter le bon nombre de lignes."""
    report = compute_null_rates(raw_df)
    assert report["total_rows"] == 7


def test_compute_null_rates_detects_nulls(raw_df):
    """Le rapport doit detecter les nulls avant nettoyage."""
    report = compute_null_rates(raw_df)
    # reviews_per_month : 1 null (id=2)
    assert report["columns"]["reviews_per_month"]["nulls"] == 1
    # name : 1 null (id=6)
    assert report["columns"]["name"]["nulls"] == 1


def test_compute_null_rates_zero_after_cleaning(raw_df):
    """Apres nettoyage, plus aucun null sur les colonnes traitees."""
    cleaned = filter_invalid(handle_missing(cast_types(raw_df)))
    report = compute_null_rates(cleaned)
    assert report["columns"]["reviews_per_month"]["nulls"] == 0
    assert report["columns"]["last_review"]["nulls"] == 0
    assert report["columns"]["name"]["nulls"] == 0
