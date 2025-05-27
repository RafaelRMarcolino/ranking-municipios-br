import pandas as pd
import random
import unicodedata
from io import BytesIO
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.hooks.base import BaseHook
import boto3

BUCKET = "ranking-municipios-br"

def normalize_str(s):
    """Remove acentos e converte para minúsculas."""
    if pd.isnull(s):
        return s
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

def criar_df_mapeamento_estado_pandas():
    return pd.DataFrame({
        "city_codigo": [110, 120, 130, 140, 150, 160, 170, 210, 230, 240, 250, 260, 270, 330, 410, 420, 500, 510, 520, 530],
        "city_nome": ["Rondônia", "Acre", "Amazonas", "Roraima", "Pará", "Amapá", "Tocantins", "Maranhão", 
                      "Ceará", "Rio Grande do Norte", "Paraíba", "Pernambuco", "Alagoas", "Rio de Janeiro", 
                      "Paraná", "Santa Catarina", "Mato Grosso do Sul", "Mato Grosso", "Goiás", "Distrito Federal"]
    })

def ler_parquet_s3(s3_hook, s3_path):
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

def salvar_parquet_s3(s3_hook, df, s3_path):
    print(f"✅ Preparando para salvar {len(df)} registros em {s3_path}")
    bucket = s3_path.split('/')[2]
    prefix = '/'.join(s3_path.split('/')[3:])
    # ✅ Corrigido: salva o arquivo diretamente na partição
    key = f"{prefix}aluguel_populacao.parquet"
    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3_hook.load_bytes(buffer.getvalue(), key, bucket_name=bucket, replace=True)
    print(f"✅ Salvo com sucesso em {s3_path}aluguel_populacao.parquet")

def adicionar_particao_glue(database, table, data_carga, s3_location, region='us-east-2'):
    """Adiciona automaticamente partição no Glue após salvar Parquet."""
    aws_conn = BaseHook.get_connection('aws_s3')
    aws_access_key_id = aws_conn.login
    aws_secret_access_key = aws_conn.password

    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
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
                    'Columns': [
                        {'Name': 'area', 'Type': 'int'},
                        {'Name': 'rooms', 'Type': 'int'},
                        {'Name': 'bathroom', 'Type': 'int'},
                        {'Name': 'parking_spaces', 'Type': 'int'},
                        {'Name': 'floor', 'Type': 'int'},
                        {'Name': 'animal', 'Type': 'int'},
                        {'Name': 'furniture', 'Type': 'int'},
                        {'Name': 'rent_amount', 'Type': 'int'},
                        {'Name': 'total', 'Type': 'int'},
                        {'Name': 'city_codigo', 'Type': 'int'},
                        {'Name': 'city', 'Type': 'string'},
                        {'Name': 'aluguel_m2', 'Type': 'double'},
                        {'Name': 'populacao', 'Type': 'int'},
                        {'Name': 'aluguel_per_capita', 'Type': 'double'}
                    ],
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
                'Parameters': {
                    'classification': 'parquet'
                }
            }
        ]
    )
    print(f"✅ Partição adicionada: {response}")

def transformar_dados_silver(data_carga: str):
    print(f"✅ Início do script Silver Aluguel População - Pandas para data_carga={data_carga}")
    s3_hook = S3Hook(aws_conn_id='aws_s3')

    path_aluguel = f"s3://{BUCKET}/bronze/aluguel_medio/data_carga={data_carga}/"
    path_pop_mun = f"s3://{BUCKET}/bronze/ibge/populacao_estimada/municipios/data_carga={data_carga}/"

    df_aluguel = ler_parquet_s3(s3_hook, path_aluguel)
    print(f"✅ df_aluguel carregado com {len(df_aluguel)} registros")

    df_pop_mun = ler_parquet_s3(s3_hook, path_pop_mun)
    print(f"✅ df_pop_mun carregado com {len(df_pop_mun)} registros")

    # Transformações numéricas
    print("✅ Transformando colunas numéricas...")
    df_aluguel["area"] = pd.to_numeric(df_aluguel["area"], errors="coerce")
    df_aluguel["rent_amount"] = pd.to_numeric(df_aluguel["rent_amount"], errors="coerce")
    df_aluguel["total"] = pd.to_numeric(df_aluguel["total"], errors="coerce")

    df_aluguel = df_aluguel.drop(columns=["id", "hoa", "property_tax", "fire_insurance", "city"], errors="ignore")
    df_aluguel = df_aluguel.dropna(subset=["area", "total"])

    # Mapeamento de estados
    df_mapeamento = criar_df_mapeamento_estado_pandas()
    codigos_estado = df_mapeamento["city_codigo"].tolist()

    num_registros = len(df_aluguel)
    df_aluguel["city_codigo"] = [random.choice(codigos_estado) for _ in range(num_registros)]

    df_aluguel = df_aluguel.merge(df_mapeamento, on="city_codigo", how="left")
    df_aluguel = df_aluguel.rename(columns={"city_nome": "city"})

    df_aluguel["aluguel_m2"] = round(df_aluguel["total"] / df_aluguel["area"], 2)

    print(f"✅ DataFrame aluguel após transformações: {len(df_aluguel)} registros")

    # Normalização das cidades
    df_pop_mun = df_pop_mun.rename(columns={"municipio": "city"})
    df_pop_mun["city"] = df_pop_mun["city"].apply(normalize_str)
    df_aluguel["city"] = df_aluguel["city"].apply(normalize_str)

    print(f"✅ Exemplos cidades df_aluguel: {df_aluguel['city'].unique()[:5]}")
    print(f"✅ Exemplos cidades df_pop_mun: {df_pop_mun['city'].unique()[:5]}")

    # Join final
    print("✅ Realizando join final...")
    df_final = df_aluguel.merge(
        df_pop_mun[['city', 'populacao']],
        on='city',
        how='inner'
    )

    print(f"✅ DataFrame final após merge: {len(df_final)} registros")

    if df_final.empty:
        print("⚠️ DataFrame final está vazio. Abortando salvamento.")
        return

    df_final["aluguel_per_capita"] = round(df_final["total"] / df_final["populacao"], 6)

    # ✅ Usa data_carga recebido como parâmetro
    df_final["data_carga"] = data_carga
    print(f"✅ Coluna data_carga adicionada: {df_final['data_carga'].unique()}")

    output_s3_path = f"s3://{BUCKET}/silver/aluguel_populacao/data_carga={data_carga}/"
    salvar_parquet_s3(s3_hook, df_final, output_s3_path)

    # ✅ Adiciona partição automaticamente no Glue
    adicionar_particao_glue(
        database="silver",
        table="aluguel_populacao",
        data_carga=data_carga,
        s3_location=output_s3_path
    )