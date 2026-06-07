# In this setup, RDS is actually provisioned via docker-compose (postgres container).
# This file is a placeholder for actual AWS RDS Terraform configuration if moved to cloud.

resource "aws_db_instance" "knowledgeos_db" {
  count                = 0 # Disabled for local setup
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "15.3"
  instance_class       = "db.t3.micro"
  db_name              = "kgpone"
  username             = "user"
  password             = "password"
  skip_final_snapshot  = true
}
