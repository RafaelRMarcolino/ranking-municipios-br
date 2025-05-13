import pandas as pd
import psycopg2
import boto3
import json
from airflow.hooks.base import BaseHook
from io import BytesIO

def inserir_aluguel_postgres_parquet(s3_path, conn_id="postgres_rds", data_carga=None):
    # Conexão S3
    aws_conn = BaseHook.get_connection("aws_s3")
    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_conn.login,
        aws_secret_access_key=aws_conn.password,
        region_name=json.loads(aws_conn.extra)["region_name"]
    )

    bucket = "ranking-municipios-br"
    key = s3_path.replace(f"s3://{bucket}/", "")
    buffer = BytesIO()
    s3.download_fileobj(bucket, key, buffer)
    buffer.seek(0)

    df = pd.read_parquet(buffer)
    df["data_carga"] = data_carga

    # Inferir colunas para criar a tabela
    colunas_pg = []
    for col in df.columns:
        tipo = "TEXT"
        if pd.api.types.is_float_dtype(df[col]):
            tipo = "FLOAT"
        elif pd.api.types.is_integer_dtype(df[col]):
            tipo = "INTEGER"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            tipo = "TIMESTAMP"
        elif col == "data_carga":
            tipo = "DATE"
        colunas_pg.append(f"{col} {tipo}")

    colunas_pg_str = ",\n    ".join(colunas_pg)
    pk = "PRIMARY KEY (city, data_carga)" if "city" in df.columns else ""

    # Conexão PostgreSQL
    pg_conn = BaseHook.get_connection(conn_id)
    conn_pg = psycopg2.connect(
        dbname=pg_conn.schema,
        user=pg_conn.login,
        password=pg_conn.password,
        host=pg_conn.host,
        port=pg_conn.port
    )
    cursor = conn_pg.cursor()

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS aluguel_medio (
            {colunas_pg_str},
            {pk}
        );
    """)
    conn_pg.commit()

    # Inserção dinâmica
    colunas = df.columns.tolist()
    placeholders = ", ".join(["%s"] * len(colunas))
    colunas_sql = ", ".join(colunas)

    update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in colunas if col != "city" and col != "data_carga"])

    for _, row in df.iterrows():
        cursor.execute(f"""
            INSERT INTO aluguel_medio ({colunas_sql})
            VALUES ({placeholders})
            ON CONFLICT (city, data_carga) DO UPDATE
            SET {update_clause};
        """, tuple(row[col] for col in colunas))

    conn_pg.commit()
    cursor.close()
    conn_pg.close()
    print("✅ Inserção concluída com todas as colunas.")
