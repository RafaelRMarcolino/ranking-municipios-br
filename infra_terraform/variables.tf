variable "region" {
  default = "us-east-2"
}

variable "db_name" {
  default = "db_datamaster"
}

variable "db_user" {
  default = "postgres"
}


variable "db_password" {
  description = "password db"
  sensitive   = true
  default     = "Data1889"
}

