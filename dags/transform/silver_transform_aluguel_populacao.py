from pyspark.sql import SparkSession
from pyspark.sql.functions import col, round, current_date, lit
from utils.spark_utils import criar_df_mapeamento_estado, limpar_df_municipios
import random
import os

print("🟢 Início do script Silver Aluguel População")

# Verificação das credenciais
if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
    raise ValueError("Credenciais AWS não encontradas nas variáveis de ambiente!")

# Configuração da sessão Spark com todas as recomendações
spark = SparkSession.builder \
    .appName("SilverAluguelPopulacao") \
    .config("spark.hadoop.fs.s3a.access.key", os.getenv("AWS_ACCESS_KEY_ID")) \
    .config("spark.hadoop.fs.s3a.secret.key", os.getenv("AWS_SECRET_ACCESS_KEY")) \
    .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "true") \
    .config("spark.hadoop.fs.s3a.attempts.maximum", "5") \
    .config("spark.hadoop.fs.s3a.connection.timeout", "10000") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
    .getOrCreate()


# ✅ Verifica se a variável de ambiente está visível dentro do container Spark



# Caminhos com partição
path_aluguel = "s3a://ranking-municipios-br/bronze/aluguel_medio/data_carga=2025-05-15/"
path_pop_mun = "s3a://ranking-municipios-br/bronze/ibge/populacao_estimada/brasil_uf/data_carga=2025-05-14/"

# Leitura dos dados
print("📂 Lendo df_aluguel do path:", path_aluguel)
df_aluguel = spark.read.parquet(path_aluguel)
print("✅ df_aluguel carregado com", df_aluguel.count(), "registros")

print("📂 Lendo df_pop_mun do path:", path_pop_mun)
df_pop_mun = spark.read.parquet(path_pop_mun)
print("✅ df_pop_mun carregado com", df_pop_mun.count(), "registros")

# Mapeamento de estados
print("🔁 Criando DataFrame de mapeamento de estado...")
df_mapeamento = criar_df_mapeamento_estado(spark)

# Geração de código aleatório no driver (evita UDFs)
print("🎲 Gerando códigos aleatórios para os registros de aluguel...")
codigos_estado = list(df_mapeamento.select("city_codigo").rdd.map(lambda x: x[0]).collect())
num_registros = df_aluguel.count()
codigos_aleatorios = [random.choice(codigos_estado) for _ in range(num_registros)]
df_codigos = spark.createDataFrame([(c,) for c in codigos_aleatorios], ["city_codigo"])

# Adiciona índice com zipWithIndex para join seguro
df_aluguel = df_aluguel.rdd.zipWithIndex().toDF(["data", "idx"])
df_codigos = df_codigos.rdd.zipWithIndex().toDF(["codigo", "idx"])

df_aluguel = df_aluguel.join(df_codigos, on="idx").select("data.*", "codigo.city_codigo")

# Transformações aluguel
print("🔄 Iniciando transformação de aluguel...")
df_aluguel_silver = (
    df_aluguel
    .withColumn("area", col("area").cast("int"))
    .withColumn("rent_amount", col("rent_amount").cast("int"))
    .withColumn("total", col("total").cast("int"))
    .drop("id", "hoa", "property_tax", "fire_insurance", "city")
    .dropna(subset=["area", "total", "city_codigo"])
    .join(df_mapeamento, on="city_codigo", how="left")
    .withColumnRenamed("city_nome", "city")
    .withColumn("aluguel_m2", round(col("total") / col("area"), 2))
)
print("✅ Transformação do df_aluguel concluída")

# Limpeza população
print("🧹 Limpando DataFrame de população...")
df_municipios_clean = limpar_df_municipios(df_pop_mun)
print("✅ Limpeza concluída")

# Join final
print("🔗 Realizando join entre aluguel e população...")
df_final = (
    df_aluguel_silver
    .join(df_municipios_clean.select("city", "populacao"), on="city", how="inner")
    .withColumn("aluguel_per_capita", round(col("total") / col("populacao"), 6))
    .withColumn("data_carga", current_date())
)
print("✅ Join concluído")

# Salvar
print("📊 Total de registros no resultado final:", df_final.count())
df_final.select("city", "populacao", "aluguel_per_capita", "data_carga").show(5)

print("💾 Salvando resultado na camada Silver...")
df_final.write.mode("overwrite") \
    .partitionBy("data_carga") \
    .parquet("s3a://ranking-municipios-br/silver/aluguel_populacao/")
print("✅ Dados salvos com sucesso")
