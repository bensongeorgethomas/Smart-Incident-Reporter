# Testing the Vision Pipeline

This guide explains how to manually test the deployed Voice of the People serverless pipeline.

## Prerequisites
- Ensure you have `gcloud` and `gsutil` installed and authenticated.
- Set your project ID:
  ```powershell
  gcloud config set project smart-incident-reporter-364cd
  ```

## Automated Test Script
A PowerShell script has been created to automate the testing process. Run the following command in PowerShell:

```powershell
.\test_pipeline.ps1
```

This script will:
1. Download a test image.
2. Upload it to the `raw-reports` bucket.
3. Wait for processing.
4. Check the `processed-thumbnails` bucket for the result.
5. Display the Cloud Function logs.

## Manual Testing Steps

If you prefer to test manually, follow these steps:

### 1. Upload a Test Image
Upload an image (JPEG or PNG) to the raw reports bucket.

```powershell
# Upload a local image
gsutil cp path/to/your/image.jpg gs://smart-incident-reporter-364cd-raw-reports-bucket/
```

### 2. Monitor Logs
Check the Cloud Function logs to see the processing status.

```powershell
gcloud functions logs read process-image --region=us-central1 --limit=20
```

You should see logs indicating:
- `📷 Processing image: ...`
- `🏷️ Top 3 Vision AI Labels: ...`
- `🛡️ SafeSearch Results: ...`
- `📤 Thumbnail saved to ...`

### 3. Verify Output
Check if the thumbnail was created in the processed bucket.

```powershell
gsutil ls gs://smart-incident-reporter-364cd-processed-thumbnails-bucket/thumbnails/
```

You can download the thumbnail to verify it:

```powershell
gsutil cp gs://smart-incident-reporter-364cd-processed-thumbnails-bucket/thumbnails/image_thumb.jpg .
```

## Troubleshooting

- **No Logs?** The trigger might take a few minutes to propagate initially. Wait 5 minutes and try uploading a new image.
- **Permission Errors?** Ensure your `gcloud` account has permission to list buckets and read logs.
- **Function Validation Error?** If the function fails to deploy or run, check the `gcloud functions logs` for stack traces.
