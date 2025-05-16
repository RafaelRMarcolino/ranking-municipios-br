from pyspark.sql.functions import col, when, lit, round
from pyspark.sql.types import IntegerType

# 🔧 Limpeza e ajustes iniciais
df_aluguel_silver = (
    df_aluguel
    .withColumn("area", col("area").cast(IntegerType()))
    .withColumn("rent_amount", col("rent amount").cast(IntegerType()))
    .withColumn("total", col("total").cast(IntegerType()))
    .withColumn("city", col("city").cast("string"))
    .withColumn("aluguel_m2", round(col("rent amount") / col("area"), 2))
    .drop("id", "hoa", "property tax", "fire insurance", "rent amount")  # opcional
    .dropna(subset=["area", "rent_amount", "total", "city"])
)

# 👥 Join com população estimada por município
# Vamos normalizar os nomes das cidades para facilitar o join

df_municipios_clean = df_pop_mun.withColumnRenamed("municipio", "city")
df_municipios_clean = df_municipios_clean.withColumn("city", col("city").cast("string"))

# 🔗 Realizar o JOIN por cidade
df_final = df_aluguel_silver.join(
    df_municipios_clean.select("city", "populacao"),
    on="city",
    how="left"
)

# ➕ Criar mais uma métrica: percentual de aluguel per capita
df_final = df_final.withColumn(
    "aluguel_per_capita",
    round(col("total") / col("populacao"), 6)
)

# 📦 Exportar para Parquet local (ajuste caminho se for salvar no S3)
df_final.write.mode("overwrite").partitionBy("data_carga").parquet("silver/aluguel_medio/")
















from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit, round, trim, floor, rand
from pyspark.sql.types import IntegerType



# Criar sessão Spark
spark = SparkSession.builder.appName("Transformação Silver com Join").getOrCreate()

# 📍 Mapeamento de código da cidade para nome de estado
codigo_para_estado = {
    0: "Rondônia",
    1: "Acre",
    2: "Amazonas",
    3: "Roraima",
    4: "Pará",
    5: "Amapá",
    6: "Tocantins",
    8: "Maranhão",
    9: "Piauí",
    10: "Ceará",
    11: "Rio Grande do Norte",
    12: "Paraíba",
    13: "Pernambuco",
    14: "Alagoas",
    15: "Sergipe",
    16: "Bahia",
    17: "Minas Gerais",
    18: "Espírito Santo",
    19: "Rio de Janeiro",
    20: "São Paulo",
    22: "Paraná",
    23: "Santa Catarina",
    24: "Rio Grande do Sul",
    26: "Mato Grosso do Sul",
    27: "Mato Grosso",
    28: "Goiás",
    29: "Distrito Federal"
}

# Converter dicionário para DataFrame de mapeamento
df_mapeamento = spark.createDataFrame(
    [(k, v) for k, v in codigo_para_estado.items()],
    ["city_codigo", "city_nome"]
)

# Transformação
df_aluguel_silver = (
    df_aluguel
    .withColumn("area", col("area").cast(IntegerType()))
    .withColumn("rent_amount", col("rent amount").cast(IntegerType()))
    .withColumn("total", col("total").cast(IntegerType()))
    .withColumn("city_codigo", floor(rand() * 30).cast(IntegerType()))  # 🎲 atribui valor aleatório entre 0 e 29
    .drop("id", "hoa", "property tax", "fire insurance", "rent amount", "city")
    .dropna(subset=["area", "total", "city_codigo"])
    .join(df_mapeamento, on="city_codigo", how="left")  # 🔗 substitui código por nome
    .withColumnRenamed("city_nome", "city")
    .withColumn("aluguel_m2", round(col("total") / col("area"), 2))
)

df_aluguel_silver.show(10, truncate=False)
# df_aluguel_silver.show(5, truncate=False)

# 👥 Limpeza da população estimada por UF
df_municipios_clean = (
    df_pop_mun
    .withColumnRenamed("unidade_federativa", "city")
    .withColumn("city", trim(col("city")).cast("string"))
    .filter(
        (col("city").isNotNull()) &
        (col("city") != "") &
        (~col("city").rlike("Fonte:|Norte|Sul|Sudeste|Centro|Nordeste"))
    )
)

# df_municipios_clean.select("city").distinct().show(30, truncate=False)

# 🔗 JOIN Silver + população
df_final = (
    df_aluguel_silver
    .join(df_municipios_clean.select("city", "populacao"), on="city", how="left")
)

# df_final.show(10, truncate=False)


df_aluguel_silver.show()