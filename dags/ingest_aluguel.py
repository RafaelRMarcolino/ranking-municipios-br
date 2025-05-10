from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.hooks.base import BaseHook
from datetime import datetime
import os
import pandas as pd
import json
import boto3
from io import StringIO

@dag(
    dag_id="ingest_aluguel_kaggle_rds",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["aluguel", "bronze"]
)
def ingest_aluguel_kaggle_rds():

    @task()
    def download_kaggle_dataset():
        conn = BaseHook.get_connection("kaggle_default")
        kaggle_json = {
            "username": conn.login,
            "key": conn.password
        }

        os.makedirs("/home/astro/.kaggle", exist_ok=True)
        with open("/home/astro/.kaggle/kaggle.json", "w") as f:
            json.dump(kaggle_json, f)
        os.chmod("/home/astro/.kaggle/kaggle.json", 0o600)

        os.makedirs("/tmp/data_kaggle", exist_ok=True)
        os.system("kaggle datasets download -d shwaubh/updated-brasilian-housing-to-rent -p /tmp/data_kaggle --unzip")

    @task()
    def process_and_upload(execution_date=None):
        # Identifica o CSV baixado
        files = os.listdir("/tmp/data_kaggle")
        csv_file = next((f for f in files if f.endswith(".csv")), None)

        if not csv_file:
            raise FileNotFoundError("Nenhum arquivo CSV encontrado em /tmp/data_kaggle")

        df = pd.read_csv(f"/tmp/data_kaggle/{csv_file}")

        # Normaliza colunas para letras minúsculas
        df.columns = [col.strip().lower() for col in df.columns]

        if 'rent amount' not in df.columns:
            raise KeyError(f"Coluna 'rent amount' não encontrada. Colunas disponíveis: {df.columns}")

        df['rent amount'] = df['rent amount'].replace('[R$ ]', '', regex=True).astype(float)
        media_por_cidade = df.groupby('city')['rent amount'].mean().reset_index()

        # Envio ao S3
        aws_conn = BaseHook.get_connection("aws_s3")
        session = boto3.Session(
            aws_access_key_id=aws_conn.login,
            aws_secret_access_key=aws_conn.password,
            region_name=json.loads(aws_conn.extra).get("region_name")
        )
        s3 = session.client("s3")
        bucket_name = "ranking-municipios-br"
        date_prefix = execution_date.strftime("%Y-%m") if execution_date else "manual"
        prefix = f"bronze/aluguel/{date_prefix}/"

        # CSV
        csv_buffer = StringIO()
        media_por_cidade.to_csv(csv_buffer, index=False)
        s3.put_object(Bucket=bucket_name, Key=f"{prefix}aluguel_medio_por_cidade.csv", Body=csv_buffer.getvalue())

        # JSON
        json_buffer = StringIO()
        media_por_cidade.to_json(json_buffer, orient="records", force_ascii=False)
        s3.put_object(Bucket=bucket_name, Key=f"{prefix}aluguel_medio_por_cidade.json", Body=json_buffer.getvalue())

    download_kaggle_dataset() >> process_and_upload()

dag = ingest_aluguel_kaggle_rds()
