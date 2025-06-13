from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from airflow.hooks.base import BaseHook
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from datetime import datetime
import os
import json
import boto3
from io import BytesIO
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit

BUCKET = "ranking-municipios-br"

@dag(
    dag_id="bronze_aluguel_pyspark",
    schedule_interval=None,
    start_date=datetime(2025, 5, 1),
    catchup=False,
    tags=["aluguel", "bronze", "pyspark"]
)
def ingest_aluguel_pyspark():

    @task()
    def processar_com_spark() -> str:
        # Obter data de execução
        context = get_current_context()
        execution_date = context["execution_date"]
        data_carga_str = execution_date.strftime("%Y-%m-%d")

        # Kaggle config
        conn = BaseHook.get_connection("kaggle_default")
        kaggle_json = {"username": conn.login, "key": conn.password}
        os.makedirs("/home/astro/.kaggle", exist_ok=True)
        with open("/home/astro/.kaggle/kaggle.json", "w") as f:
            json.dump(kaggle_json, f)
        os.chmod("/home/astro/.kaggle/kaggle.json", 0o600)

        # Download dataset
        os.makedirs("/tmp/data_kaggle", exist_ok=True)
        os.system("kaggle datasets download -d shwaubh/updated-brasilian-housing-to-rent -p /tmp/data_kaggle --unzip")
        csv_file = next((f for f in os.listdir("/tmp/data_kaggle") if f.endswith(".csv")), None)

        # Inicializar SparkSession
        spark = SparkSession.builder \
            .appName("AluguelBronze") \
            .master("spark://spark-master:7077") \
            .getOrCreate()

        # Ler CSV
        df = spark.read.option("header", True).csv(f"/tmp/data_kaggle/{csv_file}")

        # Padronizar colunas
        for col in df.columns:
            df = df.withColumnRenamed(col, col.strip().lower().replace(" ", "_").replace("-", "_"))

        # Adicionar data de carga
        df = df.withColumn("data_carga", lit(data_carga_str))

        # Salvar temporariamente como Parquet
        parquet_path = f"/tmp/aluguel_{data_carga_str}.parquet"
        df.write.mode("overwrite").parquet(parquet_path)

        # Enviar ao S3
        aws_conn = BaseHook.get_connection("aws_s3")
        s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_conn.login,
            aws_secret_access_key=aws_conn.password,
            region_name=json.loads(aws_conn.extra)["region_name"]
        )
        key = f"bronze/aluguel_medio/data_carga={data_carga_str}/aluguel.parquet"

        # Compactar arquivo local em buffer para envio
        buffer = BytesIO()
        local_file = os.popen(f"find {parquet_path} -name '*.parquet' | head -n 1").read().strip()
        with open(local_file, "rb") as f:
            buffer.write(f.read())
        buffer.seek(0)

        s3.upload_fileobj(buffer, BUCKET, key)
        s3_path = f"s3://{BUCKET}/{key}"
        print(f"✅ Parquet salvo: {s3_path}")
        return s3_path

    executar_msck_repair = AthenaOperator(
        task_id="executar_msck_repair",
        query="MSCK REPAIR TABLE bronze.aluguel_medio",
        database="bronze",
        output_location=f"s3://{BUCKET}/athena-results/",
        workgroup="bronze_workgroup",
        aws_conn_id="aws_s3"
    )

    s3_path = processar_com_spark()
    s3_path >> executar_msck_repair

dag = ingest_aluguel_pyspark()
