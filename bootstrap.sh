#!/bin/bash

# =====================================================
# Data Factory Airbnb
# Bootstrap Script
# =====================================================

echo ""
echo "======================================"
echo "   DATA FACTORY AIRBNB"
echo "======================================"
echo ""

# Vérification Python
if ! command -v python >/dev/null 2>&1; then
    echo "Erreur : Python n'est pas installé."
    exit 1
fi

# Vérification Kaggle
if ! command -v kaggle >/dev/null 2>&1; then
    echo "Kaggle n'est pas installé."
    echo "Installation de Kaggle..."
    pip install kaggle
fi

# Vérification du token Kaggle
if [ ! -f "$HOME/.kaggle/kaggle.json" ]; then
    echo ""
    echo "Erreur : fichier Kaggle introuvable."
    echo "Veuillez créer :"
    echo "$HOME/.kaggle/kaggle.json"
    echo ""
    echo "Exemple :"
    echo '{'
    echo '  "username":"votre_username",'
    echo '  "key":"votre_api_key"'
    echo '}'
    exit 1
fi

echo ""
echo "======================================"
echo "ETAPE 1 : INGESTION KAGGLE -> BRONZE"
echo "======================================"

python src/ingestion/download_airbnb.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Erreur pendant l'ingestion."
    exit 1
fi

echo ""
echo "======================================"
echo "INGESTION TERMINEE"
echo "======================================"

echo ""
echo "Prochaines étapes du pipeline :"
echo " - Bronze -> Silver"
echo " - Silver -> Gold"
echo " - Exploration"
echo " - Machine Learning"
echo ""

echo "Structure du projet :"
echo "src/ingestion/download_airbnb.py           [OK]"
echo "src/engineering/bronze_to_silver.py        [A développer]"
echo "src/engineering/silver_to_gold.py          [A développer]"
echo "notebooks/exploration/exploration_airbnb.ipynb"
echo "notebooks/modeling/prediction_prix.ipynb"

echo ""
echo "Bootstrap terminé avec succès."
echo ""
