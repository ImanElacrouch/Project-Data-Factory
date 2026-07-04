# Utilisation d'une image de base Python
FROM python:3.10-slim

# Configuration pour eviter les invites interactives lors des installations apt
ENV DEBIAN_FRONTEND=noninteractive

# Installation de Java  et des outils de compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jre-headless \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Definition des variables d'environnement pour Java
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# Definition du repertoire de travail dans le conteneur
WORKDIR /app

# Copie et installation des dependances Python 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du notebook du projet 
COPY predection_prix_airbnb_NN.ipynb .

# Creation des repertoires utilises par le script
RUN mkdir -p /home/onyxia/work/Data-factory/data/gold_ml \
    && mkdir -p /home/onyxia/work/Data-factory/models

# Commande par defaut : execution automatique du notebook en mode headless
CMD ["jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", "predection_prix_airbnb_NN.ipynb"]