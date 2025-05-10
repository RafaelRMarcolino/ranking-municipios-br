from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from include.dieese.task import inserir_cesta_basica_postgres

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
