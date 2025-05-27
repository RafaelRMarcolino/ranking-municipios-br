import pandas as pd
from io import BytesIO
import boto3
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.hooks.base import BaseHook

def ler_parquet_s3(s3_hook: S3Hook, s3_path: str) -> pd.DataFrame:
    print(f"✅ Lendo: {s3_path}")
    bucket = s3_path.split('/')[2]
    prefix = '/'.join(s3_path.split('/')[3:])
    keys = s3_hook.list_keys(bucket_name=bucket, prefix=prefix)
    parquet_keys = [k for k in keys if k.endswith('.parquet')]

    if not parquet_keys:
        raise FileNotFoundError(f"❌ Nenhum arquivo .parquet encontrado no prefixo: {prefix}")

    key = parquet_keys[0]
    print(f"✅ Arquivo encontrado: {key}")
    obj = s3_hook.get_key(key, bucket_name=bucket)
    return pd.read_parquet(BytesIO(obj.get()['Body'].read()))

def salvar_parquet_s3(s3_hook: S3Hook, df: pd.DataFrame, s3_path: str, filename: str):
    print(f"✅ Preparando para salvar {len(df)} registros em {s3_path}")
    bucket = s3_path.split('/')[2]
    prefix = '/'.join(s3_path.split('/')[3:])
    key = f"{prefix}{filename}.parquet"
    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3_hook.load_bytes(buffer.getvalue(), key, bucket_name=bucket, replace=True)
    print(f"✅ Salvo com sucesso em {s3_path}{filename}.parquet")

def adicionar_particao_glue(database: str, table: str, data_carga: str, s3_location: str, columns: list, region='us-east-2'):
    aws_conn = BaseHook.get_connection('aws_s3')
    session = boto3.Session(
        aws_access_key_id=aws_conn.login,
        aws_secret_access_key=aws_conn.password,
        region_name=region
    )
    client = session.client('glue')

    print(f"✅ Adicionando partição para data_carga={data_carga} na tabela {table}...")

    response = client.batch_create_partition(
        DatabaseName=database,
        TableName=table,
        PartitionInputList=[
            {
                'Values': [data_carga],
                'StorageDescriptor': {
                    'Columns': columns,
                    'Location': s3_location,
                    'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
                    'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
                    'SerdeInfo': {
                        'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
                        'Parameters': {}
                    },
                    'Compressed': False,
                    'StoredAsSubDirectories': False
                },
                'Parameters': {'classification': 'parquet'}
            }
        ]
    )
    print(f"✅ Partição adicionada: {response}")
