##############################################################################
# Voice of the People – Terraform Variables
##############################################################################

variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for all resources."
  type        = string
  default     = "us-central1"
}

variable "raw_bucket_name" {
  description = "Name of the GCS bucket for raw incident reports."
  type        = string
  default     = "raw-reports-bucket"
}

variable "processed_bucket_name" {
  description = "Name of the GCS bucket for processed thumbnails."
  type        = string
  default     = "processed-thumbnails-bucket"
}

variable "function_entry_point" {
  description = "The entry-point function name inside the Cloud Function source."
  type        = string
  default     = "process_image"
}

variable "gemini_model" {
  description = "The Gemini model to use for civic intelligence analysis."
  type        = string
  default     = "gemini-2.5-pro"
}

variable "sightengine_user" {
  description = "Sightengine API User ID"
  type        = string
}

variable "sightengine_secret" {
  description = "Sightengine API Secret"
  type        = string
}
