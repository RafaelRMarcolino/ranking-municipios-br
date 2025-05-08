from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from include.ibge.task import inserir_populacao_postgres

def build_path_from_execution_date(execution_date):
    return execution_date.strftime("s3://ranking-municipios-br/bronze/ibge/populacao/ano=%Y/mes=%m/dia=%d/populacao.csv")

def wrapper(**kwargs):
    execution_date = kwargs['execution_date']
    csv_path = build_path_from_execution_date(execution_date)
    inserir_populacao_postgres(csv_path, conn_id="postgres_rds")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 1),
}

dag = DAG(
    dag_id='insert_populacao_rds',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['ibge', 'rds']
)

inserir = PythonOperator(
    task_id="inserir_dados_postgres",
    python_callable=wrapper,
    provide_context=True,
    dag=dag
)

inserir
