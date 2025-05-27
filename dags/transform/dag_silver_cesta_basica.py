from airflow.decorators import dag, task
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from datetime import datetime
from utils.transform_silver_cesta_basica import transform_silver_cesta_basica

BUCKET = "ranking-municipios-br"

@dag(
    dag_id="silver_cesta_basica",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["silver", "cesta_basica"]
)
def silver_cesta_basica():

    @task(task_id="transform_silver_cesta_basica")
    def executar_transformacao(**kwargs):
        data_carga = kwargs['logical_date'].strftime('%Y-%m-%d')
        print(f"✅ Executando transformação da cesta básica para data_carga={data_carga}")
        transform_silver_cesta_basica(data_carga=data_carga)

    transformar = executar_transformacao()

    msck_repair = AthenaOperator(
        task_id="msck_repair_silver_cesta_basica",
        query="MSCK REPAIR TABLE silver.cesta_basica_full",
        database="silver",
        output_location=f"s3://{BUCKET}/athena-results/",
        workgroup="silver_workgroup",
        aws_conn_id="aws_s3"
    )

    transformar >> msck_repair

silver_cesta_basica_dag = silver_cesta_basica()

