import os
from kaggle.api.kaggle_api_extended import KaggleApi
import pandas as pd

DATASET = "dgomonov/new-york-city-airbnb-open-data"

def download():
    print("Starting Kaggle download...")

    api = KaggleApi()
    api.authenticate()

    os.makedirs("data/raw", exist_ok=True)

    api.dataset_download_files(DATASET, path="data/raw", unzip=True)

    print("Download finished")

    # lire le CSV automatiquement
    files = [f for f in os.listdir("data/raw") if f.endswith(".csv")]
    
    if not files:
        raise Exception("No CSV found after download")

    df = pd.read_csv(f"data/raw/{files[0]}")

    print("Dataset shape:", df.shape)

if __name__ == "__main__":
    download()
