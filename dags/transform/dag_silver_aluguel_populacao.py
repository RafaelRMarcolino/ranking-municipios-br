from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from datetime import datetime

# Subclasse para evitar que o bash_command seja tratado como Jinja template
class RawBashOperator(BashOperator):
    template_fields = []  # Desativa renderização Jinja no campo bash_command

BUCKET = "ranking-municipios-br"

@dag(
    dag_id="silver_aluguel_populacao",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["silver", "aluguel", "populacao"]
)
def silver_aluguel_populacao():
    
    transformar_dados_silver = RawBashOperator(
        task_id="transformar_dados_silver",
        bash_command="bash /usr/local/airflow/dags/scripts/run_silver.sh",
        do_xcom_push=False
    )

    msck_repair = AthenaOperator(
        task_id="msck_repair_silver",
        query="MSCK REPAIR TABLE silver.aluguel_populacao",
        database="silver",
        output_location=f"s3://{BUCKET}/athena-results/",
        workgroup="silver_workgroup",
        aws_conn_id="aws_s3"
    )

    transformar_dados_silver >> msck_repair

silver_aluguel_populacao_dag = silver_aluguel_populacao()
