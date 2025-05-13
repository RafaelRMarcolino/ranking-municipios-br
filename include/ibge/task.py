import pandas as pd
import requests
import json
import boto3
from io import StringIO
import psycopg2
import re
from airflow.hooks.base import BaseHook


def inserir_populacao_postgres(csv_s3_path, conn_id, data_carga):
    # 1. Conectar ao S3 e baixar o arquivo
    conn = BaseHook.get_connection('aws_s3')
    s3 = boto3.client(
        's3',
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=json.loads(conn.extra)['region_name']
    )

    bucket = "ranking-municipios-br"
    key = csv_s3_path.replace(f"s3://{bucket}/", "")
    local_path = "/tmp/populacao.csv"
    s3.download_file(bucket, key, local_path)

    # 2. Carregar e tratar o DataFrame
    df = pd.read_csv(local_path)
    df = df[["BRASIL E UNIDADES DA FEDERAÇÃO", "POPULAÇÃO ESTIMADA"]]
    df.columns = ["unidade_federativa", "populacao"]

    df["populacao"] = df["populacao"].astype(str).apply(lambda x: re.sub(r"[^\d]", "", x))
    df["populacao"] = df["populacao"].replace("", None).astype("Int64")

    # 3. Conectar ao banco PostgreSQL
    pg_conn = BaseHook.get_connection(conn_id)
    conn_pg = psycopg2.connect(
        dbname=pg_conn.schema,
        user=pg_conn.login,
        password=pg_conn.password,
        host=pg_conn.host,
        port=pg_conn.port
    )
    cursor = conn_pg.cursor()

    # 4. Criar a tabela com coluna `data_carga`
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS populacao_estimada (
            unidade_federativa TEXT,
            populacao INTEGER,
            data_carga DATE,
            PRIMARY KEY (unidade_federativa, data_carga)
        );
    """)
    conn_pg.commit()

    # 5. Inserir os dados
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO populacao_estimada (unidade_federativa, populacao, data_carga)
            VALUES (%s, %s, %s)
            ON CONFLICT (unidade_federativa, data_carga) DO UPDATE
            SET populacao = EXCLUDED.populacao;
        """, (row['unidade_federativa'], row['populacao'] if pd.notnull(row['populacao']) else None, data_carga))

    conn_pg.commit()
    cursor.close()
    conn_pg.close()
    print(f"✅ Dados da população inseridos com sucesso para data_carga={data_carga}")
