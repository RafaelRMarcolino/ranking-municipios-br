import pandas as pd
import random
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from utils.pandas_utils import normalize_str, criar_df_mapeamento_estado_pandas
from utils.aws_utils import ler_parquet_s3, salvar_parquet_s3, adicionar_particao_glue

BUCKET = "ranking-municipios-br"

def transformar_dados_silver(data_carga: str):
    print(f"✅ Início do script Silver Aluguel População - Pandas para data_carga={data_carga}")
    s3_hook = S3Hook(aws_conn_id='aws_s3')

    path_aluguel = f"s3://{BUCKET}/bronze/aluguel_medio/data_carga={data_carga}/"
    path_pop_mun = f"s3://{BUCKET}/bronze/ibge/populacao_estimada/municipios/data_carga={data_carga}/"

    df_aluguel = ler_parquet_s3(s3_hook, path_aluguel)
    df_pop_mun = ler_parquet_s3(s3_hook, path_pop_mun)

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

    df_aluguel["city_codigo"] = [random.choice(codigos_estado) for _ in range(len(df_aluguel))]
    df_aluguel = df_aluguel.merge(df_mapeamento, on="city_codigo", how="left").rename(columns={"city_nome": "city"})

    df_aluguel["aluguel_m2"] = round(df_aluguel["total"] / df_aluguel["area"], 2)

    # Normalização
    df_pop_mun = df_pop_mun.rename(columns={"municipio": "city"})
    df_pop_mun["city"] = df_pop_mun["city"].apply(normalize_str)
    df_aluguel["city"] = df_aluguel["city"].apply(normalize_str)

    # Join final
    print("✅ Realizando join final...")
    df_final = df_aluguel.merge(df_pop_mun[['city', 'populacao']], on='city', how='inner')

    if df_final.empty:
        print("⚠️ DataFrame final está vazio. Abortando salvamento.")
        return

    df_final["aluguel_per_capita"] = round(df_final["total"] / df_final["populacao"], 6)
    df_final["data_carga"] = data_carga

    output_s3_path = f"s3://{BUCKET}/silver/aluguel_populacao/data_carga={data_carga}/"
    salvar_parquet_s3(s3_hook, df_final, output_s3_path, filename="aluguel_populacao")

    # Definindo colunas para Glue
    columns = [
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
    ]

    adicionar_particao_glue(
        database="silver",
        table="aluguel_populacao",
        data_carga=data_carga,
        s3_location=output_s3_path,
        columns=columns
    )
