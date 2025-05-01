import pandas as pd
import os
import requests
import json
import boto3
from io import StringIO
from airflow.hooks.base import BaseHook

def baixar_arquivo_ibge(url):
    import pandas as pd
    import requests
    import json
    import boto3
    from io import StringIO
    from airflow.hooks.base import BaseHook

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
        region_name=json.loads(conn.extra)['region_name']  # isso sim pode ficar
    )


    s3.put_object(
        Bucket="ranking-municipios-br",
        Key="bronze/ibge/populacao/ano=2021/populacao.csv",
        Body=csv_buffer.getvalue()
    )

    return json.dumps(df.head(5).to_dict(orient='records'))
