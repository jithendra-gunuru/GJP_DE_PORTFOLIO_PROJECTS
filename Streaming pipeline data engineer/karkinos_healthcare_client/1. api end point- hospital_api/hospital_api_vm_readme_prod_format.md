# 🚀 Hospital API VM Setup & Usage Guide

> **Enterprise Guide for Secure Flask API Deployment, API Key Management, and GCP Integration**

---

## 1. GCP Firewall & Network

Create a firewall rule to allow required ports:

- **TCP 22** (SSH)
- **TCP 5001** (Patients API)
- **TCP 5002** (Appointments API)
- **TCP 5003** (Lab Results API)

```bash
gcloud compute firewall-rules create hospital-api-ingress \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:22,tcp:5001,tcp:5002,tcp:5003 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=hospital-api-vm \
  --description="Allow SSH and API access for hospital APIs"
```

> **Best Practice:** In production, restrict `--source-ranges` to your office/public IPs only.

---

## 2. Service Account & IAM Roles

**Create a dedicated service account:**

```bash
gcloud iam service-accounts create hospital-api-vm-sa \
  --description="Service Account for API VM" \
  --display-name="Hospital API VM Service Account"
```

**Grant permissions:**

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:hospital-api-vm-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:hospital-api-vm-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"
```

- Add `roles/pubsub.publisher` if your API/producer writes to Pub/Sub.

---

## 3. VM Creation

```bash
gcloud compute instances create hospital-api-vm \
  --zone=YOUR_ZONE \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --tags=hospital-api-vm \
  --service-account=hospital-api-vm-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform
```

---

## 4. VM Bootstrapping (Python & Venv Setup)

**Install Python 3.11.9 & Virtual Environment:**

```bash
sudo apt update
sudo apt install -y wget build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev curl libbz2-dev

cd /tmp
wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xf Python-3.11.9.tgz
cd Python-3.11.9
./configure --enable-optimizations
make -j $(nproc)
sudo make altinstall

python3.11 --version  # Should output Python 3.11.9

cd <your-repo>
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> **Tip:** Use virtual environments for project-specific dependencies.

---

## 5. requirements.txt (Sample)

Keep this in your repo root:

```
flask
gunicorn
google-cloud-secret-manager
google-cloud-logging
google-cloud-pubsub
requests
python-json-logger
pydantic
typing-extensions
```

---

## 6. API Key Management with Google Secret Manager (GSM)

**Generate strong random API keys:**

```bash
openssl rand -hex 32 > patients_api_key.txt
openssl rand -hex 32 > appointments_api_key.txt
openssl rand -hex 32 > lab_results_api_key.txt
```

> *Never commit these files. Use only for uploading keys to GSM.*

**Create & upload secrets:**

```bash
gcloud secrets create patients_api_key --replication-policy="automatic"
gcloud secrets versions add patients_api_key --data-file=patients_api_key.txt

# Repeat for appointments_api_key and lab_results_api_key
```

> Delete `.txt` files after uploading to GSM.

---

## 7. Running Flask APIs with Gunicorn

**Stop old Gunicorn processes:**

```bash
pkill gunicorn
```

**Export API Key Secret IDs:**

```bash
export PATIENTS_API_KEY_SECRET_ID="projects/<PROJECT_ID>/secrets/patients_api_key/versions/latest"
export APPOINTMENTS_API_KEY_SECRET_ID="projects/<PROJECT_ID>/secrets/appointments_api_key/versions/latest"
export LAB_RESULTS_API_KEY_SECRET_ID="projects/<PROJECT_ID>/secrets/lab_results_api_key/versions/latest"
```

**Start each API in the background:**

```bash
# Patients API (port 5001)
gunicorn -w 2 -b 0.0.0.0:5001 patients_api:app &

# Appointments API (port 5002)
gunicorn -w 2 -b 0.0.0.0:5002 appointments_api:app &

# Lab Results API (port 5003)
gunicorn -w 2 -b 0.0.0.0:5003 lab_results_api:app &
```

**Python Example (for GSM key fetch):**

```python
import os
from google.cloud import secretmanager

def get_api_key_from_gsm(env_var):
    secret_id = os.environ[env_var]
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": secret_id})
    return response.payload.data.decode('UTF-8')
```

---

## 8. Testing with cURL

- **Patients:**\
  `curl -H "x-api-key: <YOUR_PATIENTS_API_KEY>" http://<EXTERNAL_IP>:5001/patients`
