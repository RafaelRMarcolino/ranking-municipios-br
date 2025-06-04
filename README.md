# 🏛️ Projeto: Ranking de Municípios Brasileiros

Este projeto realiza a coleta, transformação e análise de dados públicos (IBGE, DIEESE, Kaggle, etc.) para gerar indicadores socioeconômicos por município. Utiliza Apache Airflow com Astro CLI para orquestração, AWS (S3, Athena, Glue) para armazenamento e análise, e Docker para execução local.

---

## 🧭 Sumário

1. [Primeiro Acesso à AWS](#primeiro-acesso-à-aws)
2. [Pré-Requisitos](#pré-requisitos)
3. [Clonar o Projeto](#clonar-o-projeto)
4. [Executar com Astro CLI](#executar-com-astro-cli)
5. [Provisionar Infraestrutura com Terraform](#provisionar-infraestrutura-com-terraform)
6. [Conexões no Airflow](#conexões-no-airflow)
7. [Encerrando e Limpando Recursos](#encerrando-e-limpando-recursos)

---

## 📄 Documentação: Primeiro Acesso à AWS

### 👤 Acesso via Console Web

Acesse o console da AWS: 👉 [https://772056227406.signin.aws.amazon.com/console](https://772056227406.signin.aws.amazon.com/console)

Credenciais:

```
IAM Username: user-data-master
Senha: 1kuwS57_
```

### 💻 Acesso via Terminal (AWS CLI)

Pré-requisitos:

* AWS CLI instalado ([https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html))

Configure com:

```bash
aws configure
```

Insira:

```
AWS Access Key ID [None]: Axxxxxx
AWS Secret Access Key [None]: rxxxxxxxx
Default region name [None]: us-east-2
Default output format [None]: json
```

Teste de acesso ao S3:

```bash
aws s3 ls
```

Se estiver certo, listará o bucket `ranking-municipios-br`

---

## 📦 Pré-requisitos

| Ferramenta              | Descrição                     | Comando/Teste        |
| ----------------------- | ----------------------------- | -------------------- |
| Docker e Docker Compose | Para orquestrar os containers | `docker --version`   |
| Terraform               | Provisionar infraestrutura    | `terraform -version` |
| Python 3.8+             | Utilitários locais            | `python --version`   |
| AWS CLI configurado     | Acesso AWS                    | `aws configure`      |
| VS Code + extensão SSH  | (opcional) ambiente remoto    | —                    |

---

## 📁 Estrutura do Projeto (Resumo)

```
ranking-municipios-br/
├── dags/
├── bronze/ silver/ gold/
├── include/
├── transformations/
├── utils/
├── infra_terraform/
├── .astro/
├── Dockerfile
├── docker-compose.override.yml
├── requirements.txt
├── README.md
```

---

## 🚀 Passo a Passo para Executar o Projeto

### 1. Localmente:

#### Clone o projeto

```bash
git clone https://github.com/seu-usuario/ranking-municipios-br.git
cd ranking-municipios-br
```

#### Instale as dependências

* Astro CLI: [https://docs.astronomer.io/astro/cli/install](https://docs.astronomer.io/astro/cli/install)

```bash
curl -sSL https://install.astronomer.io | sudo bash
```

* Docker: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)

* Terraform: [https://developer.hashicorp.com/terraform/downloads](https://developer.hashicorp.com/terraform/downloads)

```bash
sudo apt update && sudo apt install terraform
```

* Python (Linux):

```bash
sudo apt install python3.10 python3.10-venv python3.10-dev
```

#### Suba o ambiente local

```bash
astro dev start
```

Acesse: [http://localhost:8080](http://localhost:8080)

#### Provisionar com Terraform

```bash
cd infra_terraform
terraform init
terraform apply
```

### 2. Execução por Máquina Virtual

Acesse o console da AWS: 👉 [https://772056227406.signin.aws.amazon.com/console](https://772056227406.signin.aws.amazon.com/console)

Instancie uma EC2 e conecte via:

```bash
ssh -i "key-master.pem" ubuntu@<IPv4>
```

#### Suba o ambiente no servidor remoto

```bash
cd ranking-municipios-br
astro dev start
```

---

## 🔌 Conexões do Airflow

Essas são as conexões configuradas manualmente via interface Web do Airflow:

### 1. S3 (AWS)

* Conn ID: `aws_s3`
* Conn Type: Amazon Web Services
* AWS Access Key ID: `AWS_ACCESS_KEY_ID`
* AWS Secret Access Key: `********`
* Extra: `{ "region_name": "us-east-2" }`

### 2. ibge\_api

* Connection Id: `ibge_api`
* Type: HTTP
* Host: `https://ftp.ibge.gov.br`
* Extra:

```json
{
  "endpoint": "/Estimativas_de_Populacao/Estimativas_2024/POP2024_20241230.xls",
  "headers": {}
}
```

### 3. diese\_api

* Connection Id: `diese_api`
* Type: HTTP
* Host: `https://www.dieese.org.br`

### 4. kaggle\_default

* Connection Id: `kaggle_default`
* Type: generic
* login: `datamasterrafael`
* password: `80243e1ba78e7efb5c5f678cad1be8b5`
* extra:

```json
{ "file_path": "/home/astro/.kaggle/kaggle.json" }
```

---

## 🧹 Encerrando e Limpando Recursos

### 🔄 Parar containers e ambiente local:

```bash
astro dev stop
```

### ❌ Destruir infraestrutura:

```bash
cd infra_terraform
terraform destroy
```

### 🧼 Apagar todos os containers Docker (opcional):

```bash
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
```

### 🗑️ Deletar Workgroups do Athena (caso necessário):

```bash
aws athena delete-work-group --work-group silver_workgroup --recursive-delete-option
aws athena delete-work-group --work-group bronze_workgroup --recursive-delete-option
aws athena delete-work-group --work-group gold_workgroup --recursive-delete-option
```
