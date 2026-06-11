<div align="center">

# Data Factory _ Pipeline Data Engineering

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
BRONZE                    SILVER                         GOLD
──────────────────        ──────────────────────         ──────────────────────
CSV brut            ──►   Données nettoyées        ──►   Features ML
AB_NYC_2019               Parquet partitionné            KPI Dashboard
(Architecte)              (Data Engineer)                (Data Engineer)
          [bronze_to_silver.py]          [silver_to_gold.py]
```

<div align="center">

| Zone | Contenu | Responsabilité |
|------|---------|---------------|
| Bronze | CSV brut Airbnb non modifié | Architecte |
| Silver | Données nettoyées · Parquet partitionné | Data Engineer |
| Gold | Features ML + KPI dashboard agrégés | Data Engineer |

</div>

---

## Structure du projet

```
Data-factory/
├── src/engineering/
│   ├── bronze_to_silver.py    # Nettoyage CSV → Parquet partitionné
│   └── silver_to_gold.py      # Feature engineering + KPI agrégés
└── reports/
    └── quality_report.json    # Rapport qualité (nulls avant/après)
```

---

## Script 1 — `bronze_to_silver.py`

> Lecture du CSV Bronze · Nettoyage · Écriture Parquet Silver

### Nettoyages appliqués

| Opération | Détail | Impact |
|-----------|--------|--------|
| Correction des types | `price`, `minimum_nights`, `latitude` → `int` / `double` | Toutes colonnes |
| `reviews_per_month` null | Remplacé par `0.0` - aucune review ≠ donnée manquante | 20.56 % |
| `last_review` null | Remplacé par `"No review"` | 20.56 % |
| `name` / `host_name` null | Remplacé par `"Unknown"` | ~0.04 % |
| Prix ≤ 0 | Supprimés - logement gratuit incohérent pour la prédiction | 11 lignes |
| `minimum_nights` > 365 | Supprimés - valeurs aberrantes (jusqu'à 1 250 nuits) | 14 lignes |
| Déduplication sur `id` | Garantit l'idempotence en cas de ré-ingestion | - |

**Sortie :** Parquet partitionné par `neighbourhood_group` - 5 partitions (partition pruning efficace)

---

## Script 2 — `silver_to_gold.py`

> Lecture Silver · Feature Engineering · KPI Dashboard

### Gold ML — features pour le Data Scientist

| Feature | Type | Description |
|---------|------|-------------|
| `price_log` | Numérique | Logarithme du prix - normalise la distribution |
| `has_reviews` | Binaire | Indicateur d'activité du listing |
| `occupancy_rate` | Numérique | Taux d'occupation estimé |
| `zone_avg_price` | Numérique | Prix moyen de la zone géographique |
| `price_vs_zone_pct` | Numérique | Écart relatif au prix moyen de zone |
| `zone_type_avg_price` | Numérique | Prix moyen zone × type de logement |

### Gold Dashboard — KPI pour le Data Analyst

**15 lignes agrégées** (5 zones × 3 types) · Métriques : prix moyen · médian · min · max · disponibilité · reviews

---

## Résultats du pipeline

<div align="center">

| Métrique | Valeur |
|----------|--------|
| Lignes Bronze | 48 895 |
| Lignes Silver | 48 870 |
| Lignes retirées | 25 (0.05 %) |
| Taux de rétention | **99.95 %** |
| Partitions Silver | 5 arrondissements NYC |
| Table ML Gold | 48 870 lignes × 22 colonnes |
| KPI Dashboard Gold | 15 lignes agrégées |

</div>

---

## Propriétés garanties

| Propriété | Description |
|-----------|-------------|
| 100 % PySpark | Aucune opération pandas - traitement entièrement distribué |
| Idempotent | `mode("overwrite")` - relançable sans duplication des données |
| Sans credential | `S3_USERNAME` via variable d'environnement · accès S3 géré par Onyxia |
| Gouvernance Medallion | Silver alimentée depuis Bronze uniquement · Gold depuis Silver uniquement |
| Tolérance aux pannes | Spark recalcule automatiquement les partitions perdues (OOMKill Kubernetes) |

---

## Lancement

**Pré-requis :** Service Jupyter PySpark lancé sur Onyxia · Dossiers S3 créés · CSV brut présent en Bronze

```bash
cd ~/work/data-factory

# Étape 1 _ Bronze vers Silver
python src/engineering/bronze_to_silver.py

# Étape 2 - Silver vers Gold
python src/engineering/silver_to_gold.py

# Avec un bucket S3 personnalisé
S3_USERNAME=votre_user python src/engineering/bronze_to_silver.py
```

**Vérification :**

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
