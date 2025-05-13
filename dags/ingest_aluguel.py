from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from datetime import datetime
import os
import pandas as pd
import json
import boto3
from io import BytesIO
from include.aluguel.task import inserir_aluguel_postgres_parquet

@dag(
    dag_id="ingest_aluguel_kaggle_rds",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["aluguel", "bronze", "rds"]
)
def ingest_aluguel_kaggle_rds():

    @task()
    def processar_e_salvar_s3(execution_date=None) -> str:
        # Configura credenciais do Kaggle
        conn = BaseHook.get_connection("kaggle_default")
        kaggle_json = {"username": conn.login, "key": conn.password}
        os.makedirs("/home/astro/.kaggle", exist_ok=True)
        with open("/home/astro/.kaggle/kaggle.json", "w") as f:
            json.dump(kaggle_json, f)
        os.chmod("/home/astro/.kaggle/kaggle.json", 0o600)

        # Baixa o dataset
        os.makedirs("/tmp/data_kaggle", exist_ok=True)
        os.system("kaggle datasets download -d shwaubh/updated-brasilian-housing-to-rent -p /tmp/data_kaggle --unzip")

        # Processa CSV
        files = os.listdir("/tmp/data_kaggle")
        csv_file = next((f for f in files if f.endswith(".csv")), None)
        df = pd.read_csv(f"/tmp/data_kaggle/{csv_file}")

        # Normaliza e sanitiza colunas
        df.columns = [col.strip().lower().replace(" ", "_").replace("-", "_") for col in df.columns]

        # Salva Parquet no S3
        aws_conn = BaseHook.get_connection("aws_s3")
        s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_conn.login,
            aws_secret_access_key=aws_conn.password,
            region_name=json.loads(aws_conn.extra).get("region_name")
        )

        bucket = "ranking-municipios-br"
        prefix = execution_date.strftime("bronze/aluguel/%Y/%m/")
        key = f"{prefix}aluguel_medio_por_cidade.parquet"
        s3_path = f"s3://{bucket}/{key}"

        buffer = BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)
        s3.upload_fileobj(buffer, Bucket=bucket, Key=key)

        return s3_path

    @task()
    def inserir_no_rds(s3_path: str, execution_date=None):
        data_carga = execution_date.date()
        inserir_aluguel_postgres_parquet(s3_path, conn_id="postgres_rds", data_carga=data_carga)

    inserir_no_rds(processar_e_salvar_s3())

dag = ingest_aluguel_kaggle_rds()
