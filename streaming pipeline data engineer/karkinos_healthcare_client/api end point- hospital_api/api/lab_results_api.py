from flask import Flask, jsonify
import sys
import os
import random
from datetime import datetime, timedelta

# Import shared_module for logging and API auth
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared_module'))
from utils import get_logger
from auth import require_api_key  # <-- Use the shared decorator

app = Flask(__name__)
logger = get_logger("lab_results_api")

@app.route("/health", methods=["GET"])
@require_api_key
def health_check():
    logger.info("Health check endpoint called.")
    return jsonify({"status": "ok", "service": "lab_results_api"}), 200

def generate_lab_result(id):
    test_names = [
        "CBC", "Blood Sugar", "Lipid Profile", "Liver Function", "Kidney Function",
        "Thyroid Panel", "ECG", "Urine Routine", "Vitamin D", "COVID RT-PCR"
    ]
    result_statuses = ["normal", "abnormal", "critical", "pending"]
    units = ["mg/dL", "g/dL", "IU/L", "U/L", "pg/mL", "cells/cumm", "bpm"]
    sample_types = ["Blood", "Urine", "Saliva", "Swab"]
    collection_sites = ["Right Arm", "Left Arm", "Oral", "Nasal"]
    labs = ["Apollo Lab", "SRL Diagnostics", "Thyrocare", "Max Lab", "Metropolis"]
    reference_ranges = [
        "4.5-11 x10^3/uL", "70-110 mg/dL", "135-145 mmol/L", "0.8-1.2 mg/dL",
        "140-400 x10^3/uL", "0.5-5.0 uIU/mL", "120-160 g/L"
    ]

    # Each result is linked to a patient and appointment
    patient_id = 1000 + id
    appointment_id = 2000 + id
    test_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
    report_date = test_date + timedelta(days=random.randint(0, 2))
    created_ts = test_date - timedelta(days=random.randint(0, 5))
    updated_ts = report_date + timedelta(days=random.randint(0, 3))

    lab_result = {
        "lab_result_id": 3000 + id,
        "patient_id": patient_id,
        "appointment_id": appointment_id,
        "test_name": random.choice(test_names),
        "result_value": round(random.uniform(0.5, 18.0), 2),
        "unit": random.choice(units),
        "reference_range": random.choice(reference_ranges),
        "result_status": random.choice(result_statuses),
        "sample_type": random.choice(sample_types),
        "collection_site": random.choice(collection_sites),
        "lab_name": random.choice(labs),
        "collected_by": random.choice(["Technician A", "Technician B", "Technician C"]),
        "verified_by": random.choice(["Dr. Reddy", "Dr. Sharma", "Dr. Gupta"]),
        "test_date": test_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "report_date": report_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "report_file_url": f"https://hospital.com/labresults/report_{3000 + id}.pdf",
        "remarks": random.choice([
            "Within normal range", "Abnormal, follow-up required", "Critical value", "Pending review"
        ]),
        # --- Audit Columns (7) ---
        "created_ts": created_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_ts": updated_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "created_by": "lab_results_api",
        "updated_by": "lab_results_api",
        "source_system": "lab_results_api",
        "is_active": True if random.choice(result_statuses) == "normal" else False,
        "record_status": random.choice(["active", "inactive", "error"])
    }
    return lab_result

@app.route("/lab_results", methods=["GET"])
@require_api_key
def get_lab_results():
    lab_results = [generate_lab_result(i) for i in range(1, 11)]  # 10 records
    logger.info("Returning 10 dummy lab results with business and audit columns")
    return jsonify({"lab_results": lab_results}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)

