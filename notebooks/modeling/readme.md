# Prediction des prix Airbnb a New York : Approche par Machine Learning et NLP avec PySpark

## 1. Contexte et Objectifs
Ce projet de Data Science a pour objectif de construire un modele predictif capable d'estimer le prix d'une nuitee pour un logement Airbnb situe a New York. 

Ce travail s'inscrit dans la continuite de la chaine de traitement des donnees. Le point de depart de notre modelisation repose sur la couche "Gold" (donnees raffinees et structurees au format Parquet), preparee et mise a disposition en amont par l'equipe de Data Engineering.

La variable cible (le prix) presentant une forte asymetrie, une transformation logarithmique a ete appliquee au prealable (`price_log`) pour normaliser sa distribution et stabiliser l'apprentissage des algorithmes. Le projet a ete integralement code en Python en s'appuyant sur le framework Big Data PySpark afin de garantir l'integration fluide avec les donnees Gold et la scalabilite du traitement.

## 2. Analyse Exploratoire des Donnees (EDA) et Constats
L'exploration initiale du jeu de donnees a permis de degager plusieurs axes analytiques majeurs qui ont conditionne la suite du projet :

- Valeurs aberrantes et realite metier : L'analyse des distributions (via boxplots) sur des variables telles que le nombre minimum de nuits ou le nombre d'avis a revele une forte dispersion. Ces valeurs extremes n'ont pas ete supprimees car elles refletent la realite asymetrique du marche (locations tres longue duree, biens d'exception).
- Detection de fuite de donnees (Data Leakage) : L'analyse de la matrice de correlation de Pearson a mis en evidence des variables (`price_vs_zone_pct`, `zone_type_avg_price`) presentant une correlation superieure a 0.90 avec la variable cible. Ces champs etant calcules a partir du prix lui-meme, ils ont ete exclus de l'analyse pour eviter de fausser les performances du modele.
- Absence de donnees structurelles : Le jeu de donnees initial ne contient aucune information explicite sur la surface en metres carres ni sur le nombre exact de chambres. L'inspection de la colonne textuelle `name` (titre de l'annonce) a neanmoins montre que les hotes y inscrivent systematiquement la taille du bien (ex: "1 BR", "Studio", "Spacious").

## 3. Ingenierie des Caracteristiques (Feature Engineering)
Pour pallier le manque de donnees structurelles et enrichir l'information fournie aux algorithmes, un pipeline de transformation avance a ete developpe :

- Distances Geospatiales : A partir des coordonnees de latitude et longitude, calcul de la distance euclidienne separant chaque logement de deux points nevralgiques : Times Square (hyper-centre) et l'aeroport international JFK.
- Extraction par Expressions Regulieres (Regex) : Creation de regles pour analyser les titres des annonces et en extraire mathematiquement le nombre de chambres (detection des entiers precedant les termes "BR", "bedroom") ainsi que la typologie du bien (Studio, Loft).
- Traitement du Langage Naturel (NLP) : Utilisation combinee d'un RegexTokenizer, d'un StopWordsRemover et d'un algorithme TF-IDF pour vectoriser le reste du texte et isoler l'impact de mots-cles dits "premium" (luxury, view, renovated).

## 4. Strategie de Modelisation
La modelisation s'est deroulee en deux iterations pour mesurer precisement l'apport du Feature Engineering :

- Iteration 1 (Baseline) : Entrainement de modeles (Regression Lineaire, Random Forest, Gradient Boosting) uniquement sur les donnees numeriques et categorielles brutes.
- Iteration 2 (Modele Avance) : Entrainement sur le jeu de donnees enrichi par les variables geospatiales et NLP( pour extraire des infos a partire de name).

Afin de prevenir les erreurs de saturation de memoire (Out Of Memory) liees a l'expansion de la dimensionnalite par l'encodage One-Hot et le TF-IDF, la profondeur maximale des arbres a ete plafonnee. L'algorithme Gradient Boosting a ete privilegie en augmentant son nombre d'iterations (apprentissage sequentiel), garantissant ainsi endurance et stabilite sur la memoire RAM.

## 5. Resultats et Interpretabilite
Le modele final (Gradient BoostingRegressor) atteint un coefficient de determination (R2) d'environ 0.64.

Atteindre une precision de 64% sur l'explication de la variance des prix immobiliers, en l'absence stricte de metrage carre ou de capacite d'accueil explicite, constitue une performance analytique de tres bon niveau.

L'analyse de l'importance des variables du modele final confirme ce succes : les caracteristiques creees de toutes pieces lors de l'etape d'ingenierie (le nombre de chambres extrait par Regex, l'indicateur de Studio, et les distances geospatiales calcules) se hissent en tete des criteres les plus impactants pour la fixation du prix par l'algorithme.

## 6. Limites et Perspectives
Pour franchir le seuil des 70% ou 80% de precision, l'algorithme a atteint ses limites mathematiques sur ce perimetre de donnees. La perspective d'amelioration principale residerait dans l'enrichissement de la base de donnees source (jointure avec d'autres bases) pour y integrer la surface habitable reelle et les capacites d'accueil.

## 7. Instructions d'Installation et d'Execution

### Prerequis techniques
- Python 3.8 ou superieur
- Apache Spark et Java 8+ installes et configures dans les variables d'environnement
- Minimum 8 Go de RAM sur la machine hote (4 Go alloues au driver Spark)
- Docker (optionnel, pour une execution isolee)

### Installation et Execution locale
1. Clonez ce depot sur votre machine locale.
2. Installez les bibliotheques Python requises via la commande suivante :
   pip install -r requirements.txt
3. Lancez le notebook via Jupyter :
   jupyter notebook predection_prix_airbnb_NN.ipynb

### Execution via Docker (Recommande)
1. Construisez l'image Docker a la racine du projet :
   docker build -t airbnb-model .
2. Lancez le conteneur pour executer le pipeline complet :
   docker run airbnb-model

## 8. Structure du Repertoire
- /data : Contient le fichier source au format parquet (non inclus dans le depot par defaut).
- /models : Repertoire d'exportation cree dynamiquement pour stocker le pipeline entraine (MLOps).
- predection_prix_airbnb_NN.ipynb : Notebook complet incluant l'EDA, le pipeline de Feature Engineering et la modelisation.
- Dockerfile : Configuration pour l'execution automatisee et isolee du projet.
- requirements.txt : Liste des dependances Python.