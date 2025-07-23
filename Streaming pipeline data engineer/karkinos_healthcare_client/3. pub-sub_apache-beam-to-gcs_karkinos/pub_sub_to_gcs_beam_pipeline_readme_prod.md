# 🚀 Pub/Sub to GCS – Apache Beam Dataflow Pipeline

> **Enterprise streaming pipeline step: Ingest messages from Google Pub/Sub and write partitioned, timestamped files to GCS for downstream analytics and batch processing.**

---

## 📌 Overview

This pipeline:

- **Consumes**: Pub/Sub subscription (`patient-events-sub`)
- **Processes**: Messages in streaming or batched mode
- **Stores**: Each event/message in partitioned Google Cloud Storage (GCS) folders
- **Organizes**: Files by event/processing time (year/month/day/hour[/minute])
- **Prepares for**: Downstream analytics (BigQuery, Dataproc, Spark)

---

## 📂 GCS Folder Structure & Naming Convention

**GCS Bucket:**\
`gs://karkinos-health-client/dataflow/raw/patients/output/`

**Partitioned path example:**

```
gs://karkinos-health-client/dataflow/raw/patients/output/2025/07/17/17/34/message-20250717-173401-e8bbe6.json
```

- **/2025/07/17/17/34/** → Year / Month / Day / Hour / Minute partition
- **message-20250717-173401-e8bbe6.json**
  - `20250717-173401`: Event time (UTC)
  - `e8bbe6`: Short random UUID to prevent file collisions
  - `.json`: Line-delimited JSON format

**Why?**

- Enables time-based partitioning for fast, scalable querying
- Simplifies downstream loading (BigQuery, Spark, retention jobs)
- Prevents filename collisions in parallel jobs

---

## ⚙️ Core Pipeline Files

- `pubsub_to_gcs.py` – Writes each message as an individual file partitioned by hour (`/YYYY/MM/DD/HH/`)
- `pubsub_to_gcs_batch.py` – Batches messages by minute and writes 1 file per window (`/YYYY/MM/DD/HH/mm/`)
- `requirements.txt` – All Python/GCP dependencies and environment setup

---

## 🏗️ How it Works (Pipeline Logic)

### **pubsub\_to\_gcs.py**

- Reads Pub/Sub messages in streaming mode
- Attaches GCS output path prefix using event or processing timestamp
- Writes each message to a unique JSON file in GCS

### **pubsub\_to\_gcs\_batch.py**

- Reads Pub/Sub messages, **groups by 1-minute window**
- Writes a single JSON file containing all messages for each window

**Both use Apache Beam I/O and GCP SDKs for resilient, cloud-scale data movement.**

---

## 🛠️ Setup & Quickstart

### 1. **Prepare GCS Bucket & Folders**

```bash
gsutil mb gs://karkinos-health-client

# Create example folders (Beam/Dataflow will auto-create as needed)
gsutil cp somefile.txt gs://karkinos-health-client/dataflow/raw/patients/output/test.txt
gsutil cp somefile.txt gs://karkinos-health-client/dataflow/staging/test.txt
gsutil cp somefile.txt gs://karkinos-health-client/dataflow/temp/test.txt
gsutil cp somefile.txt gs://karkinos-health-client/dataflow/templates/test.txt
```

### 2. **Install Python and All Requirements**

```bash
python -m venv env
source env/bin/activate  # Or activate Windows venv as needed

pip install --upgrade pip setuptools wheel
pip install "apache-beam[gcp]"
pip install google-cloud-storage
pip install google-cloud-pubsub
# (Optional) pip install google-cloud-bigquery
```

> See `requirements.txt` for troubleshooting dependency upgrades.

### 3. **Run Locally for Testing**

```bash
python pubsub_to_gcs.py \
  --project gcp-de-vaarahi-b38 \
  --region asia-south1 \
  --input_subscription projects/gcp-de-vaarahi-b38/subscriptions/patient-events-sub \
  --output_path gs://karkinos-health-client/dataflow/raw/patients/output \
  --staging_location gs://karkinos-health-client/dataflow/staging \
  --temp_location gs://karkinos-health-client/dataflow/temp \
  --runner DirectRunner \
  --streaming
```

### 4. **Deploy to Google Cloud Dataflow**

- Change `--runner DataflowRunner` (remove `DirectRunner`)
- Grant GCP Dataflow service account permissions on Pub/Sub and GCS
- Run from VM, Cloud Shell, or CI/CD

---

## 🔑 Security & Best Practices

- Use **least privilege IAM**: grant Dataflow access only to needed GCS buckets and Pub/Sub subscriptions
- All messages written as **line-delimited JSON** for safe downstream parsing
- All files named with timestamp + short UUID (no overwrites, easy traceability)
- **Partitioning by event time**: aligns with enterprise standards for data lakes

---

## 📝 requirements.txt

```
apache-beam[gcp]
google-cloud-storage
google-cloud-pubsub
# (optional for BigQuery): google-cloud-bigquery
```

> See `requirements.txt` for full troubleshooting and upgrade tips.

---

## 🧑‍💻 Example Message Path & File

**File:**

```
gs://karkinos-health-client/dataflow/raw/patients/output/2025/07/17/17/34/message-20250717-173401-e8bbe6.json
```

**Sample file content:**

```json
{"event_timestamp": "2025-07-17T17:34:01Z", "patient_id": 123, "event_type": "admit"}
```

(or newline-delimited JSON objects if batched)

---

## 💬 Interview & Ops Q&A

- **Q: Why do you partition files in GCS by time?**\
  A: Enables scalable, fast queries, makes retention/archival easy, and is required for Data Lake hygiene.

- **Q: Why use a short UUID in filenames?**\
  A: Prevents file overwrites and ensures unique output in parallel streams.

- **Q: How is this used downstream?**\
  A: Data is picked up by PySpark, Dataflow, or BigQuery jobs by partition, supporting hourly/minute batch ETL.

---

## ❓ FAQ & Troubleshooting

- **Pipeline errors?**

  - Check IAM on Dataflow service account (must access both Pub/Sub & GCS).
  - Check for dependency mismatches—use pip upgrades in requirements.txt.
  - Confirm subscription exists with `gcloud pubsub subscriptions list --project=gcp-de-vaarahi-b38`.

- **Empty or missing files?**

  - Ensure messages are publishing to the correct Pub/Sub topic.
  - Confirm pipeline is running in streaming mode for real-time data.

---

## 👤 Author & Contact

- **Maintainer:** Jithendra Gunuru
- **Email:** [jithendra.gunuru2016@gmail.com](mailto\:jithendra.gunuru2016@gmail.com)

---

**This README.md is ready for production, audit, and interview use.**\
**Copy it to your **``** component folder.**\
**Want an Airflow DAG example, monitoring, or diagram? Just ask!**

