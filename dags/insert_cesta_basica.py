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
BUCKET = "ranking-municipios-br"

def salvar_parquet_local_para_s3(ds, ti):
    # Carregar Excel
    df = pd.read_excel(ARQUIVO_XLS_LOCAL)

    # Normalizar colunas
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df = df.rename(columns={"data": "data_mes"})

    # Ajustar formatos de data
    df["data_mes"] = pd.to_datetime(df["data_mes"]).dt.strftime("%Y-%m-%d")
    data_carga = pd.to_datetime(ds).strftime("%Y-%m-%d")

    # ❌ Não incluir 'data_carga' como coluna (é usada apenas na partição)
    # df["data_carga"] = data_carga

    # Conectar ao S3
    conn = BaseHook.get_connection('aws_s3')
    s3 = boto3.client(
        's3',
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=json.loads(conn.extra).get('region_name', 'us-east-1'),
        endpoint_url=json.loads(conn.extra).get('endpoint_url')  # opcional
    )

    # Caminho particionado
    key = f"bronze/dieese/cesta_basica/data_carga={data_carga}/cesta_basica_valor.parquet"
    s3_path = f"s3://{BUCKET}/{key}"

    # Escrever em Parquet
    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3.upload_fileobj(buffer, BUCKET, key)

    ti.xcom_push(key="parquet_s3_path", value=s3_path)
    print(f"✅ Parquet salvo: {s3_path}")

# DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 1),
}

with DAG(
    dag_id='ingest_cesta_basica_full',
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
        output_location=f's3://{BUCKET}/athena-results/',
        workgroup='bronze_workgroup',
        aws_conn_id='aws_s3'
    )

    upload_task >> executar_msck_repair
