import pandas as pd
import psycopg2
from airflow.hooks.base import BaseHook
import json
import boto3
from io import BytesIO
from datetime import datetime

def inserir_cesta_basica_postgres(parquet_s3_path, conn_id):



    # Conexão com S3
    conn = BaseHook.get_connection('aws_s3')
    s3 = boto3.client(
        's3',
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=json.loads(conn.extra)['region_name']
    )

    bucket = "ranking-municipios-br"
    key = parquet_s3_path.replace(f"s3://{bucket}/", "")

    # Baixando Parquet em memória
    buffer = BytesIO()
    s3.download_fileobj(bucket, key, buffer)
    buffer.seek(0)

    # Leitura do Parquet
    df = pd.read_parquet(buffer)
    df = df.rename(columns={"Data": "data_mes"})
    df["data_mes"] = pd.to_datetime(df["data_mes"])

    # Garante que a coluna data_carga exista
    if "data_carga" not in df.columns:
        df["data_carga"] = datetime.utcnow()

    # Transforma para formato long
    df_melted = df.melt(id_vars=["data_mes", "data_carga"], var_name="cidade", value_name="valor")

    # Conexão com PostgreSQL
    pg_conn = BaseHook.get_connection(conn_id)
    conn_pg = psycopg2.connect(
        dbname=pg_conn.schema,
        user=pg_conn.login,
        password=pg_conn.password,
        host=pg_conn.host,
        port=pg_conn.port
    )
    cursor = conn_pg.cursor()

    # Criação da tabela com campo de partição lógico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cesta_basica (
            data_mes TEXT,
            cidade TEXT,
            valor FLOAT,
            data_carga TIMESTAMP,
            PRIMARY KEY (data_mes, cidade)
        );
    """)
    conn_pg.commit()

    for _, row in df_melted.iterrows():
        cursor.execute("""
            INSERT INTO cesta_basica (data_mes, cidade, valor, data_carga)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (data_mes, cidade) DO UPDATE
            SET valor = EXCLUDED.valor,
                data_carga = EXCLUDED.data_carga;
        """, (row["data_mes"], row["cidade"], row["valor"], row["data_carga"]))

    conn_pg.commit()
    cursor.close()
    conn_pg.close()
    print("✅ Dados da cesta básica inseridos com sucesso!")