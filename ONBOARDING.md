# ONBOARDING - Guide Complet Pas à Pas 

Ce guide vous montre comment reproduire **Data Factory** de zéro.

**Important** : Chaque personne utilise son propre **bucket S3** (remplacer `amalam` par votre username)

---

# TABLE DES MATIÈRES

1. [Créer un compte Kaggle](#1-créer-un-compte-kaggle)
2. [Configuration Onyxia](#2-configuration-onyxia)
3. [Créer les dossiers S3](#3-créer-les-dossiers-s3)
4. [Token Kaggle](#4-configurer-le-token-kaggle)
5. [Cloner le projet](#5-cloner-le-projet)
6. [Modifier pour votre username](#6-modifier-pour-votre-username)
7. [Lancer l'ingestion](#7-lancer-lingestion)
8. [Vérifier les données](#8-vérifier-les-données)
9. [Prochaines étapes](#9-prochaines-étapes)

---

# 1. Créer un compte Kaggle

## Étape 1.1 : Aller sur Kaggle

1. Ouvrir : https://www.kaggle.com/
2. Cliquer sur **"Sign Up"** (en haut à droite)

## Étape 1.2 : Créer le compte

1. Remplir le formulaire :
   - Email
   - Username
   - Password
2. Cliquer **"Create account"**


## Étape 1.3 : Accepter le dataset

1. Aller sur : https://www.kaggle.com/datasets/dgomonov/new-york-city-airbnb-open-data
2. Cliquer **"Join"** pour accepter les conditions
3. Attendre 30 secondes (le dataset sera accessible)

**Kaggle est prêt !**

---

# 2. Configuration Onyxia

## Étape 2.1 : Se connecter à Onyxia

1. Ouvrir : https://onyxia.sh/ 
2. Cliquer **"Login"** ou **"Sign In"**


## Étape 2.2 : Lancer Jupyter PySpark

1. Rechercher **"Jupyter PySpark"**
2. Cliquer sur la carte **"Jupyter PySpark"**
3. Cliquer **"Launch"** (garder les paramètres par défaut)


**Quand c'est prêt** :
- Vous verrez un bouton **"Jupyter"** 
- Cliquer dessus pour ouvrir Jupyter

**Onyxia et Jupyter sont prêts !**

---

# 3. Créer les dossiers S3

## Étape 3.1 : Connaître votre username S3

Votre username S3 = **votre username Onyxia** 

Vous allez créer cette structure :

```
VOTRE_USERNAME/
├── bronze/
│   └── airbnb/
│
├── silver/
│   └── airbnb/
│
└── gold/
    ├── ml/
    └── dashboard/
```

Créer les dossiers dans **Data Storage** → **New Folder**

**Dossiers S3 créés !**

---

# 4. Configurer le Token Kaggle

## Étape 4.1 : Créer le token API Kaggle

1. Aller sur : https://www.kaggle.com/settings/account
2. Cliquer sur **"Create New API Token"**
3. Copier le token

### Le fichier ressemble à :

```json
{
  "username": "monusername",
  "key": "abcdef123456"
}
```

## Étape 4.2 : Configurer dans Jupyter

Exécuter dans le terminal :

```bash
mkdir -p ~/.kaggle
nano ~/.kaggle/kaggle.json
```

Coller :
```json
{
  "username": "monusername",
  "key": "abcdef123456"
}
```

Puis :
```bash
mv kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
ls ~/.kaggle
pip install kaggle
```

**Token Kaggle configuré !**


# 5. Cloner le projet

## Étape 5.1 : Ouvrir le Terminal Jupyter

1. Dans Jupyter, cliquer **"Terminal"**
2. Ou **File → New → Terminal**

## Étape 5.2 : Cloner le dépôt

```bash
git clone https://github.com/solfahamal/data-factory.git
cd data-factory
```

**Projet cloné !**

---

# 6. Modifier pour votre username

## Étape 6.1 : Ouvrir le fichier d'ingestion

**Dans Jupyter** :

1. Naviguer : `data-factory → src → ingestion`
2. Double-cliquer sur **`download_airbnb.py`**

## Étape 6.2 : Modifier le bucket S3

Chercher cette ligne (vers la ligne 16) :

```python
S3_BRONZE_PATH = "s3a://amalam/bronze/airbnb/"
```

**Remplacer `amalam` par VOTRE_USERNAME** :

```python
S3_BRONZE_PATH = "s3a://VOTRE_USERNAME/bronze/airbnb/"
```



## Étape 6.3 : Sauvegarder

- **Ctrl+S** (ou Cmd+S sur Mac)
- Ou **File → Save**

✅ **Fichier modifié et sauvegardé !**

---

# 7. Lancer l'ingestion

## Étape 7.1 : Ouvrir le Terminal

**Dans Jupyter** :

1. Cliquer **"Terminal"**
2. Se placer dans le dossier du projet :

```bash
cd data-factory
```

## Étape 7.2 : Lancer l'ingestion

```bash
python src/ingestion/download_airbnb.py
```

## Étape 7.3 : Attendre et voir les messages

L'ingestion va faire :

1. **Télécharger depuis Kaggle** (~50 MB)
2. **Uploader en S3 Bronze** (votre bucket)


### Output attendu :

```
======================================================================
STEP 1: DOWNLOAD FROM KAGGLE
======================================================================
Downloading to: ...data/bronze

 Downloading from Kaggle...

 Download complete. Files in local Bronze:
   - AB_NYC_2019.csv                 (48.45 MB)

======================================================================
STEP 2: UPLOAD TO S3 BRONZE (CSV FORMAT)
======================================================================

 Reading CSV with pandas...
 Read 48895 rows, 16 columns

 Writing to S3: s3a://VOTRE_USERNAME/bronze/airbnb/AB_NYC_2019.csv
 Successfully uploaded to S3 Bronze!

======================================================================
 INGESTION COMPLETE
======================================================================

Data flow:
  Local Bronze: data/bronze/AB_NYC_2019.csv
  S3 Bronze:    s3a://VOTRE_USERNAME/bronze/airbnb/AB_NYC_2019.csv
======================================================================
```

**Ingestion terminée !**

---

# 8. Vérifier les données

## Étape 8.1 : Vérifier en S3

**Dans un Notebook Jupyter** :

```python

pip install boto3

import boto3

s3 = boto3.client('s3')
username = "VOTRE_USERNAME"  # Remplacer

# Lister les fichiers en Bronze
response = s3.list_objects_v2(
    Bucket=username,
    Prefix="bronze/airbnb/"
)

print("Fichiers en Bronze :")
for obj in response.get('Contents', []):
    size_mb = obj['Size'] / (1024 * 1024)
    print(f"  {obj['Key']} ({size_mb:.2f} MB)")
```


## Étape 8.2 : Vérifier avec Spark

**Dans un Notebook Jupyter** :

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("check_bronze").getOrCreate()

username = "VOTRE_USERNAME"  # Remplacer

# Lire depuis S3 Bronze
df = spark.read.option("header", "true").csv(
    f"s3a://{username}/bronze/airbnb/AB_NYC_2019.csv"
)

print(f"Données Bronze : {df.count()} rows")
print(f"Colonnes : {len(df.columns)}")
print("\nAperçu :")
df.show(5)
```

**Vous devriez voir :**
```
<img width="1462" height="504" alt="{32B253F3-FF76-4E9C-A689-F277740C8980}" src="https://github.com/user-attachments/assets/f2bef69f-4011-4cf2-b97a-039a359d0923" />


```

**Données vérifiées !**

---




## Spark en Jupyter

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("MyApp") \
    .enableHiveSupport() \
    .getOrCreate()

# Lire CSV
df = spark.read.option("header", "true").csv("s3a://VOTRE_USERNAME/bronze/airbnb/AB_NYC_2019.csv")

# Afficher le schéma
df.printSchema()

# Compter les lignes
print(df.count())

# Afficher les premiers enregistrements
df.show(5)

```
<img width="1414" height="815" alt="{6A0B68F4-F7BD-4DFC-8060-6EA641DA1A89}" src="https://github.com/user-attachments/assets/db997225-dc57-45de-bdbc-428356d6753b" />

---

# 9. Troubleshooting

### Token Kaggle non trouvé

```
OSError: Could not find kaggle.json
```

**Solution :**
- Vérifier que `~/.kaggle/kaggle.json` existe
- Refaire l'étape 4


### CSV non trouvé en S3

```
FileNotFoundError: CSV file not found
```

**Solution :**
- Vérifier que vous avez remplacé `amalam` par VOTRE_USERNAME
- Relancer l'ingestion

### Hive table non trouvée

```
AnalysisException: Table not found
```

**Solution :**
```python
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS airbnb_listings
    USING PARQUET
    LOCATION 's3a://VOTRE_USERNAME/silver/airbnb/cleaned/'
""")
```

### Spark ne démarre pas

**Solution :**
- Attendre 5 minutes après le lancement d'Onyxia
- Redémarrer Jupyter PySpark

---

# 10. Structure finale

Après tout, vous aurez :

```
s3://VOTRE_USERNAME/
├── bronze/airbnb/AB_NYC_2019.csv       Données brutes
├── silver/airbnb/cleaned/              À faire (Data Engineer)
├── gold/ml/                            À faire (Data Scientist)
└── gold/dashboard/                     À faire (Data Analyst)

data-factory/
├── src/ingestion/download_airbnb.py    Fait
├── src/engineering/bronze_to_silver.py  À faire
├── notebooks/modeling/prediction_prix.ipynb  À faire
└── notebooks/exploration/exploration_airbnb.ipynb  À faire
```

---

# 11. Conclusion

- **README.md** : Architecture générale
- **ONBOARDING.md** : Ce guide (vous le lisez !)

---

**Vous êtes prêt ! 🚀**

Commencez par l'étape 1 et suivez le guide. Si vous avez des questions, consultez la section **Troubleshooting**.