- **Appointments:**\
  `curl -H "x-api-key: <YOUR_APPOINTMENTS_API_KEY>" http://<EXTERNAL_IP>:5002/appointments`
- **Lab Results:**\
  `curl -H "x-api-key: <YOUR_LAB_RESULTS_API_KEY>" http://<EXTERNAL_IP>:5003/lab_results`
- **Health Check:**\
  `curl -H "x-api-key: <YOUR_API_KEY>" http://<EXTERNAL_IP>:5001/health`

---

## 9. Security & Production Tips

- Restrict firewall to trusted IPs.
- Use HTTPS/reverse proxy (Nginx/Apache).
- Run APIs as systemd services for auto-restart.
- Rotate API keys in GSM as needed.
- **Never** store API keys in code or env files.
- Use GCP IAM & GSM for all secrets.

---

## 10. API Directory Structure Example

```
hospital-streaming-pipeline/
├── README.md
├── api/
│   ├── patients_api.py
│   ├── appointments_api.py
│   ├── lab_results_api.py
│   └── shared_module/
│       ├── auth.py
│       ├── logger.py
│       ├── schemas.py
│       └── utils.py
├── config/
│   ├── dev_config.yaml
│   └── example.env
├── requirements.txt
```

---

## 11. FAQ / Troubleshooting

- **API not reachable?** Check firewall, Gunicorn, and port.
- **Permission denied for GSM?** Check service account roles.
- **Logs?** Use Cloud Logging or check Gunicorn/stdout.
- **Rotate API key?** Upload new secret version in GSM, restart Gunicorn.

---

## 12. Producer VM, Pub/Sub & Data Flow (Enterprise Pattern)

> Typical: Client → Hospital API VM → Producer VM → Pub/Sub → Dataflow/BigQuery

**Producer VM:**

- Needs `roles/pubsub.publisher` on the topic.
- Fetches API data using API key.
- Publishes to Pub/Sub.

---

## 13. Key Management Patterns

- **Single Secret:** One API key for all endpoints.
- **Per-API Secret (Best):** Unique key/secret per endpoint, for fine-grained security.

---

## 14. Service Account JSON – Not for API Clients!

- Use API keys for client endpoints, never SA JSON.
- SA JSON is for internal, server-to-server GCP authentication.

---

## 15. Gunicorn: Foreground, Daemon & Production

- Foreground: Dev only.
- Daemon: Safer for background.
- **Production:** Use systemd or supervisor for process management.

**Sample systemd Unit:**

```ini
[Unit]
Description=Patients API Gunicorn Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/path/to/api
ExecStart=/path/to/venv/bin/gunicorn -w 2 -b 0.0.0.0:5001 patients_api:app

[Install]
WantedBy=multi-user.target
```

---

## 16. Audit Columns for Compliance

| Column      | Type      | Description                       |
| ----------- | --------- | --------------------------------- |
| created\_ts | TIMESTAMP | When record was created           |
| updated\_ts | TIMESTAMP | When last updated                 |
| created\_by | STRING    | Creator/service                   |
| updated\_by | STRING    | Last updater                      |
| is\_active  | BOOLEAN   | Soft delete/logical active status |

---

## 17. Advanced Testing & Troubleshooting

- Check Gunicorn: `sudo netstat -tulnp | grep gunicorn`
- Logs: `journalctl -u <service-name>`
- Curl with debug: `curl -v ...`
- If API down: Check firewall, Gunicorn, service account, GSM.

---

## 18. Containerization, CI/CD & Cloud Readiness

- Use Docker for packaging, CI/CD for deployment.
- Pass secrets/configs via env vars or GSM.
- Cloud Run/K8s: Containerize your Gunicorn/Flask app for modern cloud.

---

## 19. Interview & Documentation Keywords

> *Enterprise API Security, Google Secret Manager (GSM), WSGI Hosting (Gunicorn), GCP IAM, Pub/Sub Producer, Audit Columns, Data Compliance, CI/CD, Containerization, systemd, Health Data Pipeline*

---

## 20. Authors & Support

- **Lead:** Jithendra Gunuru
- **Email:** [jithendra.gunuru2016@gmail.com](mailto\:jithendra.gunuru2016@gmail.com)

---

**This guide is production-proven. Copy it into your README.md for world-class onboarding, audit, and compliance.**

---

