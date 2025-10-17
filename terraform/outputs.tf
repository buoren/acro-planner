output "cloud_run_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.backend.status[0].url
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection name for the instance"
  value       = google_sql_database_instance.mysql.connection_name
}

output "cloud_sql_ip_address" {
  description = "IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.mysql.ip_address[0].ip_address
  sensitive   = true
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}"
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Run"
  value       = google_service_account.cloud_run_sa.email
}

output "database_password_secret" {
  description = "Name of the secret containing the database password"
  value       = google_secret_manager_secret.db_password.id
}

output "deployment_commands" {
  description = "Commands to build and deploy the application"
  value = {
    build_image = "docker build -t ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}/${var.service_name}:latest ./server"
    push_image  = "docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}/${var.service_name}:latest"
    deploy      = "gcloud run deploy ${var.service_name} --image=${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}/${var.service_name}:latest --region=${var.region}"
  }
}