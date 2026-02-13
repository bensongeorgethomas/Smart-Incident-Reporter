# 🗣️ Voice of the People — Vision AI Module

> **A cloud-native, event-driven pipeline that uses AI to automate civic issue verification and triage.**

Citizens upload photos of civic issues (potholes, broken street lights, illegal dumping). Instead of manual review, the system **automatically classifies, moderates, and optimizes** every image using Google Cloud Vision AI — all triggered serverlessly the instant a file lands in Cloud Storage.

---

## 🧱 Architecture

```
                          ┌──────────────────────────────────┐
  📷 User Upload ────────►│   raw-reports-bucket  (GCS)      │
                          └────────────┬─────────────────────┘
                                       │  google.cloud.storage.
                                       │  object.v1.finalized
                                       ▼
                          ┌──────────────────────────────────┐
                          │  Cloud Function (Gen 2 / Python) │
                          │  ┌────────────────────────────┐  │
                          │  │ 1. Vision AI Label Detect   │  │
                          │  │ 2. Vision AI SafeSearch     │  │
                          │  │ 3. Pillow 300×300 Resize    │  │
                          │  └────────────────────────────┘  │
                          └────────────┬─────────────────────┘
                                       │
                                       ▼
                          ┌──────────────────────────────────┐
                          │ processed-thumbnails-bucket (GCS)│
                          │  └─ thumbnails/*_thumb.jpg       │
                          │     metadata: labels, safesearch │
                          └──────────────────────────────────┘
```

---

## 📂 Project Structure

```
vision/
├── main.tf                        # Terraform – all GCP resources
├── variables.tf                   # Configurable inputs
├── outputs.tf                     # Exported resource identifiers
├── terraform.tfvars.example       # Copy → terraform.tfvars
└── function_source/
    ├── main.py                    # Cloud Function entry-point
    └── requirements.txt           # Python dependencies
```

---

## ⚙️ What Gets Provisioned (Terraform)

| Resource | Purpose |
|----------|---------|
| **Vision API** | Label detection + SafeSearch moderation |
| **Cloud Functions API** | Gen 2 function runtime |
| **Cloud Build API** | Builds the function container |
| **Eventarc API** | GCS → Cloud Function event routing |
| **Cloud Run API** | Gen 2 functions run on Cloud Run |
| **`raw-reports-bucket`** | Receives citizen-uploaded images |
| **`processed-thumbnails-bucket`** | Stores 300×300 optimized thumbnails |
| **`gcf-source` bucket** | Holds the function source ZIP |
| **Service Account** | `vision-pipeline-sa` with `vision.aiUser`, `storage.objectAdmin`, `eventarc.eventReceiver` |
| **Cloud Function (Gen 2)** | `process-image` — triggered by object finalize |

---

## 🧠 What the Cloud Function Does

1. **Downloads** the uploaded image from the raw bucket.
2. **Vision AI – Label Detection** — identifies up to 10 objects (e.g. *pothole*, *asphalt*, *road surface*).
3. **Vision AI – SafeSearch** — flags inappropriate content (`adult`, `violence`, `racy`).
4. **Logs the top 3 labels** with confidence scores to Cloud Logging.
5. **Resizes** the image to exactly **300×300 px** using Pillow (LANCZOS interpolation).
6. **Uploads** the thumbnail to the processed bucket with all labels + SafeSearch results as GCS object metadata.

---

## 🚀 Deployment

### Prerequisites

- [Terraform ≥ 1.5](https://developer.hashicorp.com/terraform/downloads)
- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install)
- A GCP project with billing enabled

### Steps

```bash
# 1. Authenticate
gcloud auth application-default login

# 2. Configure your project
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars → set project_id = "your-gcp-project-id"

# 3. Deploy
terraform init
terraform plan
terraform apply

# 4. Test — upload a test image
gsutil cp test-image.jpg gs://YOUR_PROJECT_ID-raw-reports-bucket/

# 5. Verify — check function logs
gcloud functions logs read process-image --gen2 --region=us-central1
```

---

## 📊 Example Console Output

```
📷 Processing image: gs://my-project-raw-reports-bucket/pothole_main_st.jpg
   Downloaded 2,451,832 bytes
🏷️  Top 3 Vision AI Labels:
   1. Pothole                    (confidence: 94.12%)
   2. Asphalt                    (confidence: 89.67%)
   3. Road surface               (confidence: 85.33%)
🛡️  SafeSearch Results: {"adult": "VERY_UNLIKELY", "violence": "UNLIKELY", "racy": "VERY_UNLIKELY"}
✅ SafeSearch: Image pothole_main_st.jpg passed moderation checks.
📤 Thumbnail saved to gs://my-project-processed-thumbnails-bucket/thumbnails/pothole_main_st_thumb.jpg
🏁 Processing complete for pothole_main_st.jpg
```

---

## 🔐 IAM Roles

| Role | Why |
|------|-----|
| `roles/vision.aiUser` | Allows the function to call Vision API (label + SafeSearch) |
| `roles/storage.objectAdmin` | Read from raw bucket, write to processed bucket |
| `roles/eventarc.eventReceiver` | Required for GCS event triggers on Gen 2 functions |

---

## 📝 License

This project is part of the **Voice of the People** civic technology initiative.
