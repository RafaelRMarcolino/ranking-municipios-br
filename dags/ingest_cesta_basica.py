from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.hooks.base import BaseHook
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import boto3
import json
from io import StringIO


from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from include.dieese.task import inserir_cesta_basica_postgres

# Caminho do CSV local já baixado manualmente
ARQUIVO_CSV_LOCAL = 'include/data/data_cesta.xls'  # ajuste se o nome estiver diferente

# Função principal de leitura e envio ao S3
def salvar_csv_local_para_s3(ds):
    # Lê o arquivo CSV
    df = pd.read_excel(ARQUIVO_CSV_LOCAL)


    # Salva como CSV em buffer
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)

    # Conecta ao S3 via Airflow Connection
    conn = BaseHook.get_connection('aws_s3')
    s3 = boto3.client(
        's3',
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=json.loads(conn.extra).get('region_name', 'us-east-1'),
        endpoint_url=json.loads(conn.extra).get('endpoint_url')  # útil se usar MinIO
    )

    # Data de execução (para particionar o caminho)
    data_execucao = datetime.strptime(ds, "%Y-%m-%d")
    ano = data_execucao.year
    mes = data_execucao.month
    dia = data_execucao.day

    # Bucket e chave do S3
    bucket = "ranking-municipios-br"
    key = f"bronze/dieese/cesta_basica/ano={ano}/mes={mes:02d}/cesta_basica_valor.csv"

    # Upload
    s3.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())
    return json.dumps(df.head(5).to_dict(orient='records'))


# DAG
@dag(
    schedule_interval=None,  # executa manualmente
    start_date=days_ago(1),
    catchup=False,
    tags=["dieese", "cesta_basica", "s3"]
)
def ingesta_cesta_basica_s3():

    task = PythonOperator(
        task_id="upload_csv_to_s3",
        python_callable=salvar_csv_local_para_s3,
        op_kwargs={"ds": "{{ ds }}"},
    )

    task

ingesta_cesta_basica_s3()




def build_cesta_path(execution_date):
    return execution_date.strftime("s3://ranking-municipios-br/bronze/dieese/cesta_basica/ano=%Y/mes=%m/cesta_basica_valor.csv")

def wrapper(**kwargs):
    execution_date = kwargs['execution_date']
    csv_path = build_cesta_path(execution_date)
    inserir_cesta_basica_postgres(csv_path, conn_id="postgres_rds")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 1),
}

dag = DAG(
    dag_id='insert_cesta_basica_rds',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['dieese', 'rds']
)

inserir = PythonOperator(
    task_id="inserir_dados_postgres",
    python_callable=wrapper,
    provide_context=True,
    dag=dag
)

inserir
