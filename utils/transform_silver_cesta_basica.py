import pandas as pd
import unicodedata
from datetime import datetime
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
        "city_nome": ["rondônia", "acre", "amazonas", "roraima", "pará", "amapá", "tocantins", "maranhão", 
                      "ceará", "rio grande do norte", "paraíba", "pernambuco", "alagoas", "rio de janeiro", 
                      "paraná", "santa catarina", "mato grosso do sul", "mato grosso", "goiás", "distrito federal"]
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

def transform_silver_cesta_basica(data_carga: str):
    print(f"✅ Início do script Silver Cesta Básica - Pandas para data_carga={data_carga}")
    s3_hook = S3Hook(aws_conn_id='aws_s3')

    path_cesta = f"s3://{BUCKET}/bronze/dieese/cesta_basica/data_carga={data_carga}/"
    path_pop_mun = f"s3://{BUCKET}/bronze/ibge/populacao_estimada/municipios/data_carga={data_carga}/"

    df_cesta = ler_parquet_s3(s3_hook, path_cesta)
    df_municipios = ler_parquet_s3(s3_hook, path_pop_mun)

    print(f"✅ df_cesta carregado com {len(df_cesta)} registros")
    print(f"✅ df_municipios carregado com {len(df_municipios)} registros")

    cidades = [
        "brasília", "campo_grande", "cuiabá", "goiânia", "belo_horizonte", "rio_de_janeiro",
        "são_paulo", "vitória", "curitiba", "florianópolis", "porto_alegre", "belém", "boa_vista",
        "macapá", "manaus", "palmas", "porto_velho", "rio_branco", "aracaju", "fortaleza",
        "joão_pessoa", "maceió", "natal", "recife", "salvador", "são_luís", "teresina", "macaé"
    ]

    # ✅ Unpivot (melt)
    df_unpivot = df_cesta.melt(id_vars=['data_mes'], value_vars=cidades, var_name='cidade', value_name='valor')
    df_unpivot['cidade_norm'] = df_unpivot['cidade'].apply(lambda x: normalize_str(x).replace('_', ' '))

    df_municipios['municipio_norm'] = df_municipios['municipio'].apply(normalize_str)

    # ✅ Merge com municipios
    df_join = pd.merge(
        df_unpivot,
        df_municipios,
        left_on='cidade_norm',
        right_on='municipio_norm',
        how='left'
    )

    # ✅ Adiciona data_carga
    df_join['data_carga'] = data_carga

    # ✅ Preenchendo 'uf' baseado no 'cidade' se for nulo
    def preencher_uf(row):
        if pd.notnull(row['uf']):
            return row['uf']
        mapa = {
            "brasília": "DF", "campo_grande": "MS", "cuiabá": "MT", "goiânia": "GO", 
            "belo_horizonte": "MG", "rio_de_janeiro": "RJ", "são_paulo": "SP", "vitória": "ES", 
            "curitiba": "PR", "florianópolis": "SC", "porto_alegre": "RS", "belém": "PA", 
            "boa_vista": "RR", "macapá": "AP", "manaus": "AM", "palmas": "TO", 
            "porto_velho": "RO", "rio_branco": "AC", "aracaju": "SE", "fortaleza": "CE", 
            "joão_pessoa": "PB", "maceió": "AL", "natal": "RN", "recife": "PE", 
            "salvador": "BA", "são_luís": "MA", "teresina": "PI"
        }
        return mapa.get(row['cidade'], None)

    df_join['uf'] = df_join.apply(preencher_uf, axis=1)

    # ✅ Mapeamento de UF para city_code e city_name
    mapeamento = criar_df_mapeamento_estado_pandas()
    uf_para_codigo = {
        "RO": 110, "AC": 120, "AM": 130, "RR": 140, "PA": 150, "AP": 160, "TO": 170, 
        "MA": 210, "CE": 230, "RN": 240, "PB": 250, "PE": 260, "AL": 270, "RJ": 330, 
        "PR": 410, "SC": 420, "MS": 500, "MT": 510, "GO": 520, "DF": 530
    }
    uf_para_nome = {row['city_codigo']: row['city_nome'] for _, row in mapeamento.iterrows()}

    df_join['city_code'] = df_join['uf'].map(uf_para_codigo)
    df_join['city_name'] = df_join['city_code'].map(uf_para_nome)

    # ✅ Conversão de city_code para float (double no Glue)
    df_join['city_code'] = df_join['city_code'].astype(float)

    # ✅ Seleção final (exclui data_mes, coloca city_code primeiro)
    df_silver = df_join[['city_code', 'cidade', 'uf', 'valor', 'cod_municipio', 'populacao', 'city_name', 'data_carga']]

    print(f"✅ DataFrame final: {len(df_silver)} registros")

    # ✅ Salvar no S3
    output_s3_path = f"s3://{BUCKET}/silver/cesta_basica_full/data_carga={data_carga}/"
    salvar_parquet_s3(s3_hook, df_silver, output_s3_path)

    # ✅ Adicionar partição no Glue
    adicionar_particao_glue(
        database="silver",
        table="cesta_basica_full",
        data_carga=data_carga,
        s3_location=output_s3_path
    )

def salvar_parquet_s3(s3_hook, df, s3_path):
    print(f"✅ Preparando para salvar {len(df)} registros em {s3_path}")
    bucket = s3_path.split('/')[2]
    prefix = '/'.join(s3_path.split('/')[3:])
    key = f"{prefix}cesta_basica_full.parquet"
    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3_hook.load_bytes(buffer.getvalue(), key, bucket_name=bucket, replace=True)
    print(f"✅ Salvo com sucesso em {s3_path}cesta_basica_full.parquet")

def adicionar_particao_glue(database, table, data_carga, s3_location, region='us-east-2'):
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
                    'Columns': [
                        {'Name': 'city_code', 'Type': 'double'},
                        {'Name': 'cidade', 'Type': 'string'},
                        {'Name': 'uf', 'Type': 'string'},
                        {'Name': 'valor', 'Type': 'double'},
                        {'Name': 'cod_municipio', 'Type': 'bigint'},
                        {'Name': 'populacao', 'Type': 'bigint'},
                        {'Name': 'city_name', 'Type': 'string'}
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
                'Parameters': {'classification': 'parquet'}
            }
        ]
    )
    print(f"✅ Partição adicionada: {response}")
