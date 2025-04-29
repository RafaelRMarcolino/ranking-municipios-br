import pandas as pd
import os
import requests
import json

def baixar_arquivo_ibge(url):
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Erro ao baixar arquivo do IBGE: Status {response.status_code}")
    
    temp_file = '/tmp/temp_ibge.xls'
    with open(temp_file, 'wb') as f:
        f.write(response.content)
    
    df = pd.read_excel(temp_file, skiprows=1)

    # Caminho para salvar localmente
    # local_dir = "/usr/local/airflow/data/bronze/ibge/populacao/ano=2021/"
    local_dir = "include/data/bronze/ibge/populacao/ano=2021/"

    os.makedirs(local_dir, exist_ok=True)

    local_path = os.path.join(local_dir, 'populacao.csv')
    df.to_csv(local_path, index=False)

    dados = df.head(10).to_dict(orient='records')

    return json.dumps(dados)
