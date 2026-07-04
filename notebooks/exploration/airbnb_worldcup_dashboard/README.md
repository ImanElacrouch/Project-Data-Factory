# 🏟️ Dashboard Airbnb NYC — Coupe du Monde 2026

> **Question métier :** _« Si des milliers de visiteurs arrivent à New York pour
> la Coupe du Monde 2026, où peuvent-ils se loger à moindre coût tout en
> conservant de bonnes conditions de séjour ? »_

Tableau de bord **Streamlit + Plotly** connecté aux données réelles de la zone
**Gold** (`airbnb_features.csv`, 48 870 logements), déployable tel quel sur
**Onyxia / SSPCloud**. Conçu pour être compris par un décideur non technique en
moins de deux minutes.

Contexte réel : le MetLife Stadium (New York / New Jersey) accueille **8 matchs**
du tournoi du 13 juin au **19 juillet 2026 (finale)** d'où une pression forte
sur le logement et les prix.

---

## 🚀 Démarrage rapide

```bash
pip install -r requirements.txt
streamlit run app.py
```
---

## 🧭 Déploiement sur Onyxia / SSPCloud

Le dashboard a été **testé et validé sur Onyxia / SSPCloud**.

L'erreur **404** rencontrée lors de la première tentative vient du reverse-proxy
Onyxia qui n'expose pas automatiquement le port Streamlit. Procédure fiable :

1. Lancer un service **Jupyter-PySpark** ou **VSCode-python**.
2. Dans la configuration du service → **Networking** → **ouvrir le port `8501`**
   (ou utiliser un port déjà exposé par le service).
3. Cloner / copier ce dossier, puis :
   ```bash
   bash run.sh
   ```
   `run.sh` lance Streamlit avec `--server.enableCORS=false`,
   `--server.enableXsrfProtection=false` et `--server.address=0.0.0.0`,
   réglages indispensables derrière le proxy.
4. Accéder à l'URL proxifiée fournie par Onyxia pour ce port.

## 💡  Déploiement final sur Streamlit

Le dashboard a été développé avec **Streamlit** car il permet de créer rapidement une application web interactive en Python.

Contrairement à **Power BI** ou **Tableau** .., il ne nécessite ni logiciel BI, ni licence, ni compte Microsoft pour consulter le tableau de bord. Une simple **URL** suffit.

Ce choix permet aux utilisateurs d'explorer facilement le marché Airbnb, de filtrer les données et d'obtenir une vision globale afin de prendre rapidement des décisions.

---

## 📊 Les KPI métier

| KPI | Formule | Intérêt métier | Lecture Coupe du Monde |
|-----|---------|----------------|------------------------|
| **Nombre de logements** | `count(id)` | Taille de l'offre disponible | Capacité d'accueil totale |
| **Prix moyen / nuit** | `mean(price)` | Niveau de prix général | Budget moyen à prévoir |
| **Prix médian / nuit** | `median(price)` | Prix typique (robuste aux extrêmes) | Repère plus fiable que la moyenne |
| **Disponibilité moyenne** | `mean(availability_365)` | Tension de l'offre | Reste-t-il de la place ? |
| **Taux d'occupation moyen** | `mean(occupancy_rate)` | Demande réelle | Quartiers déjà très sollicités |
| **Avis moyens / logement** | `mean(number_of_reviews)` | Fiabilité / popularité | Logements éprouvés |
| **Quartier le moins cher** | `argmin` du prix médian par quartier (≥ 30 annonces) | Meilleure opportunité | Où loger pas cher |
| **Quartier le plus cher** | `argmax` du prix médian par quartier | Zone à éviter | Où ne PAS loger |
| **Logements dispo > 180 j** | `count(availability_365 > 180)` | Réserve de capacité | Marge pour absorber l'afflux |

**Score « meilleur compromis »** (page Classement & Recommandations) :
`0,5 × (prix bas) + 0,3 × disponibilité + 0,2 × popularité` (dimensions
normalisées 0–1). Il identifie les quartiers au meilleur rapport qualité/prix.

---

## 📈 Les visualisations & leur justification

| # | Graphique | Type | Pourquoi ce choix |
|---|-----------|------|-------------------|
| 1 | Cartes KPI | `st.metric` | Chiffres clés lisibles en un coup d'œil |
| 2 | Prix médian par arrondissement | Barres horizontales | Comparaison de 5 catégories ordonnées (pas de camembert) |
| 3 | Prix par type de logement | Barres horizontales | 3 catégories à comparer |
| 4 | Carte des logements | `scatter_map` | Dimension géographique = besoin réel de l'utilisateur |
| 5 | Densité des prix | `density_map` (heatmap) | Révèle les zones chères vs abordables |
| 6 | Heatmap arrondissement × type | `imshow` | Matrice prix lisible immédiatement |
| 7 | Distribution des prix | Histogramme + médiane | Montre où se concentre l'offre |
| 8 | Occupation par arrondissement | Barres | Tension de la demande |
| 9 | Disponibilité vs prix | Nuage de points | « Payer plus ≠ trouver de la place » |
| 10 | Avis vs prix | Nuage de points | « Payer plus ≠ meilleure qualité » |
| 11 | Top 10 moins / plus chers | Barres | Recommandations directes |
| 12 | Score compromis | Barres colorées | Synthèse actionnable |

Tous les titres sont **explicites** (ils disent ce qu'on voit, pas ce qu'on mesure).

---



## 🗂️ Architecture

```
airbnb_worldcup_dashboard/
├── app.py                  # point d'entrée + navigation multipage
├── pages/
│   ├── accueil.py          # contexte, KPI, graphiques d'intro
│   ├── carte.py            # carte interactive + heatmap densité
│   ├── prix.py             # heatmap, distribution, croisements
│   ├── quartiers.py        # top 10 + score compromis
│   └── recommandations.py  # storytelling 5 étapes + tableau final
├── components/
│   ├── kpi_cards.py        # cartes KPI réutilisables
│   └── filters.py          # filtres latéraux partagés
├── utils/
│   ├── data_loader.py      # chargement + cache (@st.cache_data)
│   ├── kpis.py             # calculs métier (formules documentées)
│   └── theme.py            # palette, thème Plotly, CSS
├── assets/style.css        # design moderne
├── .streamlit/config.toml  # thème + réglages serveur Onyxia
├── data/airbnb_features.csv
├── requirements.txt
├── run.sh                  # lancement Onyxia
└── README.md
```

Pipeline respecté : **Bronze → Silver → Gold → Dashboard**.

---

## 📖 Storytelling (page Recommandations)

1. Le contexte de la Coupe du Monde 2026 à New York.
2. La demande de logement explose.
3. Ce que révèlent les prix et disponibilités Airbnb.
4. Les quartiers du meilleur compromis prix / disponibilité.
5. Les recommandations finales pour les supporters.
