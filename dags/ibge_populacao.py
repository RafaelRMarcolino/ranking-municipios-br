from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.hooks.base import BaseHook
from airflow.sensors.base import PokeReturnValue
from airflow.operators.python import PythonOperator
from include.ibge.task import baixar_arquivo_ibge
from datetime import datetime

@dag(
    schedule_interval='@daily', 
    start_date=days_ago(1),
    catchup=False,
    tags=["ibge", "populacao", "bronze"],
)
def ibge_populacao():

    @task.sensor(poke_interval=30, timeout=300, mode='poke')
    def is_api_available() -> PokeReturnValue:
        import requests

        api = BaseHook.get_connection('ibge_api')
        url = f"{api.host}{api.extra_dejson['endpoint']}"
        print(f"URL verificada: {url}")

        response = requests.head(url) 
        condition = response.status_code == 200 
        return PokeReturnValue(is_done=condition, xcom_value=url)

    download_ibge = PythonOperator(
        task_id='download_ibge',
        python_callable=baixar_arquivo_ibge,
        op_kwargs={'url': '{{ ti.xcom_pull(task_ids="is_api_available") }}'}
    )

    is_api_available() >> download_ibge

ibge_populacao()
