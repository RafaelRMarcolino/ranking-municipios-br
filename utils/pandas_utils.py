import pandas as pd

def criar_df_mapeamento_estado_pandas():
    """
    Cria o DataFrame de mapeamento de códigos de estado para nomes.
    Ajustado para usar 'city' como nome de coluna.
    """
    codigo_para_estado = {
        110: "Rondônia", 120: "Acre", 130: "Amazonas", 140: "Roraima", 150: "Pará",
        160: "Amapá", 170: "Tocantins", 210: "Maranhão", 230: "Ceará", 240: "Rio Grande do Norte",
        250: "Paraíba", 260: "Pernambuco", 270: "Alagoas", 280: "Sergipe", 290: "Bahia",
        310: "Minas Gerais", 320: "Espírito Santo", 330: "Rio de Janeiro", 350: "São Paulo",
        410: "Paraná", 420: "Santa Catarina", 430: "Rio Grande do Sul", 500: "Mato Grosso do Sul",
        510: "Mato Grosso", 520: "Goiás", 530: "Distrito Federal"
    }
    df_mapeamento = pd.DataFrame(
        [(k, v) for k, v in codigo_para_estado.items()],
        columns=["city_codigo", "city"]
    )
    return df_mapeamento

def limpar_df_municipios_pandas(df_pop_mun):
    """
    Limpa e ajusta DataFrame de população para padronizar e remover ruídos.
    Tenta detectar a coluna correta para 'city'.
    """
    print(f"🔍 Colunas do df_pop_mun: {df_pop_mun.columns.tolist()}")

    if 'unidade_federativa' in df_pop_mun.columns:
        df = df_pop_mun.rename(columns={'unidade_federativa': 'city'})
    elif 'municipio' in df_pop_mun.columns:
        df = df_pop_mun.rename(columns={'municipio': 'city'})
    elif 'nome_municipio' in df_pop_mun.columns:
        df = df_pop_mun.rename(columns={'nome_municipio': 'city'})
    elif 'city' in df_pop_mun.columns:
        df = df_pop_mun.copy()
    else:
        raise ValueError("❌ Não foi encontrada coluna adequada para renomear para 'city'!")

    df['city'] = df['city'].astype(str).str.strip()

    df = df[
        df['city'].notnull() &
        (df['city'] != '') &
        (~df['city'].str.contains(r'Fonte:|Norte|Sul|Sudeste|Centro|Nordeste', regex=True))
    ]
    
    print(f"✅ Limpeza concluída. {len(df)} registros após limpeza.")
    
    return df
