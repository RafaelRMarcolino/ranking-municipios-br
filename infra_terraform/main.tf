provider "aws" {
  region = var.region
}

# ====================
# Athena Workgroups
# ====================

resource "aws_athena_workgroup" "bronze" {
  name = "bronze_workgroup"

  configuration {
    enforce_workgroup_configuration = true
    result_configuration {
      output_location = "s3://ranking-municipios-br/athena-results/"
    }
  }

  state = "ENABLED"

  tags = {
    Environment = "dev"
    Project     = "Ranking Municipios"
  }
}

resource "aws_athena_workgroup" "silver" {
  name = "silver_workgroup"

  configuration {
    enforce_workgroup_configuration = true
    result_configuration {
      output_location = "s3://ranking-municipios-br/athena-results/"
    }
  }

  state = "ENABLED"

  tags = {
    Environment = "dev"
    Project     = "Ranking Municipios"
  }
}

resource "aws_athena_workgroup" "gold" {
  name = "gold_workgroup"

  configuration {
    enforce_workgroup_configuration = true
    result_configuration {
      output_location = "s3://ranking-municipios-br/athena-results/"
    }
  }

  state = "ENABLED"

  tags = {
    Environment = "dev"
    Project     = "Ranking Municipios"
  }
}



# ====================
# Glue Databases
# ====================

resource "aws_glue_catalog_database" "bronze_db" {
  name        = "bronze"
  description = "Banco de dados do Glue para camada Bronze"
}

resource "aws_glue_catalog_database" "silver_db" {
  name        = "silver"
  description = "Banco de dados do Glue para camada Silver"
}

resource "aws_glue_catalog_database" "gold_db" {
  name        = "gold"
  description = "Banco de dados do Glue para camada Gold"
}


# ====================
# Glue Tables - Bronze
# ====================

resource "aws_glue_catalog_table" "cesta_basica" {
  name          = "cesta_basica"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://ranking-municipios-br/bronze/dieese/cesta_basica/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
    compressed    = false

    ser_de_info {
      name                  = "parquet"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "data_mes"
      type = "string"
    }

    columns {
      name = "cidade"
      type = "string"
    }

    columns {
      name = "valor"
      type = "double"
    }
  }

  partition_keys {
    name = "data_carga"
    type = "string"
  }
}

# Glue Table: aluguel_medio
resource "aws_glue_catalog_table" "aluguel_medio" {
  name          = "aluguel_medio"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://ranking-municipios-br/bronze/aluguel_medio/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
    compressed    = false

    ser_de_info {
      name                  = "parquet"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "id"
      type = "int"
    }
    columns {
      name = "city"
      type = "string"
    }
    columns {
      name = "area"
      type = "int"
    }
    columns {
      name = "rooms"
      type = "int"
    }
    columns {
      name = "bathroom"
      type = "int"
    }
    columns {
      name = "parking_spaces"
      type = "int"
    }
    columns {
      name = "floor"
      type = "int"
    }
    columns {
      name = "animal"
      type = "int"
    }
    columns {
      name = "furniture"
      type = "int"
    }
    columns {
      name = "hoa"
      type = "int"
    }
    columns {
      name = "rent_amount"
      type = "int"
    }
    columns {
      name = "property_tax"
      type = "int"
    }
    columns {
      name = "fire_insurance"
      type = "int"
    }
    columns {
      name = "total"
      type = "int"
    }
  }

  partition_keys {
    name = "data_carga"
    type = "string"
  }
}


# Glue Table: populacao_estimada_uf
resource "aws_glue_catalog_table" "populacao_estimada_uf" {
  name          = "populacao_estimada_uf"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://ranking-municipios-br/bronze/ibge/populacao_estimada/brasil_uf/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
    compressed    = false

    ser_de_info {
      name                  = "parquet"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "unidade_federativa"
      type = "string"
    }
    columns {
      name = "populacao"
      type = "int"
    }
  }

  partition_keys {
    name = "data_carga"
    type = "string"
  }
}

