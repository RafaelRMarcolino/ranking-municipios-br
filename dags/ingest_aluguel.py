from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from datetime import datetime
import os
import pandas as pd
import json
import boto3
from io import BytesIO

BUCKET = "ranking-municipios-br"

@dag(
    dag_id="ingest_aluguel_kaggle_athena",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["aluguel", "bronze", "athena"]
)
def ingest_aluguel_kaggle_athena():

    @task()
    def processar_e_salvar_s3(execution_date=None) -> str:
        # Configurar credenciais do Kaggle
        conn = BaseHook.get_connection("kaggle_default")
        kaggle_json = {"username": conn.login, "key": conn.password}
        os.makedirs("/home/astro/.kaggle", exist_ok=True)
        with open("/home/astro/.kaggle/kaggle.json", "w") as f:
            json.dump(kaggle_json, f)
        os.chmod("/home/astro/.kaggle/kaggle.json", 0o600)

        # Baixar dataset
        os.makedirs("/tmp/data_kaggle", exist_ok=True)
        os.system("kaggle datasets download -d shwaubh/updated-brasilian-housing-to-rent -p /tmp/data_kaggle --unzip")

        # Ler CSV
        files = os.listdir("/tmp/data_kaggle")
        csv_file = next((f for f in files if f.endswith(".csv")), None)
        df = pd.read_csv(f"/tmp/data_kaggle/{csv_file}")

        # Padronizar nomes das colunas
        df.columns = [
            col.strip().lower().replace(" ", "_").replace("-", "_")
            for col in df.columns
        ]

        # Garantir tipos compatíveis
        df["id"] = df["id"].astype(int)
        df["city"] = df["city"].astype(str)
        df["area"] = df["area"].astype("Int64")
        df["rooms"] = df["rooms"].astype("Int64")
        df["bathroom"] = df["bathroom"].astype("Int64")
        df["parking_spaces"] = df["parking_spaces"].astype("Int64")
        df["floor"] = df["floor"].astype("Int64")
        df["animal"] = df["animal"].astype("Int64")
        df["furniture"] = df["furniture"].astype("Int64")
        df["hoa"] = df["hoa"].astype("Int64")
        df["rent_amount"] = df["rent_amount"].astype("Int64")
        df["property_tax"] = df["property_tax"].astype("Int64")
        df["fire_insurance"] = df["fire_insurance"].astype("Int64")
        df["total"] = df["total"].astype("Int64")

        # Adicionar coluna de partição
        exec_dt = execution_date
        data_carga_str = exec_dt.strftime("%Y-%m-%d")
        df["data_carga"] = data_carga_str

        # Salvar em Parquet
        buffer = BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)

        # Enviar ao S3 com partição única
        aws_conn = BaseHook.get_connection("aws_s3")
        s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_conn.login,
            aws_secret_access_key=aws_conn.password,
            region_name=json.loads(aws_conn.extra)["region_name"]
        )

        key = f"bronze/aluguel_medio/data_carga={data_carga_str}/aluguel.parquet"
        s3_path = f"s3://{BUCKET}/{key}"
        s3.upload_fileobj(buffer, Bucket=BUCKET, Key=key)

        print(f"✅ Parquet salvo: {s3_path}")
        return s3_path

    executar_msck_repair = AthenaOperator(
        task_id="executar_msck_repair",
        query="MSCK REPAIR TABLE bronze.aluguel_medio",
        database="bronze",
        output_location=f"s3://{BUCKET}/athena-results/",
        workgroup="bronze_workgroup",
        aws_conn_id="aws_s3"
    )

    s3_path = processar_e_salvar_s3()
    executar_msck_repair.set_upstream(s3_path)

dag = ingest_aluguel_kaggle_athena()
