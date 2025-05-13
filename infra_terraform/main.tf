provider "aws" {
  region = var.region
}

resource "aws_db_instance" "postgres_instance" {
  identifier           = "ranking-municipios-db"
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "15.12"
  instance_class       = "db.t3.micro"
  db_name              = var.db_name            
  username             = var.db_user
  password             = var.db_password
  parameter_group_name = "default.postgres15"
  skip_final_snapshot  = true
  publicly_accessible  = true
}


# Provisionamento de Glue + Athena com Terraform

# 1. Criar o banco de dados no Glue
resource "aws_glue_catalog_database" "bronze_db" {
  name = "bronze"
  description = "Banco de dados do Glue para camada Bronze"
}

# 2. Criar a tabela externa de cesta básica no Glue
resource "aws_glue_catalog_table" "cesta_basica" {
  name          = "cesta_basica"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification        = "parquet"
    has_encrypted_data    = "false"
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

# 3. Criar a tabela externa de aluguel médio no Glue
resource "aws_glue_catalog_table" "aluguel_medio" {
  name          = "aluguel_medio"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification        = "parquet"
    has_encrypted_data    = "false"
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

# 4. Criar a tabela externa de população estimada no Glue
resource "aws_glue_catalog_table" "populacao_estimada" {
  name          = "populacao_estimada"
  database_name = aws_glue_catalog_database.bronze_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification        = "parquet"
    has_encrypted_data    = "false"
  }

  storage_descriptor {
    location      = "s3://ranking-municipios-br/bronze/populacao_estimada/"
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
      type = "date"
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

# 5. Criar o Workgroup do Athena (opcional)
resource "aws_athena_workgroup" "default" {
  name = "bronze_workgroup"

  configuration {
    enforce_workgroup_configuration = true

    result_configuration {
      output_location = "s3://ranking-municipios-br/athena-results/"
    }
  }
}
