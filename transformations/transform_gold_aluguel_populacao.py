from utils.aws_utils import ler_parquet_s3, salvar_parquet_s3, adicionar_particao_glue
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import pandas as pd

BUCKET = "ranking-municipios-br"

def transformar_dados_gold_aluguel_populacao(data_carga: str):
    print(f"✅ [GOLD] Início da transformação - data_carga={data_carga}")
    s3_hook = S3Hook(aws_conn_id='aws_s3')

    path_silver = f"s3://{BUCKET}/silver/aluguel_populacao/data_carga={data_carga}/"
    print(f"✅ [GOLD] Lendo dados de: {path_silver}")

    df_silver = ler_parquet_s3(s3_hook, path_silver)

    # Conversão de tipos
    cols_int = ["rooms", "bathroom", "parking_spaces", "floor", "animal", "furniture"]
    cols_float = ["area", "rent_amount", "total", "aluguel_m2", "populacao", "aluguel_per_capita"]

    print("✅ [GOLD] Convertendo colunas numéricas...")

    for col in cols_int:
        df_silver[col] = pd.to_numeric(df_silver[col], errors='coerce').astype('Int64')

    for col in cols_float:
        df_silver[col] = pd.to_numeric(df_silver[col], errors='coerce').astype(float)

    print("✅ [GOLD] Criando novos indicadores...")

    df_silver["aluguel_m2_calculado"] = df_silver.apply(
        lambda row: row["rent_amount"] / row["area"] if pd.notnull(row["area"]) and row["area"] > 0 else None,
        axis=1
    ).astype(float)

    df_silver["total_cost"] = (df_silver["rent_amount"] + df_silver["total"]).astype(float)

    df_silver["aluguel_per_room"] = df_silver.apply(
        lambda row: row["rent_amount"] / row["rooms"] if pd.notnull(row["rooms"]) and row["rooms"] > 0 else None,
        axis=1
    ).astype(float)

    print("✅ [GOLD] Ajustando tipos...")

    # Seleção para GOLD
    df_gold = df_silver[["city", "aluguel_m2_calculado", "total_cost", "aluguel_per_room"]].copy()
    df_gold["data_carga"] = data_carga

    print("✅ [GOLD] Tipos finais do DataFrame GOLD:")
    print(df_gold.dtypes)

    print(f"✅ [GOLD] DataFrame gerado com {len(df_gold)} registros.")

    if df_gold.empty:
        print("⚠️ [GOLD] DataFrame vazio. Abortando salvamento.")
        return

    output_s3_path = f"s3://{BUCKET}/gold/aluguel_populacao_gold/data_carga={data_carga}/"
    print(f"✅ [GOLD] Salvando Parquet em: {output_s3_path}")

    salvar_parquet_s3(
        s3_hook,
        df_gold,
        output_s3_path,
        filename="aluguel_populacao_gold"
    )

    # Schema conforme Glue Catalog
    columns = [
        {'Name': 'city', 'Type': 'string'},
        {'Name': 'aluguel_m2_calculado', 'Type': 'double'},
        {'Name': 'total_cost', 'Type': 'double'},
        {'Name': 'aluguel_per_room', 'Type': 'double'}
    ]

    print(f"✅ [GOLD] Adicionando partição no Glue para data_carga={data_carga}")

    adicionar_particao_glue(
        database="gold",
        table="aluguel_populacao_gold",
        data_carga=data_carga,
        s3_location=output_s3_path,
        columns=columns
    )

    print("✅ [GOLD] Transformação finalizada com sucesso!")
