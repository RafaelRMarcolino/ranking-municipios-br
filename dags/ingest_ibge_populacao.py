from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from airflow.hooks.base import BaseHook
from airflow.sensors.base import PokeReturnValue
from datetime import datetime
import pandas as pd
import requests
import boto3
import json
from io import BytesIO

BUCKET = "ranking-municipios-br"

def build_s3_key(ds):
    dt = datetime.strptime(ds, "%Y-%m-%d")
    return f"bronze/ibge/populacao_estimada/ano={dt.year}/mes={dt.month:02d}/dia={dt.day:02d}/populacao.parquet"


@dag(
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=True,
    tags=["ibge", "populacao", "athena"],
    default_args={"owner": "airflow"},
)
def ibge_populacao_athena():

    @task.sensor(poke_interval=30, timeout=300, mode='poke')
    def is_api_available() -> PokeReturnValue:
        api = BaseHook.get_connection('ibge_api')
        url = f"{api.host}{api.extra_dejson['endpoint']}"
        response = requests.head(url)
        return PokeReturnValue(is_done=(response.status_code == 200), xcom_value=url)

    @task
    def baixar_e_salvar_parquet(url: str, ds: str = None) -> str:
        print(f"🛰️ Iniciando download da API: {url}")
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Erro ao baixar arquivo: {response.status_code}")

        df = pd.read_excel(response.content, skiprows=1)
        df = df[["BRASIL E UNIDADES DA FEDERAÇÃO", "POPULAÇÃO ESTIMADA"]]
        df.columns = ["unidade_federativa", "populacao"]

        df["populacao"] = (
            df["populacao"]
            .astype(str)
            .str.replace(r"[^\d]", "", regex=True)
            .replace("", pd.NA)
            .astype("Int64")
        )

        exec_dt = datetime.strptime(ds, "%Y-%m-%d")
        df["data_carga"] = exec_dt
        df["ano"] = exec_dt.year
        df["mes"] = exec_dt.month
        df["dia"] = exec_dt.day

        print(f"✅ DataFrame carregado com {df.shape[0]} registros")

        buffer = BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)

        conn = BaseHook.get_connection('aws_s3')
        s3 = boto3.client(
            's3',
            aws_access_key_id=conn.login,
            aws_secret_access_key=conn.password,
            region_name=json.loads(conn.extra)['region_name']
        )

        key = f"bronze/ibge/populacao_estimada/ano={exec_dt.year}/mes={exec_dt.month:02d}/dia={exec_dt.day:02d}/populacao.parquet"
        s3.put_object(Bucket=BUCKET, Key=key, Body=buffer.getvalue())
        s3_path = f"s3://{BUCKET}/{key}"
        print(f"✅ Parquet salvo em: {s3_path}")
        return s3_path


    # Task Athena MSCK REPAIR
    executar_msck_repair = AthenaOperator(
        task_id="executar_msck_repair",
        query="MSCK REPAIR TABLE bronze.populacao_estimada",
        database="bronze",
        output_location=f"s3://{BUCKET}/athena-results/",
        workgroup="bronze_workgroup",
        aws_conn_id="aws_s3"
    )

    # Encadeamento
    url = is_api_available()
    s3_path = baixar_e_salvar_parquet(url)
    executar_msck_repair.set_upstream(s3_path)

ibge_populacao_athena()
