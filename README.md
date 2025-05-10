
# Projeto: Ranking de Municípios Brasileiros

## 🔌 Conexões do Airflow

Essas são as conexões configuradas manualmente via interface Web do Airflow:

### 1. PostgreSQL (AWS RDS)
- **Conn ID**: `postgres_rds`
- **Conn Type**: `Postgres`
- **Host**: `db-datamaster.chy482imol7a.us-east-2.rds.amazonaws.com`
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

---

## 🧪 Comandos Úteis

### ▶️ Execução de DAGs no Airflow:
```bash
astro dev run dags test insert_populacao_rds 2025-05-04
astro dev run dags test ingest_diese 2025-01-01
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
psql -h db-datamaster.chy482imol7a.us-east-2.rds.amazonaws.com -U postgres -d postgres
```

### 🐳 Docker - Limpeza total:
```bash
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
```