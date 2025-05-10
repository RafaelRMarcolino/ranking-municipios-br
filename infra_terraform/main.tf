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
