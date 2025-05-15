# Provisionamento de Glue + Athena com Terraform

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
      type = "string"
    }
    columns {
      name = "data_carga"
      type = "string"
    }
    columns {
      name = "brasilia"
      type = "double"
    }
    columns {
      name = "campo_grande"
      type = "double"
    }
    columns {
      name = "cuiaba"
      type = "double"
    }
    columns {
      name = "goiania"
      type = "double"
    }
    columns {
      name = "belo_horizonte"
      type = "double"
    }
    columns {
      name = "rio_de_janeiro"
      type = "double"
    }
    columns {
      name = "sao_paulo"
      type = "double"
    }
    columns {
      name = "vitoria"
      type = "double"
    }
    columns {
      name = "curitiba"
      type = "double"
    }
    columns {
      name = "florianopolis"
      type = "double"
    }
    columns {
      name = "porto_alegre"
      type = "double"
    }
    columns {
      name = "belem"
      type = "double"
    }
    columns {
      name = "boa_vista"
      type = "double"
    }
    columns {
      name = "macapa"
      type = "double"
    }
    columns {
      name = "manaus"
      type = "double"
    }
    columns {
      name = "palmas"
      type = "double"
    }
    columns {
      name = "porto_velho"
      type = "double"
    }
    columns {
      name = "rio_branco"
      type = "double"
    }
    columns {
      name = "aracaju"
      type = "double"
    }
    columns {
      name = "fortaleza"
      type = "double"
    }
    columns {
      name = "joao_pessoa"
      type = "double"
    }
    columns {
      name = "maceio"
      type = "double"
    }
    columns {
      name = "natal"
      type = "double"
    }
    columns {
      name = "recife"
      type = "double"
    }
    columns {
      name = "salvador"
      type = "double"
    }
    columns {
      name = "sao_luis"
      type = "double"
    }
    columns {
      name = "teresina"
      type = "double"
    }
    columns {
      name = "macae"
      type = "double"
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
    columns {
      name = "data_carga"
      type = "string"
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

# 4b. Tabela externa: população estimada por UF
resource "aws_glue_catalog_table" "populacao_estimada_uf" {
  name          = "populacao_estimada_uf"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification     = "parquet"
    has_encrypted_data = "false"
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
    columns {
      name = "data_carga"
      type = "string"
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

# 4c. Tabela externa: população estimada por municípios
resource "aws_glue_catalog_table" "populacao_estimada_municipios" {
  name          = "populacao_estimada_municipios"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification     = "parquet"
    has_encrypted_data = "false"
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
    columns {
      name = "data_carga"
      type = "string"
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