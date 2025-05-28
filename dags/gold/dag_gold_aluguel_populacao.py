from airflow.decorators import dag, task
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from datetime import datetime
from transformations.transform_gold_aluguel_populacao import transformar_dados_gold_aluguel_populacao

BUCKET = "ranking-municipios-br"

@dag(
    dag_id="gold_aluguel_populacao",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["gold", "aluguel", "populacao"]
)
def gold_aluguel_populacao():

    @task(task_id="transformar_dados_gold")
    def executar_transformacao(**kwargs):
        data_carga = kwargs['logical_date'].strftime('%Y-%m-%d')
        print(f"✅ [GOLD] Iniciando transformação para data_carga={data_carga}")
        transformar_dados_gold_aluguel_populacao(data_carga=data_carga)

    transformar = executar_transformacao()

    msck_repair = AthenaOperator(
        task_id="msck_repair_gold",
        query="MSCK REPAIR TABLE gold.aluguel_populacao_gold",
        database="gold",
        output_location=f"s3://{BUCKET}/athena-results/",
        workgroup="gold_workgroup",
        aws_conn_id="aws_s3"
    )

    transformar >> msck_repair

gold_aluguel_populacao_dag = gold_aluguel_populacao()
