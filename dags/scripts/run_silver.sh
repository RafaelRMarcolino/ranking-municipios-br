#!/bin/bash
set -e

echo "🟢 Iniciando o spark-submit do silver_transform_aluguel_populacao..."

if [[ -z "$AWS_ACCESS_KEY_ID" || -z "$AWS_SECRET_ACCESS_KEY" ]]; then
  echo "❌ Variáveis AWS não definidas."
  exit 1
fi

# Define o diretório raiz dos DAGs como PYTHONPATH
export PYTHONPATH="/usr/local/airflow/dags"

# Executa o job Spark
/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
  --conf spark.hadoop.fs.s3a.access.key="${AWS_ACCESS_KEY_ID}" \
  --conf spark.hadoop.fs.s3a.secret.key="${AWS_SECRET_ACCESS_KEY}" \
  --conf spark.hadoop.fs.s3a.endpoint=s3.us-east-2.amazonaws.com \
  --conf spark.hadoop.fs.s3a.path.style.access=true \
  /usr/local/airflow/dags/transform/silver_transform_aluguel_populacao.py

echo "✅ Finalizado com sucesso."
