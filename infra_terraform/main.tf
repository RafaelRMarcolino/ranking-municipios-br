# Provisionamento de Glue + Athena com Terraform

provider "aws" {
  region = var.region
}

# 1. Criar o banco de dados no Glue
resource "aws_glue_catalog_database" "bronze_db" {
  name        = "bronze"
  description = "Banco de dados do Glue para camada Bronze"
}

# 2. Tabela externa: cesta básica
resource "aws_glue_catalog_table" "cesta_basica" {
  name          = "cesta_basica"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification     = "parquet"
    has_encrypted_data = "false"
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
      type = "timestamp"
    }
    columns {
      name = "cidade"
      type = "string"
    }
    columns {
      name = "valor"
      type = "float"
    }
    columns {
      name = "data_carga"
      type = "timestamp"
    }
  }

  partition_keys {
    name = "ano"
    type = "int"
  }
  partition_keys {
    name = "mes"
    type = "int"
  }
}

# 3. Tabela externa: aluguel médio
resource "aws_glue_catalog_table" "aluguel_medio" {
  name          = "aluguel_medio"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification     = "parquet"
    has_encrypted_data = "false"
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
      name = "city"
      type = "string"
    }
    columns {
      name = "aluguel"
      type = "float"
    }
    columns {
      name = "data_carga"
      type = "timestamp"
    }
  }

  partition_keys {
    name = "ano"
    type = "int"
  }
  partition_keys {
    name = "mes"
    type = "int"
  }
}

# 4. Tabela externa: população estimada (✅ CAMINHO CORRIGIDO)
resource "aws_glue_catalog_table" "populacao_estimada" {
  name          = "populacao_estimada"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification     = "parquet"
    has_encrypted_data = "false"
  }

  storage_descriptor {
    # ✅ CAMINHO ATUALIZADO COM /ibge/
    location      = "s3://ranking-municipios-br/bronze/ibge/populacao_estimada/"
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
    columns {
      name = "data_carga"
      type = "timestamp"
    }
  }

  partition_keys {
    name = "ano"
    type = "int"
  }
  partition_keys {
    name = "mes"
    type = "int"
  }
  partition_keys {
    name = "dia"
    type = "int"
  }
}

# 5. Workgroup do Athena
resource "aws_athena_workgroup" "default" {
  name = "bronze_workgroup"

  configuration {
    enforce_workgroup_configuration = true

    result_configuration {
      output_location = "s3://ranking-municipios-br/athena-results/"
    }
  }

  force_destroy = true
}
