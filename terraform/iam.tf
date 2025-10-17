# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name}"
  description  = "Service account for Cloud Run service ${var.service_name}"
}

# Service Account for Cloud Build
resource "google_service_account" "cloud_build_sa" {
  account_id   = "acro-planner-build-sa"
  display_name = "Cloud Build Service Account"
  description  = "Service account for Cloud Build to deploy to Cloud Run"
}

# Grant Cloud Run service account access to Cloud SQL
resource "google_project_iam_member" "cloud_run_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Grant Cloud Run service account access to Secret Manager
resource "google_secret_manager_secret_iam_member" "cloud_run_secret_accessor" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Grant Cloud Build service account permissions to deploy
resource "google_project_iam_member" "cloud_build_permissions" {
  for_each = toset([
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
    "roles/artifactregistry.writer",
    "roles/cloudbuild.builds.builder",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_build_sa.email}"
}

# Allow Cloud Build to act as Cloud Run service account
resource "google_service_account_iam_member" "cloud_build_act_as" {
  service_account_id = google_service_account.cloud_run_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cloud_build_sa.email}"
}

# Grant Artifact Registry permissions
resource "google_artifact_registry_repository_iam_member" "cloud_build_repo_admin" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.backend_repo.name
  role       = "roles/artifactregistry.repoAdmin"
  member     = "serviceAccount:${google_service_account.cloud_build_sa.email}"
}

resource "google_artifact_registry_repository_iam_member" "cloud_run_repo_reader" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.backend_repo.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Grant default compute service account access to Artifact Registry (for initial builds)
resource "google_artifact_registry_repository_iam_member" "compute_repo_admin" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.backend_repo.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Data source to get project number
data "google_project" "project" {
  project_id = var.project_id
}