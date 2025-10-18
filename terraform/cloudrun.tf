# Cloud Run Service
resource "google_cloud_run_service" "backend" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.cloud_run_sa.email
      containers {
        # Initial image - will be updated by CI/CD
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}/${var.service_name}:latest"
        
        ports {
          container_port = var.container_port
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name = "DATABASE_URL"
          value = format(
            "mysql+pymysql://%s:%s@/%s?unix_socket=/cloudsql/%s",
            var.db_user,
            random_password.db_password.result,
            var.db_name,
            google_sql_database_instance.mysql.connection_name
          )
        }

        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "REGION"
          value = var.region
        }

        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
        }

        # Health check probe
        startup_probe {
          http_get {
            path = "/health"
            port = var.container_port
          }
          initial_delay_seconds = 5
          timeout_seconds       = 5
          period_seconds        = 10
          failure_threshold     = 3
        }

        liveness_probe {
          http_get {
            path = "/health"
            port = var.container_port
          }
          initial_delay_seconds = 30
          timeout_seconds       = 5
          period_seconds        = 30
          failure_threshold     = 3
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"        = tostring(var.min_instances)
        "autoscaling.knative.dev/maxScale"        = tostring(var.max_instances)
        "run.googleapis.com/cloudsql-instances"   = google_sql_database_instance.mysql.connection_name
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    ignore_changes = [
      template[0].spec[0].containers[0].image,
      template[0].metadata[0].annotations["client.knative.dev/user-image"],
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"],
    ]
  }

  depends_on = [
    google_project_service.required_apis,
    google_sql_database_instance.mysql,
    google_artifact_registry_repository.backend_repo,
  ]
}

# IAM policy to allow unauthenticated access (if enabled)
resource "google_cloud_run_service_iam_member" "public_access" {
  count = var.allow_unauthenticated ? 1 : 0

  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Build trigger for automated deployments (commented out - requires GitHub repository connection)
# resource "google_cloudbuild_trigger" "deploy_trigger" {
#   name        = "${var.service_name}-deploy"
#   description = "Deploy ${var.service_name} to Cloud Run"

#   github {
#     owner = "YOUR_GITHUB_USERNAME" # Replace with your GitHub username
#     name  = "acro-planner"
#     push {
#       branch = "^main$"
#     }
#   }

#   build {
#     step {
#       name = "gcr.io/cloud-builders/docker"
#       args = [
#         "build",
#         "-t",
#         "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}/${var.service_name}:$COMMIT_SHA",
#         "-t",
#         "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}/${var.service_name}:latest",
#         "./server"
#       ]
#     }

#     step {
#       name = "gcr.io/cloud-builders/docker"
#       args = [
#         "push",
#         "--all-tags",
#         "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}/${var.service_name}"
#       ]
#     }

#     step {
#       name = "gcr.io/google.com/cloudsdktool/cloud-sdk"
#       entrypoint = "gcloud"
#       args = [
#         "run",
#         "deploy",
#         var.service_name,
#         "--image",
#         "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}/${var.service_name}:$COMMIT_SHA",
#         "--region",
#         var.region,
#         "--platform",
#         "managed",
#         "--service-account",
#         google_service_account.cloud_run_sa.email,
#       ]
#     }

#     options {
#       logging = "CLOUD_LOGGING_ONLY"
#     }
#   }

#   service_account = google_service_account.cloud_build_sa.id

#   depends_on = [google_project_service.required_apis]
# }