from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from datetime import datetime
import pandas as pd
import boto3
import json
from io import BytesIO, StringIO
import pyarrow as pa
import pyarrow.parquet as pq
import os

BUCKET = "ranking-municipios-br"

CSV_CONTENT = """city,area,rooms,bathroom,parking spaces,floor,animal,furniture,hoa (R$),rent amount (R$),property tax (R$),fire insurance (R$),total (R$)
São Paulo,70,2,1,1,5,acept,furnished,600,2000,100,50,2750
São Paulo,80,3,2,1,7,not acept,not furnished,800,2500,150,80,3530
Rio de Janeiro,60,2,1,1,3,acept,not furnished,400,1800,90,40,2330
Rio de Janeiro,90,3,2,2,9,acept,furnished,900,3000,160,90,4150
Belo Horizonte,55,2,1,0,2,not acept,furnished,350,1500,80,30,1960
Porto Alegre,65,2,2,1,6,acept,not furnished,500,1700,100,50,2350
Curitiba,72,3,2,2,4,acept,furnished,700,2200,120,70,3090
Recife,50,1,1,0,1,not acept,not furnished,300,1300,60,30,1690
Salvador,85,3,3,2,8,acept,furnished,950,2800,180,100,4030
Fortaleza,68,2,2,1,5,not acept,furnished,550,1900,110,60,2620"""

@dag(
    dag_id="ingest_aluguel_unificada",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["aluguel", "bronze", "athena"]
)
def ingest_aluguel_unificada():

    @task()
    def extrair_e_enviar_s3(logical_date=None, fonte="kaggle") -> str:
        if fonte == "csv":
            df = pd.read_csv(StringIO(CSV_CONTENT))
        elif fonte == "kaggle":
            # 🔐 Baixar do Kaggle
            conn = BaseHook.get_connection("kaggle_default")
            kaggle_json = {"username": conn.login, "key": conn.password}
            os.makedirs("/home/astro/.kaggle", exist_ok=True)
            with open("/home/astro/.kaggle/kaggle.json", "w") as f:
                json.dump(kaggle_json, f)
            os.chmod("/home/astro/.kaggle/kaggle.json", 0o600)

            # 📥 Download
            pasta = "/tmp/data_kaggle"
            os.makedirs(pasta, exist_ok=True)
            os.system(f"kaggle datasets download -d shwaubh/updated-brasilian-housing-to-rent -p {pasta} --unzip")
            arquivos = os.listdir(pasta)
            csv_file = next((f for f in arquivos if f.endswith(".csv")), None)
            if not csv_file:
                raise FileNotFoundError(f"Nenhum CSV encontrado em {pasta}")
            df = pd.read_csv(os.path.join(pasta, csv_file))

        # Padronizar colunas
        df.columns = [col.strip().lower().replace(" ", "_").replace("-", "_") for col in df.columns]
        df = df.rename(columns={
            "rent_amount_(r$)": "rent_amount",
            "total_(r$)": "total",
            "hoa_(r$)": "hoa",
            "property_tax_(r$)": "property_tax",
            "fire_insurance_(r$)": "fire_insurance",
            "parking_spaces": "parking_spaces"
        })

        # Selecionar colunas desejadas
        df = df[["city", "area", "rooms", "bathroom", "rent_amount", "total"]]

        # Garantir tipos
        df["area"] = df["area"].fillna(0).astype("int32")
        df["rooms"] = df["rooms"].fillna(0).astype("int32")
        df["bathroom"] = df["bathroom"].fillna(0).astype("int32")
        df["rent_amount"] = df["rent_amount"].fillna(0).astype("int32")
        df["total"] = df["total"].fillna(0).astype("int32")
        df["city"] = df["city"].astype(str)

        # Partição
        data_carga_str = logical_date.strftime("%Y-%m-%d")
        df["data_carga"] = data_carga_str

        # Parquet
        buffer = BytesIO()
        schema = pa.schema([
            ("city", pa.string()),
            ("area", pa.int32()),
            ("rooms", pa.int32()),
            ("bathroom", pa.int32()),
            ("rent_amount", pa.int32()),
            ("total", pa.int32()),
            ("data_carga", pa.string())
        ])
        table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
        pq.write_table(table, buffer)
        buffer.seek(0)

        # Upload S3
        aws_conn = BaseHook.get_connection("aws_s3")
        s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_conn.login,
            aws_secret_access_key=aws_conn.password,
            region_name=json.loads(aws_conn.extra)["region_name"]
        )

        key = f"bronze/aluguel_medio_teste/data_carga={data_carga_str}/aluguel.parquet"
        s3_path = f"s3://{BUCKET}/{key}"
        s3.upload_fileobj(buffer, BUCKET, key)
        print(f"✅ Upload realizado: {s3_path}")

        return s3_path

    atualizar_catalogo = AthenaOperator(
        task_id="executar_msck_repair",
        query="MSCK REPAIR TABLE bronze.aluguel_medio_teste",
        database="bronze",
        output_location=f"s3://{BUCKET}/athena-results/",
        workgroup="bronze_workgroup",
        aws_conn_id="aws_s3"
    )

    caminho = extrair_e_enviar_s3.override(task_id="extrair_e_enviar_s3")(fonte="kaggle")
    atualizar_catalogo.set_upstream(caminho)

dag = ingest_aluguel_unificada()
