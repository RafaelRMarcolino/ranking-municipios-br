from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from airflow.hooks.base import BaseHook
from airflow.utils.dates import days_ago
from datetime import datetime
import pandas as pd
import boto3
import json
import requests
from io import BytesIO

BUCKET = "ranking-municipios-br"

def salvar_populacao_full(ds, **kwargs):
    data_carga = datetime.strptime(ds, "%Y-%m-%d").date().isoformat()

    # 🔗 Conexão HTTP do Airflow
    conn = BaseHook.get_connection('ibge_api')
    url = f"{conn.host}{conn.extra_dejson['endpoint']}"
    print(f"Baixando Excel do IBGE: {url}")

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"❌ Erro ao baixar o arquivo: {response.status_code}")

    xls = pd.ExcelFile(BytesIO(response.content))

    # Aba 'BRASIL E UFs'
    df_uf = pd.read_excel(xls, sheet_name="BRASIL E UFs", skiprows=2)
    df_uf.columns = ["unidade_federativa", "populacao"]
    df_uf["populacao"] = (
        df_uf["populacao"]
        .astype(str)
        .str.replace(r"[^\d]", "", regex=True)
        .replace("", pd.NA)
        .astype("Int64")
    )
    df_uf["data_carga"] = data_carga

    # Aba 'MUNICÍPIOS'
    df_mun = pd.read_excel(xls, sheet_name="MUNICÍPIOS", skiprows=1)
    df_mun = df_mun[["UF", "COD. UF", "COD. MUNIC", "NOME DO MUNICÍPIO", "POPULAÇÃO ESTIMADA"]]
    df_mun.columns = ["uf", "cod_uf", "cod_municipio", "municipio", "populacao"]

    for col in ["cod_uf", "cod_municipio", "populacao"]:
        df_mun[col] = (
            df_mun[col]
            .astype(str)
            .str.replace(r"[^\d]", "", regex=True)
            .replace("", pd.NA)
            .astype("Int64")
        )
    df_mun["data_carga"] = data_carga

    # Conexão com S3
    s3_conn = BaseHook.get_connection('aws_s3')
    s3 = boto3.client(
        's3',
        aws_access_key_id=s3_conn.login,
        aws_secret_access_key=s3_conn.password,
        region_name=json.loads(s3_conn.extra)["region_name"]
    )

    def salvar_parquet(df, path_key):
        buffer = BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)
        s3.put_object(Bucket=BUCKET, Key=path_key, Body=buffer.getvalue())
        print(f"✅ Parquet salvo: s3://{BUCKET}/{path_key}")

    # Salvar com nova partição
    salvar_parquet(df_uf, f"bronze/ibge/populacao_estimada/brasil_uf/data_carga={data_carga}/populacao_uf.parquet")
    salvar_parquet(df_mun, f"bronze/ibge/populacao_estimada/municipios/data_carga={data_carga}/populacao_municipios.parquet")


# DAG
default_args = {"owner": "airflow", "start_date": days_ago(1)}

with DAG(
    dag_id="ibge_populacao_full",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=True,
    tags=["ibge", "populacao", "bronze"]
) as dag:

    upload_task = PythonOperator(
        task_id="upload_populacao_ufs_municipios",
        python_callable=salvar_populacao_full,
        provide_context=True,
        op_kwargs={"ds": "{{ ds }}"},
    )

    repair_ufs = AthenaOperator(
        task_id="msck_repair_populacao_uf",
        query="MSCK REPAIR TABLE bronze.populacao_estimada_uf",
        database="bronze",
        output_location=f"s3://{BUCKET}/athena-results/",
        workgroup="bronze_workgroup",
        aws_conn_id="aws_s3"
    )

    repair_municipios = AthenaOperator(
        task_id="msck_repair_populacao_municipios",
        query="MSCK REPAIR TABLE bronze.populacao_estimada_municipios",
        database="bronze",
        output_location=f"s3://{BUCKET}/athena-results/",
        workgroup="bronze_workgroup",
        aws_conn_id="aws_s3"
    )

    upload_task >> [repair_ufs, repair_municipios]
