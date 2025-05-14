# Projeto: Ranking de Municípios Brasileiros

Criando infra AWS: executar o comando `init` dentro do diretório `infra_terraform`
```bash
terraform init               # Inicializa o projeto Terraform
terraform plan
terraform apply
```

## 🔌 Conexões do Airflow

Essas são as conexões configuradas manualmente via interface Web do Airflow:

### 1. PostgreSQL (AWS RDS)
- **Conn ID**: `postgres_rds`
- **Conn Type**: `Postgres`
- **Host**: `ranking-municipios-db.chy482imol7a.us-east-2.rds.amazonaws.com`
- **Database**: `db-datamaster`
- **Login**: `postgres`
- **Password**: `********`
- **Port**: `5432`

### 2. S3 (AWS)
- **Conn ID**: `aws_s3`
- **Conn Type**: `Amazon Web Services`
- **AWS Access Key ID**: `AWS_ACCESS_KEY_ID`
- **AWS Secret Access Key**: `********`
- **Extra**:
```json
{ "region_name": "us-east-2" }
```

### 3. PostgreSQL Local
- **Conn ID**: `postgres`
- **Conn Type**: `Postgres`
- **Host**: `postgres`
- **Database**: *(opcional)*
- **Login**: `postgres`
- **Password**: `********`
- **Port**: `5432`

### 4. MinIO (alternativa ao S3)
- **Conn ID**: `minio`
- **Conn Type**: `Amazon Web Services`
- **AWS Access Key ID**: `minio`
- **AWS Secret Access Key**: `********`
- **Extra**:
```json
{ "endpoint_url": "http://minio:9000" }
```

### 5. ibge_api
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

### 6. diese_api
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

login: REMOVIDO
password	: REMOVIDO

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
