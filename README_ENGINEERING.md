<div align="center">

# Data Factory — Pipeline Data Engineering

### Architecture Medallion · PySpark · Onyxia SSP Cloud

![PySpark](https://img.shields.io/badge/PySpark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Parquet](https://img.shields.io/badge/Parquet-50ABF1?style=for-the-badge)
![S3](https://img.shields.io/badge/S3_MinIO-FF9900?style=for-the-badge&logo=amazons3&logoColor=white)

**Auteurs :** Emmanuel KOURAOGO & Mylane PECH · M2 IMSD · Paris-Saclay · 2025-2026

</div>

---

## Vue d'ensemble

Pipeline de traitement des données **Airbnb New York City 2019** (48 895 listings) selon l'architecture **Medallion** sur la plateforme **Onyxia** (SSP Cloud), entièrement en **PySpark distribué**.

```
BRONZE SILVER GOLD
──────────── ────────────────────── ─────────────────────────
CSV brut ──► Données nettoyées ──► Features ML
AB_NYC_2019 Parquet partitionné KPI Dashboard
(Architecte) (Data Engineer) (Data Engineer)
```

| Zone | Contenu | Responsabilité |
|:----:|---------|:--------------:|
| **Bronze** | CSV brut Airbnb non modifié | Architecte |
| **Silver** | Données nettoyées en Parquet | **Data Engineer** |
| **Gold** | Features ML + KPI dashboard | **Data Engineer** |

---

## Structure du projet

```
Data-factory/
├── src/engineering/
│ ├── bronze_to_silver.py # Nettoyage CSV → Parquet partitionné
│ └── silver_to_gold.py # Feature engineering + KPI agrégés
└── reports/
 └── quality_report.json # Rapport qualité (nulls avant/après)
```

---

## Script 1 — `bronze_to_silver.py`

> Lecture du CSV Bronze → Nettoyage → Écriture Parquet Silver

### Nettoyages appliqués

| Opération | Détail | Impact |
|-----------|--------|:------:|
| **Correction types** | `price`, `minimum_nights`, `latitude` → `int`/`double` | Toutes colonnes |
| **reviews_per_month** null → `0.0` | Aucune review = donnée valide, pas manquante | 20.56% |
| **last_review** null → `"No review"` | — | 20.56% |
| **name/host_name** null → `"Unknown"` | — | ~0.04% |
| **Prix ≤ 0** supprimés | Logement gratuit = aberrant | 11 lignes |
| **minimum_nights > 365** supprimés | Valeurs aberrantes (jusqu'à 1250 nuits) | 14 lignes |
| **Déduplication** sur `id` | Garantit l'idempotence | — |

**Sortie :** Parquet partitionné par `neighbourhood_group` → 5 partitions (partition pruning efficace)

---

## Script 2 — `silver_to_gold.py`

> Lecture Silver → Feature Engineering → KPI Dashboard

### Gold ML — 6 features pour le Data Scientist

| Feature | Description |
|---------|-------------|
| `price_log` | Log du prix — normalise la distribution |
| `has_reviews` | Indicateur binaire d'activité du listing |
| `occupancy_rate` | Taux d'occupation estimé |
| `zone_avg_price` | Prix moyen de la zone géographique |
| `price_vs_zone_pct` | Écart relatif au prix moyen de zone |
| `zone_type_avg_price` | Prix moyen zone × type de logement |

### Gold Dashboard — 15 KPI pour le Data Analyst

5 zones × 3 types de logement → prix moyen/médian/min/max, disponibilité, reviews

---

## Résultats

<div align="center">

| Métrique | Valeur |
|:---------|:------:|
| Lignes Bronze | 48 895 |
| Lignes Silver | **48 870** |
| Lignes retirées | 25 (0.05%) |
| Taux de rétention | **99.95%** |
| Partitions Silver | 5 arrondissements |
| Table ML Gold | 48 870 × 22 colonnes |
| KPI Dashboard | 15 lignes agrégées |

</div>

---

## Propriétés garanties

| Propriété | Détail |
|-----------|--------|
| **100% PySpark** | Aucune opération pandas — tout distribué |
| **Idempotent** | `mode("overwrite")` — relançable sans duplication |
| **0 credential en dur** | `S3_USERNAME` via variable d'env, accès S3 par Onyxia |
| **Gouvernance Medallion** | Silver ← Bronze uniquement · Gold ← Silver uniquement |
| **Tolérance aux pannes** | Spark recalcule automatiquement les partitions perdues |

---

## Lancement

### Pré-requis
- Service **Jupyter PySpark** lancé sur Onyxia
- Dossiers S3 : `bronze/`, `silver/`, `gold/ml/`, `gold/dashboard/`
- CSV brut présent en Bronze

### Exécution

```bash
cd ~/work/data-factory

# Étape 1 — Bronze → Silver
python src/engineering/bronze_to_silver.py

# Étape 2 — Silver → Gold
python src/engineering/silver_to_gold.py

# Avec un bucket S3 différent
S3_USERNAME=votre_user python src/engineering/bronze_to_silver.py
```

### Vérification

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("verif").getOrCreate()
df = spark.read.parquet("s3a://ekouraogo/silver/airbnb/cleaned/")
print("Lignes Silver:", df.count())
df.groupBy("neighbourhood_group").count().show()
spark.stop()
```

---

<div align="center">

**Emmanuel KOURAOGO** & **Mylane PECH** · M2 IMSD · Paris-Saclay

[![GitHub](https://img.shields.io/badge/GitHub-EKOURAOGO-181717?style=flat-square&logo=github)](https://github.com/EKOURAOGO)

</div>
