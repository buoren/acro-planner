terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Optional: Configure backend for state storage
  # Uncomment and configure after creating the bucket
  # backend "gcs" {
  #   bucket = "acro-planner-terraform-state"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "random" {}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",              # Cloud Run
    "sqladmin.googleapis.com",          # Cloud SQL
    "compute.googleapis.com",           # Compute Engine (for Cloud SQL)
    "containerregistry.googleapis.com", # Container Registry
    "cloudbuild.googleapis.com",        # Cloud Build
    "secretmanager.googleapis.com",     # Secret Manager
    "artifactregistry.googleapis.com",  # Artifact Registry
    "iam.googleapis.com",               # IAM
  ])

  service            = each.value
  disable_on_destroy = false
}

# Create Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "backend_repo" {
  location      = var.region
  repository_id = "acro-planner"
  description   = "Docker repository for Acro Planner backend"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}