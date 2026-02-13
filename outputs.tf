##############################################################################
# Voice of the People – Terraform Outputs
##############################################################################

output "raw_reports_bucket_name" {
  description = "Name of the raw reports GCS bucket."
  value       = google_storage_bucket.raw_reports.name
}

output "processed_thumbnails_bucket_name" {
  description = "Name of the processed thumbnails GCS bucket."
  value       = google_storage_bucket.processed_thumbnails.name
}

output "cloud_function_name" {
  description = "Name of the deployed Cloud Function (Gen 2)."
  value       = google_cloudfunctions2_function.process_image.name
}

output "cloud_function_uri" {
  description = "HTTPS URI of the deployed Cloud Function."
  value       = google_cloudfunctions2_function.process_image.service_config[0].uri
}

output "service_account_email" {
  description = "Email of the Vision Pipeline service account."
  value       = google_service_account.vision_pipeline_sa.email
}
