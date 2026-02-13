##############################################################################
# Voice of the People – GCP Serverless Pipeline
# Terraform Configuration
##############################################################################

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

# ──────────────────────────────────────────────────────────────────────────────
# Provider
# ──────────────────────────────────────────────────────────────────────────────
provider "google" {
  project = var.project_id
  region  = var.region
}

# ──────────────────────────────────────────────────────────────────────────────
# 1. Enable Required APIs
# ──────────────────────────────────────────────────────────────────────────────
resource "google_project_service" "vision_api" {
  project            = var.project_id
  service            = "vision.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudfunctions_api" {
  project            = var.project_id
  service            = "cloudfunctions.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudbuild_api" {
  project            = var.project_id
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "eventarc_api" {
  project            = var.project_id
  service            = "eventarc.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "run_api" {
  project            = var.project_id
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "aiplatform_api" {
  project            = var.project_id
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# ──────────────────────────────────────────────────────────────────────────────
# 2. Google Cloud Storage Buckets
# ──────────────────────────────────────────────────────────────────────────────
resource "google_storage_bucket" "raw_reports" {
  name                        = "${var.project_id}-${var.raw_bucket_name}"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365 # Auto-cleanup after 1 year
    }
  }
}

resource "google_storage_bucket" "processed_thumbnails" {
  name                        = "${var.project_id}-${var.processed_bucket_name}"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
}

# ──────────────────────────────────────────────────────────────────────────────
# 3. Service Account for Cloud Function
# ──────────────────────────────────────────────────────────────────────────────
resource "google_service_account" "vision_pipeline_sa" {
  account_id   = "vision-pipeline-sa"
  display_name = "Voice of the People – Vision Pipeline Service Account"
  project      = var.project_id
}

# Grant roles/vision.aiUser so the function can call the Vision API
# Grant roles/serviceusage.serviceUsageConsumer so the function can check quota/billing
resource "google_project_iam_member" "sa_vision_user" {
  project = var.project_id
  role    = "roles/serviceusage.serviceUsageConsumer"
  member  = "serviceAccount:${google_service_account.vision_pipeline_sa.email}"

  depends_on = [google_project_service.vision_api]
}

# Grant roles/aiplatform.user so the function can call Gemini via Vertex AI
resource "google_project_iam_member" "sa_aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.vision_pipeline_sa.email}"

  depends_on = [google_project_service.aiplatform_api]
}

# Grant roles/storage.objectAdmin so the function can read/write to GCS
resource "google_project_iam_member" "sa_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.vision_pipeline_sa.email}"
}

# Grant roles/eventarc.eventReceiver so Eventarc can invoke the function
resource "google_project_iam_member" "sa_eventarc_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${google_service_account.vision_pipeline_sa.email}"
}

# Grant roles/run.invoker so the service account (used by Eventarc) can invoke the Cloud Run service
resource "google_project_iam_member" "sa_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.vision_pipeline_sa.email}"
}

# ──────────────────────────────────────────────────────────────────────────────
# 3b. Service Agent Permissions (Required for Eventarc Triggers)
# ──────────────────────────────────────────────────────────────────────────────

data "google_project" "project" {}

# Use this data source to get the GCS service agent email.
# It also ensures the service agent is created if it doesn't exist.
data "google_storage_project_service_account" "gcs_account" {
}

# Grant the Eventarc Service Agent the "Eventarc Service Agent" role
resource "google_project_iam_member" "eventarc_service_agent" {
  project = var.project_id
  role    = "roles/eventarc.serviceAgent"
  member  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-eventarc.iam.gserviceaccount.com"

  depends_on = [google_project_service.eventarc_api]
}

# Grant the Cloud Storage Service Agent permission to publish to Pub/Sub
# (Required for GCS triggers to work with Eventarc)
resource "google_project_iam_member" "storage_service_agent_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"

  depends_on = [google_project_service.eventarc_api]
}

# ──────────────────────────────────────────────────────────────────────────────
# 4. Cloud Function Source Code (zipped from local dir)
# ──────────────────────────────────────────────────────────────────────────────

# Bucket to hold the function source archive
resource "google_storage_bucket" "function_source" {
  name                        = "${var.project_id}-gcf-source"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
}

data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "${path.module}/function_source"
  output_path = "${path.module}/.tmp/function-source.zip"
}

resource "google_storage_bucket_object" "function_archive" {
  name   = "function-source-${data.archive_file.function_zip.output_md5}.zip"
  bucket = google_storage_bucket.function_source.name
  source = data.archive_file.function_zip.output_path
}

# ──────────────────────────────────────────────────────────────────────────────
# 5. Cloud Function (Gen 2) – Vision Pipeline Processor
#    Triggered by finalize events on the raw-reports bucket via Eventarc.
# ──────────────────────────────────────────────────────────────────────────────
resource "google_cloudfunctions2_function" "process_image" {
  name     = "process-image"
  location = var.region
  project  = var.project_id

  depends_on = [
    google_project_service.cloudfunctions_api,
    google_project_service.cloudbuild_api,
    google_project_service.eventarc_api,
    google_project_service.run_api,
    google_project_iam_member.eventarc_service_agent,
    google_project_iam_member.storage_service_agent_pubsub,
  ]

  build_config {
    runtime     = "python312"
    entry_point = var.function_entry_point

    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_archive.name
      }
    }
  }

  service_config {
    max_instance_count    = 10
    min_instance_count    = 0
    available_memory      = "512Mi"
    timeout_seconds       = 300
    service_account_email = google_service_account.vision_pipeline_sa.email

    environment_variables = {
      PROCESSED_BUCKET = google_storage_bucket.processed_thumbnails.name
      GCP_PROJECT_ID   = var.project_id
      GEMINI_MODEL     = var.gemini_model
      SIGHTENGINE_USER = var.sightengine_user
      SIGHTENGINE_SECRET = var.sightengine_secret
    }
  }

  event_trigger {
    trigger_region        = var.region
    event_type            = "google.cloud.storage.object.v1.finalized"
    retry_policy          = "RETRY_POLICY_RETRY"
    service_account_email = google_service_account.vision_pipeline_sa.email

    event_filters {
      attribute = "bucket"
      value     = google_storage_bucket.raw_reports.name
    }
  }
}
