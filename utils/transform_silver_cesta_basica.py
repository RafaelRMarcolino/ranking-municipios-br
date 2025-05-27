import pandas as pd
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from utils.pandas_utils import normalize_str, criar_df_mapeamento_estado_pandas
from utils.aws_utils import ler_parquet_s3, salvar_parquet_s3, adicionar_particao_glue

BUCKET = "ranking-municipios-br"

def transform_silver_cesta_basica(data_carga: str):
    print(f"✅ Início do script Silver Cesta Básica - Pandas para data_carga={data_carga}")
    s3_hook = S3Hook(aws_conn_id='aws_s3')

    path_cesta = f"s3://{BUCKET}/bronze/dieese/cesta_basica/data_carga={data_carga}/"
    path_pop_mun = f"s3://{BUCKET}/bronze/ibge/populacao_estimada/municipios/data_carga={data_carga}/"

    df_cesta = ler_parquet_s3(s3_hook, path_cesta)
    df_municipios = ler_parquet_s3(s3_hook, path_pop_mun)

    cidades = [
        "brasília", "campo_grande", "cuiabá", "goiânia", "belo_horizonte", "rio_de_janeiro",
        "são_paulo", "vitória", "curitiba", "florianópolis", "porto_alegre", "belém", "boa_vista",
        "macapá", "manaus", "palmas", "porto_velho", "rio_branco", "aracaju", "fortaleza",
        "joão_pessoa", "maceió", "natal", "recife", "salvador", "são_luís", "teresina", "macaé"
    ]

    # Unpivot (melt)
    df_unpivot = df_cesta.melt(id_vars=['data_mes'], value_vars=cidades, var_name='cidade', value_name='valor')
    df_unpivot['cidade_norm'] = df_unpivot['cidade'].apply(lambda x: normalize_str(x).replace('_', ' '))

    df_municipios['municipio_norm'] = df_municipios['municipio'].apply(normalize_str)

    # Merge com municipios
    df_join = pd.merge(
        df_unpivot,
        df_municipios,
        left_on='cidade_norm',
        right_on='municipio_norm',
        how='left'
    )

    df_join['data_carga'] = data_carga

    # Preenchendo 'uf'
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

    # Mapeamento UF -> city_code e city_name
    mapeamento = criar_df_mapeamento_estado_pandas()
    uf_para_codigo = {
        "RO": 110, "AC": 120, "AM": 130, "RR": 140, "PA": 150, "AP": 160, "TO": 170, 
        "MA": 210, "CE": 230, "RN": 240, "PB": 250, "PE": 260, "AL": 270, "RJ": 330, 
        "PR": 410, "SC": 420, "MS": 500, "MT": 510, "GO": 520, "DF": 530
    }
    uf_para_nome = {row['city_codigo']: row['city_nome'] for _, row in mapeamento.iterrows()}

    df_join['city_code'] = df_join['uf'].map(uf_para_codigo).astype(float)
    df_join['city_name'] = df_join['city_code'].map(uf_para_nome)

    df_silver = df_join[['city_code', 'cidade', 'uf', 'valor', 'cod_municipio', 'populacao', 'city_name', 'data_carga']]

    print(f"✅ DataFrame final: {len(df_silver)} registros")

    output_s3_path = f"s3://{BUCKET}/silver/cesta_basica_full/data_carga={data_carga}/"
    salvar_parquet_s3(s3_hook, df_silver, output_s3_path, filename="cesta_basica_full")

    columns = [
        {'Name': 'city_code', 'Type': 'double'},
        {'Name': 'cidade', 'Type': 'string'},
        {'Name': 'uf', 'Type': 'string'},
        {'Name': 'valor', 'Type': 'double'},
        {'Name': 'cod_municipio', 'Type': 'bigint'},
        {'Name': 'populacao', 'Type': 'bigint'},
        {'Name': 'city_name', 'Type': 'string'}
    ]

    adicionar_particao_glue(
        database="silver",
        table="cesta_basica_full",
        data_carga=data_carga,
        s3_location=output_s3_path,
        columns=columns
    )
