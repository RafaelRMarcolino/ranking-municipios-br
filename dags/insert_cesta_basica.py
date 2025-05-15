from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from datetime import datetime
import pandas as pd
import boto3
import json
from io import BytesIO

ARQUIVO_XLS_LOCAL = 'include/data/data_cesta.xls'

# Task 1: Salva Parquet no S3 com partição por ano/mês
def salvar_parquet_local_para_s3(ds, ti):
    df = pd.read_excel(ARQUIVO_XLS_LOCAL)
    
    # Normaliza colunas e nomes
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df = df.rename(columns={"data": "data_mes"})

    # Transforma datas para string no formato "YYYY-MM-DD"
    df["data_mes"] = pd.to_datetime(df["data_mes"]).dt.strftime("%Y-%m-%d")
    df["data_carga"] = pd.to_datetime(ds).strftime("%Y-%m-%d")

    # Extrai partições
    data_execucao = datetime.strptime(ds, "%Y-%m-%d")
    df["ano"] = data_execucao.year
    df["mes"] = data_execucao.month

    # Conexão com S3
    conn = BaseHook.get_connection('aws_s3')
    s3 = boto3.client(
        's3',
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=json.loads(conn.extra).get('region_name', 'us-east-1'),
        endpoint_url=json.loads(conn.extra).get('endpoint_url')
    )

    # Caminho final
    key = f"bronze/dieese/cesta_basica/ano={df['ano'][0]}/mes={df['mes'][0]:02d}/cesta_basica_valor.parquet"
    bucket = "ranking-municipios-br"
    s3_path = f"s3://{bucket}/{key}"

    # Grava Parquet
    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3.upload_fileobj(buffer, bucket, key)

    ti.xcom_push(key="parquet_s3_path", value=s3_path)
    print(f"✅ Parquet salvo: {s3_path}")

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
    tags=['dieese', 'bronze', 'athena'],
) as dag:

    upload_task = PythonOperator(
        task_id='upload_parquet_to_s3',
        python_callable=salvar_parquet_local_para_s3,
        provide_context=True,
        op_kwargs={'ds': '{{ ds }}'},
    )

    executar_msck_repair = AthenaOperator(
        task_id='executar_msck_repair',
        query='MSCK REPAIR TABLE bronze.cesta_basica',
        database='bronze',
        output_location='s3://ranking-municipios-br/athena-results/',
        workgroup='bronze_workgroup',
        aws_conn_id='aws_s3'
    )

    upload_task >> executar_msck_repair
