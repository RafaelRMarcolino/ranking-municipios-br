from airflow.decorators import dag, task
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from datetime import datetime
from transformations.transform_silver_aluguel_populacao import transformar_dados_silver

BUCKET = "ranking-municipios-br"

@dag(
    dag_id="silver_aluguel_populacao",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["silver", "aluguel", "populacao"]
)
def silver_aluguel_populacao():

    @task(task_id="transformar_dados_silver")
    def executar_transformacao(**kwargs):
        data_carga = kwargs['logical_date'].strftime('%Y-%m-%d')
        print(f"✅ Executando transformação para data_carga={data_carga}")
        transformar_dados_silver(data_carga=data_carga)

    transformar = executar_transformacao()

    msck_repair = AthenaOperator(
        task_id="msck_repair_silver",
        query="MSCK REPAIR TABLE silver.aluguel_populacao",
        database="silver",
        output_location=f"s3://{BUCKET}/athena-results/",
        workgroup="silver_workgroup",
        aws_conn_id="aws_s3"
    )

    transformar >> msck_repair

silver_aluguel_populacao_dag = silver_aluguel_populacao()