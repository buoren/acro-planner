variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Cloud SQL Configuration
variable "db_instance_name" {
  description = "Cloud SQL instance name"
  type        = string
  default     = "acro-planner-mysql"
}

variable "db_version" {
  description = "MySQL version for Cloud SQL"
  type        = string
  default     = "MYSQL_8_0"
}

variable "db_tier" {
  description = "Machine type for Cloud SQL instance"
  type        = string
  default     = "db-f1-micro" # Smallest tier for development
}

variable "db_disk_size" {
  description = "Disk size in GB for Cloud SQL instance"
  type        = number
  default     = 10
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "acro_planner"
}

variable "db_user" {
  description = "Database user"
  type        = string
  default     = "acro_user"
}

# Cloud Run Configuration
variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "acro-planner-backend"
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8080
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run service"
  type        = string
  default     = "512Mi"
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run service"
  type        = string
  default     = "1"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to Cloud Run service"
  type        = bool
  default     = true
}