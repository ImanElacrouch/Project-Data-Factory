#!/usr/bin/env bash
# Lancement du dashboard sur Onyxia / SSPCloud.
# Le service Streamlit est exposé sur le port 8501 derrière le reverse-proxy.
set -e

# Installe les dépendances si nécessaire
pip install -q -r requirements.txt

# Sur Onyxia, exposer le port 8501 dans la configuration du service
# (rubrique "Networking" -> "Open a port" -> 8501) AVANT de lancer.
streamlit run app.py \
  --server.address=0.0.0.0 \
  --server.port=8501 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false
