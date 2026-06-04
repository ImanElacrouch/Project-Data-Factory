import os
from kaggle.api.kaggle_api_extended import KaggleApi
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("ingestion").getOrCreate()

DATASET = "dgomonov/new-york-city-airbnb-open-data"

# Get absolute path to ensure consistency across environments
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
BRONZE_PATH = os.path.normpath(os.path.join(BASE_PATH, "../../data/bronze"))
BRONZE_PATH = os.path.abspath(BRONZE_PATH)  # Force absolute path

# S3 paths
S3_BRONZE_PATH = "s3a://amalam/bronze/airbnb/raw/"

def download():
    """Download Airbnb dataset from Kaggle"""
    print(f"Downloading dataset to: {BRONZE_PATH}")
    
    api = KaggleApi()
    api.authenticate()

    os.makedirs(BRONZE_PATH, exist_ok=True)

    api.dataset_download_files(
        DATASET,
        path=BRONZE_PATH,
        unzip=True
    )

    print(f"Files in {BRONZE_PATH}:")
    files = os.listdir(BRONZE_PATH)
    for f in files:
        print(f"  - {f}")
    
    return files


def push_to_s3():
    """Read CSV and push to S3 as Parquet"""
    file_path = os.path.join(BRONZE_PATH, "AB_NYC_2019.csv")
    
    print(f"Looking for file: {file_path}")
    print(f"File exists (Python check): {os.path.exists(file_path)}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    # Read with explicit absolute path using file:// URI
    file_uri = f"file://{file_path}"
    print(f"Reading from Spark: {file_uri}")
    
    try:
        df = spark.read.option("header", "true").option("inferSchema", "true").csv(file_uri)
        print(f"Successfully read {df.count()} rows")
        
        # Write to S3
        print(f"Writing to S3: {S3_BRONZE_PATH}")
        df.write.mode("overwrite").parquet(S3_BRONZE_PATH)
        
        print("✓ Successfully uploaded to S3!")
        
    except Exception as e:
        print(f"✗ Error during read/write: {e}")
        raise


if __name__ == "__main__":
    download()
    push_to_s3()
