# Data Factory — Pipeline Data Engineer (Airbnb NYC 2019)

Pipeline de traitement des données Airbnb selon l'architecture **Medallion**
(Bronze → Silver → Gold) sur la plateforme Onyxia, en **PySpark**.

Auteur : Kouraogo Emmanuel — rôle **Data Engineer** — M2 IMSD.

---

## 1. Rôle du Data Engineer

Le Data Engineer intervient **après l'Architecte** (qui a ingéré le CSV brut
en Bronze) et **avant le Data Scientist / Data Analyst** (qui consomment la
zone Gold). Sa mission : transformer des données brutes en données **propres,
fiables et documentées**.

| Zone | Contenu | Responsabilité |
|------|---------|----------------|
| Bronze | CSV brut Airbnb (non modifié) | Architecte |
| Silver | Données nettoyées en Parquet | **Data Engineer** |
| Gold | Features ML + KPI dashboard | **Data Engineer** |

---

## 2. Architecture du pipeline

```
Bronze (CSV)                      Silver (Parquet)              Gold (Parquet)
s3a://USER/bronze/airbnb/   -->   s3a://USER/silver/airbnb/  -->  s3a://USER/gold/ml/
AB_NYC_2019.csv                   cleaned/                        s3a://USER/gold/dashboard/
                 [bronze_to_silver.py]            [silver_to_gold.py]
```

---

## 3. Les deux scripts

### `src/engineering/bronze_to_silver.py`
Lit le CSV Bronze, nettoie, écrit en Parquet partitionné dans Silver et
génère un rapport qualité.

**Nettoyages appliqués (chacun justifié dans le code) :**
- **Types corrigés** : les colonnes numériques (price, minimum_nights,
  latitude…) sont lues en `string` depuis le CSV → converties en `int`/`double`.
- **Valeurs manquantes** traitées selon leur sens métier :
  - `reviews_per_month` null (20.56 %) → `0.0` : un null ne signifie pas une
    donnée manquante mais **« aucune review »** (parfaitement corrélé à
    `last_review` null). On NE supprime PAS ces 20 % de listings valides.
  - `last_review` null → `"No review"`.
  - `name` / `host_name` null (~0.04 %) → `"Unknown"`.
- **Lignes aberrantes supprimées** (25 lignes au total, 0.05 %) :
  - prix ≤ 0 (11 lignes) : un logement gratuit n'a pas de sens pour une
    prédiction de prix.
  - `minimum_nights` > 365 (14 lignes) : valeurs aberrantes (jusqu'à 1250
    nuits de minimum).
- **Déduplication** sur la clé `id` : garantit l'idempotence si la source
  est ré-ingérée.

**Sortie** : Parquet partitionné par `neighbourhood_group` (5 arrondissements
= dimension de filtrage la plus fréquente → partition pruning efficace).

### `src/engineering/silver_to_gold.py`
Lit Silver et produit deux jeux Gold :
- **`gold/ml/`** : table au grain listing + 6 features pour le Data Scientist
  (`price_log`, `has_reviews`, `occupancy_rate`, `zone_avg_price`,
  `price_vs_zone_pct`, `zone_type_avg_price`).
- **`gold/dashboard/`** : 15 KPI agrégés par arrondissement × type de logement
  pour le Data Analyst (prix moyen/médian/min/max, disponibilité, reviews).

---

## 4. Propriétés garanties

- **100 % PySpark** : aucune opération pandas sur les données volumineuses,
  tout le traitement est distribué.
- **Idempotent** : les deux scripts utilisent `mode("overwrite")`. On peut
  les relancer autant de fois que voulu sans jamais dupliquer les données.
- **Aucun credential en dur** : le username vient de la variable d'env
  `S3_USERNAME` (défaut `ekouraogo`) ; l'accès S3 est géré par la session
  Spark d'Onyxia (variables `AWS_*` injectées par la plateforme).
- **Gouvernance Medallion** : Silver n'est alimentée que depuis Bronze, Gold
  uniquement depuis Silver. Aucune écriture croisée.

---

## 5. Comment relancer le pipeline de A à Z

### Pré-requis
- Service **Jupyter PySpark** lancé sur Onyxia.
- Dossiers S3 créés : `bronze/`, `silver/`, `gold/ml/`, `gold/dashboard/`.
- CSV brut présent dans Bronze (ingestion de l'Architecte exécutée).

### Étapes (dans un terminal Jupyter)
```bash
cd ~/work/data-factory

# 1. Bronze -> Silver (nettoyage + rapport qualité)
python src/engineering/bronze_to_silver.py

# 2. Silver -> Gold (features ML + KPI dashboard)
python src/engineering/silver_to_gold.py
```

> Si votre bucket S3 n'est pas `ekouraogo`, lancez avec :
> `S3_USERNAME=votre_user python src/engineering/bronze_to_silver.py`

### Vérification
```bash
python -c "
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('verif').getOrCreate()
df = spark.read.parquet('s3a://ekouraogo/silver/airbnb/cleaned/')
print('Lignes Silver:', df.count())
df.groupBy('neighbourhood_group').count().show()
spark.stop()
"
```

---

## 6. Résultats obtenus

| Métrique | Valeur |
|----------|--------|
| Lignes Bronze | 48 895 |
| Lignes Silver | 48 870 |
| Lignes retirées | 25 (0.05 %) |
| Taux de rétention | 99.95 % |
| Partitions Silver | 5 (Bronx, Brooklyn, Manhattan, Queens, Staten Island) |
| Table ML (Gold) | 48 870 lignes × 22 colonnes |
| KPI dashboard (Gold) | 15 lignes (5 zones × 3 types) |

Le rapport qualité détaillé (taux de nulls avant/après par colonne) est
généré dans `reports/quality_report.json` et sur
`s3a://ekouraogo/silver/airbnb/_quality_report/`.

---

## 7. Note sur la tolérance aux pannes

Lors d'un run, un executor Kubernetes peut être *OOMKilled* pendant le
shuffle (visible dans les logs). Spark **recalcule automatiquement** la
partition perdue et le job se termine correctement — c'est l'avantage du
traitement distribué tolérant aux pannes. Pour réduire la pression mémoire,
on peut ajouter `.config("spark.sql.shuffle.partitions", "8")` (200 partitions
par défaut est surdimensionné pour ~49 k lignes).
