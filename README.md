# Projeto: Ranking de Municípios Brasileiros

Criando infra AWS: executar o comando `init` dentro do diretório `infra_terraform`
```bash
terraform init               # Inicializa o projeto Terraform
terraform plan
terraform apply
```

## 🔌 Conexões do Airflow

Essas são as conexões configuradas manualmente via interface Web do Airflow:

### 1. S3 (AWS)
- **Conn ID**: `aws_s3`
- **Conn Type**: `Amazon Web Services`
- **AWS Access Key ID**: `AWS_ACCESS_KEY_ID`
- **AWS Secret Access Key**: `********`
- **Extra**:
```json
{ "region_name": "us-east-2" }
```


### 2. ibge_api
Para executar a DAG `ibge_populacao`, crie uma conexão HTTP no Airflow com os seguintes parâmetros:

- **Connection Id**: `ibge_api`
- **Connection Type**: `HTTP`
- **Host**: `https://ftp.ibge.gov.br`
- **Login**: `admin` *(opcional)*
- **Password**: `*****` *(opcional)*
- **Extra**:
```json
{
  "endpoint": "/Estimativas_de_Populacao/Estimativas_2024/POP2024_20241230.xls",
  "headers": {}
}
```
💡 Essa conexão será usada pelo sensor da DAG `ibge_populacao` para verificar a disponibilidade da URL antes de iniciar o download do arquivo `.xls`.

### 3. diese_api
Para executar a DAG `ingest_diese`, que automatiza o scraping de todas as cidades da cesta básica no site do DIEESE, crie uma conexão HTTP com:

- **Connection Id**: `diese_api`
- **Connection Type**: `HTTP`
- **Host**: `https://www.dieese.org.br`
- **Login**: *(em branco)*
- **Password**: *(em branco)*
- **Extra**: *(em branco)*

Essa conexão será usada pelo Selenium para simular o preenchimento e exportação da planilha de cada cidade.

---

https://www.kaggle.com/code/unanimad/brazilian-houses-to-rent/notebook

Connection Id *	 kaggle_default
Connection Type *	generic

login: datamasterrafael
password	: 80243e1ba78e7efb5c5f678cad1be8b5

extra: 
{
  "file_path": "/home/astro/.kaggle/kaggle.json"
}




## 🧲 Comandos Úteis

### ▶️ Execução de DAGs no Airflow:
```bash
astro dev run dags test insert_populacao_rds 2025-05-04
astro dev run dags test ingest_diese 2025-01-01
astro dev run dags test ibge_populacao 2025-05-09
```

### ☁️ Terraform (infraestrutura AWS):
```bash
terraform init             # Inicializa o projeto Terraform
terraform plan             # Visualiza mudanças
terraform apply            # Cria os recursos na AWS
terraform destroy          # Destroi todos os recursos criados
```

### 🐘 Conexão manual com PostgreSQL RDS:
```bash
psql -h ranking-municipios-db.chy482imol7a.us-east-2.rds.amazonaws.com -U postgres -d postgres
```

### 💣 Docker - Limpeza total:
```bash
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
```
https://www.dieese.org.br/cesta/


MSCK REPAIR TABLE bronze.cesta_basica;
MSCK REPAIR TABLE bronze.aluguel_medio;
MSCK REPAIR TABLE bronze.populacao_estimada;

excluir query salvas

aws athena delete-work-group \
  --work-group bronze_workgroup \
  --recursive-delete-option



aws athena delete-work-group \
  --work-group silver_workgroup \
  --recursive-delete-option


Verificar se as chaves estão inclusas no docker
astro dev bash scheduler
# ou
astro dev bash webserver


export $(cat .env | xargs)





# 1. Para e remove todos containers do projeto
docker-compose down -v

# 2. Lista containers que ainda estão ocupando portas importantes
docker ps -a | grep -E '3000|2376|8080|8085|7077|8081|8082'

# 3. Remove manualmente os containers zumbis que aparecerem
docker rm -f $(docker ps -aq)

# 4. Remove redes docker travadas
docker network prune -f

# 5. Remove volumes órfãos
docker volume prune -f

# 6. Confirma que não tem mais containers ocupando as portas
docker ps -a

# 7. Reinicia o projeto
astro dev restart


---------------------------------------------
iniciar terraform
terraform init