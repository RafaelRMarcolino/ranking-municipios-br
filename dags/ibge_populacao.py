from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.hooks.base import BaseHook
from airflow.sensors.base import PokeReturnValue
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import requests
import boto3
import json
from io import StringIO

# Função para baixar e salvar no S3
def baixar_e_salvar_s3(url, ano):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Erro ao baixar arquivo do IBGE: {response.status_code}")

    temp_file = '/tmp/temp_ibge.xls'
    with open(temp_file, 'wb') as f:
        f.write(response.content)

    df = pd.read_excel(temp_file, skiprows=1)

    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)

    conn = BaseHook.get_connection('aws_s3')
    s3 = boto3.client(
        's3',
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=json.loads(conn.extra).get('region_name', 'us-east-1')
    )

    bucket = "ranking-municipios-br"  # Nome do seu bucket na AWS S3
    key = f"bronze/ibge/populacao/ano={ano}/populacao.csv"

    s3.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())
    return json.dumps(df.head(5).to_dict(orient='records'))

# DAG
@dag(
    schedule_interval='@yearly',
    start_date=days_ago(1),
    catchup=True,
    tags=["ibge", "populacao", "s3"]
)
def ibge_populacao():

    @task.sensor(poke_interval=30, timeout=300, mode='poke')
    def is_api_available() -> PokeReturnValue:
        api = BaseHook.get_connection('ibge_api')
        url = f"{api.host}{api.extra_dejson['endpoint']}"
        print(f"URL verificada: {url}")
        response = requests.head(url)
        return PokeReturnValue(is_done=(response.status_code == 200), xcom_value=url)

    def wrapper(ti, ds):
        url = ti.xcom_pull(task_ids="is_api_available")
        ano = ds[:4]
        return baixar_e_salvar_s3(url, ano)

    baixar = PythonOperator(
        task_id="download_ibge_task",
        python_callable=wrapper,
        op_kwargs={"ds": "{{ ds }}"},
    )

    is_api_available() >> baixar

ibge_populacao()