# Glue Table: populacao_estimada_municipios
resource "aws_glue_catalog_table" "populacao_estimada_municipios" {
  name          = "populacao_estimada_municipios"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://ranking-municipios-br/bronze/ibge/populacao_estimada/municipios/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
    compressed    = false

    ser_de_info {
      name                  = "parquet"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "uf"
      type = "string"
    }
    columns {
      name = "cod_uf"
      type = "int"
    }
    columns {
      name = "cod_municipio"
      type = "int"
    }
    columns {
      name = "municipio"
      type = "string"
    }
    columns {
      name = "populacao"
      type = "int"
    }
  }

  partition_keys {
    name = "data_carga"
    type = "string"
  }
}

# ====================
# Glue Tables - Silver
# ====================

# Glue Table: aluguel_populacao
resource "aws_glue_catalog_table" "aluguel_populacao" {
  name          = "aluguel_populacao"
  database_name = aws_glue_catalog_database.silver_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://ranking-municipios-br/silver/aluguel_populacao/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
    compressed    = false

    ser_de_info {
      name                  = "parquet"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "area"
      type = "int"
    }
    columns {
      name = "rooms"
      type = "int"
    }
    columns {
      name = "bathroom"
      type = "int"
    }
    columns {
      name = "parking_spaces"
      type = "int"
    }
    columns {
      name = "floor"
      type = "int"
    }
    columns {
      name = "animal"
      type = "int"
    }
    columns {
      name = "furniture"
      type = "int"
    }
    columns {
      name = "rent_amount"
      type = "int"
    }
    columns {
      name = "total"
      type = "int"
    }
    columns {
      name = "city_codigo"
      type = "int"
    }
    columns {
      name = "city"
      type = "string"
    }
    columns {
      name = "aluguel_m2"
      type = "double"
    }
    columns {
      name = "populacao"
      type = "int"
    }
    columns {
      name = "aluguel_per_capita"
      type = "double"
    }
  }

  partition_keys {
    name = "data_carga"
    type = "string"
  }
}


# Glue Table: cesta_basica_full
resource "aws_glue_catalog_table" "cesta_basica_full" {
  name          = "cesta_basica_full"
  database_name = aws_glue_catalog_database.silver_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://ranking-municipios-br/silver/cesta_basica_full/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
    compressed    = false

    ser_de_info {
      name                  = "parquet"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "city_code"
      type = "int"
    }
    columns {
      name = "cidade_cesta"
      type = "string"
    }
    columns {
      name = "uf"
      type = "string"
    }
    columns {
      name = "valor_cesta"
      type = "double"
    }
    columns {
      name = "cod_municipio"
      type = "bigint"
    }
    columns {
      name = "populacao"
      type = "bigint"
    }
    columns {
      name = "estado"
      type = "string"
    }
  }

  partition_keys {
    name = "data_carga"
    type = "string"
  }
}

resource "aws_glue_catalog_table" "aluguel_populacao_gold" {
  name          = "aluguel_populacao_gold"
  database_name = aws_glue_catalog_database.gold_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
    EXTERNAL       = "TRUE"
  }

  storage_descriptor {
    location      = "s3://ranking-municipios-br/gold/aluguel_populacao_gold/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
    compressed    = false

    ser_de_info {
      name                  = "parquet"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "city"
      type = "string"
    }
    columns {
      name = "aluguel_m2_calculado"
      type = "double"
    }
    columns {
      name = "total_cost"
      type = "double"
    }
    columns {
      name = "aluguel_per_room"
      type = "double"
    }

    stored_as_sub_directories = false
  }

  partition_keys {
    name = "data_carga"
    type = "string"
  }
}


resource "aws_glue_catalog_table" "cesta_basica_gold" {
  name          = "cesta_basica_gold"
  database_name = aws_glue_catalog_database.gold_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
    EXTERNAL       = "TRUE"
  }

  storage_descriptor {
    location      = "s3://ranking-municipios-br/gold/cesta_basica_gold/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
    compressed    = false

    ser_de_info {
      name                  = "parquet"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "city_code"
      type = "int"
    }
    columns {
      name = "cidade_cesta"
      type = "string"
    }
    columns {
      name = "estado"
      type = "string"
    }
    columns {
      name = "valor_cesta_medio"
      type = "double"
    }
    columns {
      name = "populacao"
      type = "bigint"
    }
    columns {
      name = "valor_total_gasto"
      type = "double"
    }

    stored_as_sub_directories = false
  }

  partition_keys {
    name = "data_carga"
    type = "string"
  }
}


