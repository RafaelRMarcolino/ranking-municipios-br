from utils.aws_utils import ler_parquet_s3, salvar_parquet_s3, adicionar_particao_glue
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import pandas as pd

BUCKET = "ranking-municipios-br"

def transformar_dados_gold_cesta_basica(data_carga: str):
    print(f"✅ [GOLD] Início da transformação - data_carga={data_carga}")
    s3_hook = S3Hook(aws_conn_id='aws_s3')

    path_silver = f"s3://{BUCKET}/silver/cesta_basica_full/data_carga={data_carga}/"
    print(f"✅ [GOLD] Lendo dados de: {path_silver}")

    df_silver = ler_parquet_s3(s3_hook, path_silver)

    # Conversão de tipos
    df_silver['city_code'] = pd.to_numeric(df_silver['city_code'], errors='coerce').astype('Int64')
    df_silver['valor_cesta'] = pd.to_numeric(df_silver['valor_cesta'], errors='coerce').astype(float)
    df_silver['cod_municipio'] = pd.to_numeric(df_silver['cod_municipio'], errors='coerce').astype('Int64')
    df_silver['populacao'] = pd.to_numeric(df_silver['populacao'], errors='coerce').astype('Int64')

    print("✅ [GOLD] Criando indicadores...")

    # Agrupamento e cálculo
    df_gold = df_silver.groupby(["city_code", "cidade_cesta", "estado", "data_carga"]).agg(
        valor_cesta_medio=('valor_cesta', lambda x: round(x.mean(), 2)),
        populacao=('populacao', 'sum')
    ).reset_index()

    df_gold['valor_total_gasto'] = (df_gold['valor_cesta_medio'] * df_gold['populacao']).round(2)

    print("✅ [GOLD] Tipos finais do DataFrame GOLD:")
    print(df_gold.dtypes)

    print(f"✅ [GOLD] DataFrame gerado com {len(df_gold)} registros.")

    if df_gold.empty:
        print("⚠️ [GOLD] DataFrame vazio. Abortando salvamento.")
        return

    output_s3_path = f"s3://{BUCKET}/gold/cesta_basica_gold/data_carga={data_carga}/"
    print(f"✅ [GOLD] Salvando Parquet em: {output_s3_path}")

    salvar_parquet_s3(
        s3_hook,
        df_gold,
        output_s3_path,
        filename="cesta_basica_gold"
    )

    # Schema conforme Glue Catalog
    columns = [
        {'Name': 'city_code', 'Type': 'int'},
        {'Name': 'cidade_cesta', 'Type': 'string'},
        {'Name': 'estado', 'Type': 'string'},
        {'Name': 'valor_cesta_medio', 'Type': 'double'},
        {'Name': 'populacao', 'Type': 'bigint'},
        {'Name': 'valor_total_gasto', 'Type': 'double'}
    ]

    print(f"✅ [GOLD] Adicionando partição no Glue para data_carga={data_carga}")

    adicionar_particao_glue(
        database="gold",
        table="cesta_basica_gold",
        data_carga=data_carga,
        s3_location=output_s3_path,
        columns=columns
    )

    print("✅ [GOLD] Transformação finalizada com sucesso!")
