# Generate random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Store database password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.db_instance_name}-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Cloud SQL Instance
resource "google_sql_database_instance" "mysql" {
  name             = var.db_instance_name
  database_version = var.db_version
  region           = var.region

  settings {
    tier      = var.db_tier
    disk_size = var.db_disk_size
    disk_type = "PD_SSD"

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      location                       = var.region
      binary_log_enabled             = true
      transaction_log_retention_days = 7
    }

    ip_configuration {
      ipv4_enabled    = true
      private_network = null
      
      # Allow access from Cloud Run (will be restricted via Cloud SQL Proxy)
      authorized_networks {
        name  = "allow-all-for-dev"
        value = "0.0.0.0/0"
      }
    }

    insights_config {
      query_insights_enabled  = true
      query_plans_per_minute  = 5
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }

  deletion_protection = false # Set to true in production

  depends_on = [google_project_service.required_apis]
}

# Database
resource "google_sql_database" "database" {
  name     = var.db_name
  instance = google_sql_database_instance.mysql.name

  lifecycle {
    prevent_destroy = false # Set to true in production
  }
}

# Database User
resource "google_sql_user" "db_user" {
  name     = var.db_user
  instance = google_sql_database_instance.mysql.name
  password = random_password.db_password.result

  lifecycle {
    ignore_changes = [password]
  }
}