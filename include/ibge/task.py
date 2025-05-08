import pandas as pd
import requests
import json
import boto3
from io import StringIO
import psycopg2
from airflow.hooks.base import BaseHook
import os
import re


def baixar_arquivo_ibge(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Erro ao baixar arquivo do IBGE: Status {response.status_code}")

    temp_file = '/tmp/temp_ibge.xls'
    with open(temp_file, 'wb') as f:
        f.write(response.content)

    df = pd.read_excel(temp_file, skiprows=1)

    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)

    conn = BaseHook.get_connection('aws_s3')
    s3 = boto3.client(
        's3',
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=json.loads(conn.extra)['region_name']
    )

    s3.put_object(
        Bucket="ranking-municipios-br",
        Key="bronze/ibge/populacao/ano=2021/populacao.csv",
        Body=csv_buffer.getvalue()
    )

    return json.dumps(df.head(5).to_dict(orient='records'))


def inserir_populacao_postgres(csv_s3_path, conn_id):
    import pandas as pd
    import psycopg2
    from airflow.hooks.base import BaseHook
    import json
    import re
    import boto3

    # Baixar do S3 para /tmp
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

    # Ler CSV e preparar os dados
    df = pd.read_csv(local_path)
    df = df[["BRASIL E UNIDADES DA FEDERAÇÃO", "POPULAÇÃO ESTIMADA"]]
    df.columns = ["unidade_federativa", "populacao"]

    # Limpeza da coluna população: remove não-dígitos, trata vazios
    df["populacao"] = df["populacao"].astype(str).apply(lambda x: re.sub(r"[^\d]", "", x))
    df["populacao"] = df["populacao"].replace("", None).astype("Int64")  # tipo nulo-friendly para inteiros

    # Conectar ao banco
    conn_info = BaseHook.get_connection(conn_id)
    conn = psycopg2.connect(
        dbname=conn_info.schema,
        user=conn_info.login,
        password=conn_info.password,
        host=conn_info.host,
        port=conn_info.port
    )
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS populacao_estimada (
            unidade_federativa TEXT PRIMARY KEY,
            populacao INTEGER
        );
    """)
    conn.commit()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO populacao_estimada (unidade_federativa, populacao)
            VALUES (%s, %s)
            ON CONFLICT (unidade_federativa) DO UPDATE
            SET populacao = EXCLUDED.populacao;
        """, (row['unidade_federativa'], row['populacao'] if pd.notnull(row['populacao']) else None))

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Dados inseridos com sucesso!")