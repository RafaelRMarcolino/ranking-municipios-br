import pandas as pd
import os
import requests
import json
import boto3
from io import StringIO
from airflow.hooks.base import BaseHook

def baixar_arquivo_ibge(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Erro ao baixar arquivo do IBGE: Status {response.status_code}")

    temp_file = '/tmp/temp_ibge.xls'
    with open(temp_file, 'wb') as f:
        f.write(response.content)

    df = pd.read_excel(temp_file, skiprows=1)

    # Converte DataFrame para CSV em memória
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)

    # Recupera conexão do Airflow
    conn = BaseHook.get_connection('minio')
    s3 = boto3.client(
        's3',
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        endpoint_url=json.loads(conn.extra)['endpoint_url']
    )

    # Nome do bucket e chave do arquivo
    bucket = "datalake"
    key = "bronze/ibge/populacao/ano=2021/populacao.csv"


    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=csv_buffer.getvalue()
    )
    print("******************************************************************")
    print("******************************************************************")
    print("******************************************************************")
    print(f"Arquivo salvo em s3://{bucket}/{key}")


    # Loga amostra
    return json.dumps(df.head(5).to_dict(orient='records'))
