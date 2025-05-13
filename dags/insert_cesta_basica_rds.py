from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime
import pandas as pd
import boto3
import json
from io import BytesIO
from include.dieese.task import inserir_cesta_basica_postgres

ARQUIVO_XLS_LOCAL = 'include/data/data_cesta.xls'

# Task 1: Salva Parquet no S3 com partição por ano/mês e data_carga
def salvar_parquet_local_para_s3(ds, ti):
    df = pd.read_excel(ARQUIVO_XLS_LOCAL)
    df = df.rename(columns={"Data": "data_mes"})
    df["data_mes"] = pd.to_datetime(df["data_mes"])

    # Coluna de data_carga
    df["data_carga"] = pd.to_datetime(ds)

    # Conexão com S3
    conn = BaseHook.get_connection('aws_s3')
    s3 = boto3.client(
        's3',
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=json.loads(conn.extra).get('region_name', 'us-east-1'),
        endpoint_url=json.loads(conn.extra).get('endpoint_url')
    )

    # Caminho Parquet no S3 com partição por ano/mês
    data_execucao = datetime.strptime(ds, "%Y-%m-%d")
    ano = data_execucao.year
    mes = data_execucao.month
    key = f"bronze/dieese/cesta_basica/{ano}/{mes:02d}/cesta_basica_valor.parquet"
    bucket = "ranking-municipios-br"
    s3_path = f"s3://{bucket}/{key}"

    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3.upload_fileobj(buffer, bucket, key)

    ti.xcom_push(key="parquet_s3_path", value=s3_path)
    print(f"✅ Parquet salvo: {s3_path}")

# Task 2: Lê Parquet do S3 e insere no PostgreSQL
def carregar_dados_para_postgres(ti):
    parquet_path = ti.xcom_pull(key="parquet_s3_path", task_ids="upload_parquet_to_s3")
    inserir_cesta_basica_postgres(parquet_path, conn_id="postgres_rds")

# DAG mensal
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 1),
}

with DAG(
    dag_id='ingest_cesta_basica_completa',
    default_args=default_args,
    schedule_interval='@monthly', 
    catchup=True,                  
    tags=['dieese', 'bronze', 'postgres'],
) as dag:

    upload_task = PythonOperator(
        task_id='upload_parquet_to_s3',
        python_callable=salvar_parquet_local_para_s3,
        provide_context=True,
        op_kwargs={'ds': '{{ ds }}'},
    )

    carregar_task = PythonOperator(
        task_id='inserir_dados_postgres',
        python_callable=carregar_dados_para_postgres,
        provide_context=True
    )

    upload_task >> carregar_task
