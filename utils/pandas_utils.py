import pandas as pd
import unicodedata

def normalize_str(s):
    """Remove acentos e converte para minúsculas."""
    if pd.isnull(s):
        return s
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

def criar_df_mapeamento_estado_pandas():
    """Retorna DataFrame com o mapeamento dos estados brasileiros."""
    return pd.DataFrame({
        "city_codigo": [110, 120, 130, 140, 150, 160, 170, 210, 230, 240, 250, 260, 270, 330, 410, 420, 500, 510, 520, 530],
        "city_nome": ["Rondônia", "Acre", "Amazonas", "Roraima", "Pará", "Amapá", "Tocantins", "Maranhão", 
                      "Ceará", "Rio Grande do Norte", "Paraíba", "Pernambuco", "Alagoas", "Rio de Janeiro", 
                      "Paraná", "Santa Catarina", "Mato Grosso do Sul", "Mato Grosso", "Goiás", "Distrito Federal"]
    })
