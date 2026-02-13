$ProjectID = "smart-incident-reporter-364cd"
$RawBucket = "gs://${ProjectID}-raw-reports-bucket"
$ProcessedBucket = "gs://${ProjectID}-processed-thumbnails-bucket"
$FunctionName = "process-image"
$Region = "us-central1"

Write-Host "Downloading test image..."
Invoke-WebRequest -Uri "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg" -OutFile "test_cat.jpg"

Write-Host "Uploading to Raw Bucket ($RawBucket)..."
gsutil cp test_cat.jpg $RawBucket/test_cat.jpg

Write-Host "Waiting for 20 seconds for Cloud Function to process..."
Start-Sleep -Seconds 20

Write-Host "Checking Processed Bucket ($ProcessedBucket)..."
gsutil ls $ProcessedBucket

Write-Host "Fetching recent logs..."
gcloud functions logs read $FunctionName --project $ProjectID --region $Region --limit 20
