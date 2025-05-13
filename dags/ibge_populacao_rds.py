from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.hooks.base import BaseHook
from airflow.sensors.base import PokeReturnValue
from datetime import datetime
import pandas as pd
import requests
import boto3
import json
from io import StringIO
from include.ibge.task import inserir_populacao_postgres  # ajuste se necessário

BUCKET = "ranking-municipios-br"

def build_s3_key(ds):
    dt = datetime.strptime(ds, "%Y-%m-%d")
    return f"bronze/ibge/populacao/{dt.year}/{dt.month:02d}/{dt.day:02d}/populacao.csv"

@dag(
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=True,
    tags=["ibge", "populacao", "rds"],
    default_args={"owner": "airflow"},
)
def ibge_populacao_rds():

    @task.sensor(poke_interval=30, timeout=300, mode='poke')
    def is_api_available() -> PokeReturnValue:
        api = BaseHook.get_connection('ibge_api')
        url = f"{api.host}{api.extra_dejson['endpoint']}"
        response = requests.head(url)
        return PokeReturnValue(is_done=(response.status_code == 200), xcom_value=url)

    @task
    def baixar_e_salvar_s3(url: str, ds: str = None) -> str:
        print(f"🛰️ Iniciando download da API: {url}")
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Erro ao baixar arquivo: {response.status_code}")

        df = pd.read_excel(response.content, skiprows=1)
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)

        conn = BaseHook.get_connection('aws_s3')
        s3 = boto3.client(
            's3',
            aws_access_key_id=conn.login,
            aws_secret_access_key=conn.password,
            region_name=json.loads(conn.extra)['region_name']
        )

        key = build_s3_key(ds)
        s3_path = f"s3://{BUCKET}/{key}"
        s3.put_object(Bucket=BUCKET, Key=key, Body=csv_buffer.getvalue())
        print(f"✅ Arquivo salvo: {s3_path}")
        return s3_path

    @task
    def inserir_populacao_task(csv_s3_path: str, ds: str = None):
        print(f"📥 Inserindo dados de {csv_s3_path} com data_carga={ds}")
        inserir_populacao_postgres(csv_s3_path, conn_id="postgres_rds", data_carga=ds)

    # ✅ ENCADEAMENTO DAS TASKS (sem .output)
    url = is_api_available()
    s3_path = baixar_e_salvar_s3(url)
    inserir_populacao_task(s3_path)

ibge_populacao_rds()
