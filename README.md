# Infrastructure Data — Onyxia

## Projet Data Factory — M2 IMSD

Auteur : Amal  
Plateforme : Onyxia /   
Architecture : Medallion (Bronze / Silver / Gold)

---
# 1. Vue d'ensemble du projet

## Sujet du projet

Analyse des données Airbnb et prédiction des prix des logements.
<img width="921" height="413" alt="image" src="https://github.com/user-attachments/assets/82d4302d-90a7-4d65-a952-9fe8247fb345" />


## Dataset

Source :
https://www.kaggle.com/datasets/dgomonov/new-york-city-airbnb-open-data

Format :
CSV

Volume :

- environ 50 000 annonces Airbnb ;
- plusieurs millions de lignes potentielles après intégration des données de disponibilité (calendar) et des reviews ;
- plusieurs centaines de Mo de données.

Cette volumétrie justifie l'utilisation de Spark pour les traitements distribués et les transformations à grande échelle.

Contenu :
- prix
- quartier
- type de logement
- disponibilité
- nombre de reviews
- localisation

## Pourquoi Spark ?

Bien que le dataset principal contienne environ 50 000 annonces, l'intégration des données complémentaires (reviews, disponibilités et historiques) augmente significativement le volume de données à traiter.

L'utilisation de Spark permet :

le traitement distribué ;
l'exécution parallèle des transformations ;
une meilleure scalabilité ;
la reproductibilité des traitements ;
la gestion efficace de volumes de données plus importants.

## Objectifs

Cette infrastructure permet de :

- stocker les données du projet dans une architecture organisée,
- traiter les données avec Spark,
- séparer les données brutes, nettoyées et exploitables,
- permettre aux membres du projet de reproduire facilement l’environnement.

L’environnement a été testé avec :
- stockage S3 ,
- Spark sur Onyxia,
- lecture et écriture de données depuis/vers S3.
- l'utilisation du Hive Metastore pour le catalogage des tables.

---
# 2. Architecture

## Architecture globale

```text
Dataset Airbnb (Kaggle)
          |
          v
   Bronze (S3)
  Données brutes CSV
          |
          v
    Spark PySpark
 Nettoyage / Validation
          |
          v
   Silver (Parquet)
          |
          v
   Hive Metastore
 Catalogage des tables
          |
          v
      Gold
  Features & KPI
      /    \
     /      \
    v        v
 ML Model  Dashboard
```

---

## Architecture Medallion

## Bronze

Zone contenant les données brutes récupérées depuis les sources externes.

Caractéristiques :
- données jamais modifiées,
- conservation de la source originale,
- historique préservé.

Exemple :
```text
s3a://amalam/bronze/airbnb/raw/
```

---

## Silver

Zone contenant les données nettoyées et validées.

Caractéristiques :
- schémas corrigés,
- types cohérents,
- données filtrées,
- valeurs manquantes traitées.

Exemple :
```text
s3a://amalam/silver/airbnb/cleaned/
```

---

## Gold

Zone contenant les données prêtes à être utilisées :
- machine learning,
- statistiques,
- dashboards,
- reporting.

Exemples :
```text
s3a://amalam/gold/ml/
s3a://amalam/gold/dashboard/
```
## Organisation S3

```text
amalam/
├── bronze/
│   └── airbnb/
│       └── raw/
│
├── silver/
│   └── airbnb/
│       └── cleaned/
│
├── gold/
│   ├── ml/
│   └── dashboard/
│
└── logs/
```

Description :

- Bronze : stockage des données Airbnb brutes.
- Silver : stockage des données nettoyées et transformées.
- Gold : stockage des datasets prêts pour le Machine Learning et les dashboards.
- Logs : stockage éventuel des journaux d'exécution.

---

# 3. Services utilisés sur Onyxia

## Jupyter PySpark

Un seul service Jupyter PySpark a été utilisé sur Onyxia.

Ce service permet :
- l’exécution des notebooks,
- l’utilisation de Spark,
- la lecture des données depuis S3,
- l’écriture des données vers Silver.

---

## S3 

Utilisé pour :

* stockage des datasets,
* séparation des zones Bronze/Silver/Gold,
* persistance des données.


## Hive Metastore

Hive Metastore permet de centraliser les métadonnées des tables utilisées par Spark.

Utilisation dans le projet :

- cataloguer les tables Silver et Gold ;
- faciliter les requêtes SQL avec Spark ;
- partager une structure de données commune entre les membres de l'équipe.




# 4. Répartition des responsabilités

| Rôle | Lecture Bronze | Écriture Silver | Lecture Gold | Écriture Gold |
|--------|--------|--------|--------|--------|
| Architecte Data | Oui | Non | Oui | Non |
| Data Engineer | Oui | Oui | Oui | Non |
| Data Scientist | Non | Non | Oui | Oui (ml/) |
| Data Analyst | Non | Non | Oui | Oui (dashboard/) |



Gouvernance des données

Les règles suivantes sont appliquées :

- Bronze : données brutes, aucune modification manuelle.
- Silver : uniquement alimentée par les pipelines ETL.
- Gold : uniquement alimentée à partir de Silver.
- Aucun utilisateur ne modifie directement les données d'une autre couche.
- Toutes les transformations doivent être traçables dans Git.





# 5 Déploiement de l’environnement



todo


# 8. Guide d’onboarding


todo
<img width="765" height="92" alt="{1900B377-1E57-46F7-97F6-84674EFBD38B}" src="https://github.com/user-attachments/assets/69cd546f-851c-436a-b5c7-43b0dae1dd13" />





# 9. Reproductibilité et régénération des données

Le stockage S3 sur Onyxia étant temporaire, les données doivent pouvoir être recréées à tout moment.

Le projet prévoit :

- un script d’ingestion permettant de télécharger les données Airbnb depuis Kaggle ;
- les scripts de transformation Bronze → Silver ;
- les scripts de transformation Silver → Gold ;
- un script bootstrap permettant de reconstruire l’environnement.

Exemple :

```bash
./bootstrap.sh
```

Ce script permettra :

- de recréer l’arborescence S3 ;
- de récupérer les données Airbnb ;
- d’alimenter la zone Bronze ;
- d’exécuter les premiers traitements.

# 10. Structure du dépôt Git

```text
data-factory/

├── src/
│
│   ├── ingestion/
│   │   └── download_airbnb.py
│
│   ├── engineering/
│   │   ├── bronze_to_silver.py
│   │   └── silver_to_gold.py
│
├── notebooks/
│
│   ├── exploration/
│   │   └── exploration_airbnb.ipynb
│
│   └── modeling/
│       └── prediction_prix.ipynb
│
├── README.md
├── ONBOARDING.md
└── bootstrap.sh
```

Cette organisation sépare clairement :

- le code Data Engineering (scripts Python),
- les notebooks Data Science,
- la documentation,
- les scripts d’initialisation.




# 11. Conclusion

L’infrastructure mise en place permet :

- l’ingestion des données Airbnb ;
- le traitement distribué avec Spark ;
- l’organisation des données selon une architecture Medallion ;
- la séparation Bronze / Silver / Gold ;
- la préparation des données pour les équipes Engineering, Data Science et Analytics ;
- la reconstruction complète de l’environnement à partir du dépôt Git.

L’environnement a été validé par :

- la création de l’architecture S3 ;
- le lancement du cluster Spark ;
- la lecture de données depuis Bronze ;
- l’écriture de données au format Parquet dans Silver ;
- la relecture des données transformées.

Cette infrastructure constitue une base reproductible et scalable pour la réalisation du projet Data Factory sur Onyxia.
