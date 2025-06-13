from pyspark.sql import SparkSession

# Criar sessão Spark
spark = SparkSession.builder \
    .appName("TesteSpark") \
    .getOrCreate()

# Criar um pequeno DataFrame
data = [("Alice", 28), ("Bob", 35), ("Carol", 23)]
df = spark.createDataFrame(data, ["nome", "idade"])

# Mostrar conteúdo
df.show()
