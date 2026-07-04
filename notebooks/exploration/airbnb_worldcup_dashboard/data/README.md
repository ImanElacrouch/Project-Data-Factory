# Récupération des données

## Objectif

Ce guide explique comment reconstruire les couches **Silver** et **Gold** du projet Airbnb afin de disposer des données prêtes pour les analyses, les tableaux de bord et les modèles de Machine Learning.

---

## Prérequis

Avant de commencer, vérifier que :

- Le service **Jupyter PySpark** est lancé sur Onyxia.
- Le dépôt GitHub du projet est cloné.
- Un compte Kaggle est configuré.
- Un bucket S3 personnel est disponible.

---

## 1. Cloner le projet

Depuis le terminal :

```bash
cd ~/work

git clone https://github.com/EKOURAOGO/Data-factory.git

cd Data-factory
```

Vérifier que le projet est bien présent :

```bash
ls
```

---

## 2. Définir son bucket S3

Exporter son nom d'utilisateur S3 :

```bash
export S3_USERNAME=<votre_username>
```

Exemple :

```bash
export S3_USERNAME=ielacrouch
```

Vérifier :

```bash
echo $S3_USERNAME
```

---

## 3. Télécharger le dataset Airbnb

Télécharger le dataset depuis Kaggle :

```bash
kaggle datasets download -d dgomonov/new-york-city-airbnb-open-data
```

Décompresser l'archive :

```bash
unzip new-york-city-airbnb-open-data.zip
```

Le fichier obtenu est :

```
AB_NYC_2019.csv
```

---

## 4. Construire la couche Silver

Exécuter le pipeline Bronze → Silver :

```bash
python src/engineering/bronze_to_silver.py
```

Les données nettoyées sont enregistrées dans :

```
s3a://<username>/silver/airbnb/cleaned/
```

---

## 5. Construire la couche Gold

Exécuter le pipeline Silver → Gold :

```bash
python src/engineering/silver_to_gold.py
```

Deux jeux de données sont générés :

### Gold ML

```
s3a://<username>/gold/ml/airbnb_features/
```

Cette table contient les variables enrichies destinées au Data Scientist.

### Gold Dashboard

```
s3a://<username>/gold/dashboard/
```

Cette table contient les indicateurs agrégés destinés au Data Analyst.

---

## 6. Lire les données Gold

Dans un notebook PySpark :

```python
df_ml = spark.read.parquet(
    "s3a://<username>/gold/ml/airbnb_features/"
)

df_dashboard = spark.read.parquet(
    "s3a://<username>/gold/dashboard/"
)
```

---

## 7. Vérifier les données

### Gold ML

```python
df_ml.count()

df_ml.printSchema()

df_ml.show(5)
```

### Gold Dashboard

```python
df_dashboard.count()

df_dashboard.show(truncate=False)
```

---

## Architecture du pipeline

```
AB_NYC_2019.csv
        │
        ▼
Bronze
        │
        ▼
Silver
        │
        ▼
Gold
   ├── ML
   └── Dashboard
```

---

## Résultat

À l'issue de ces étapes, les données sont disponibles dans votre espace S3 personnel :

```
s3a://<username>/gold/ml/airbnb_features/

s3a://<username>/gold/dashboard/
```

Ces jeux de données peuvent ensuite être utilisés pour :

- la construction des tableaux de bord ;
- l'analyse des données ;
- l'entraînement des modèles de Machine Learning.
