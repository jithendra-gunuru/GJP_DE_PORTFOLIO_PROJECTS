from flask import Flask, jsonify
import sys
import os
import random
from datetime import datetime, timedelta

# Import shared_module for logging and auth
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared_module'))
from utils import get_logger
from auth import require_api_key

app = Flask(__name__)
logger = get_logger("patients_api")

@app.route("/health", methods=["GET"])
@require_api_key
def health_check():
    logger.info("Health check endpoint called.")
    return jsonify({"status": "ok", "service": "patients_api"}), 200

def generate_patient(id):
    first_names = ["Ramu", "Sita", "John", "Priya", "Anil", "Kiran", "Deepa", "Rakesh", "Sunita", "Ravi"]
    last_names = ["Naidu", "Reddy", "Sharma", "Kumar", "Singh", "Patel", "Yadav", "Shetty", "Das", "Gupta"]
    genders = ["Male", "Female", "Other"]
    blood_groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
    marital_statuses = ["Single", "Married", "Divorced", "Widowed"]
    allergies = ["None", "Peanuts", "Gluten", "Lactose", "Dust", "Penicillin"]
    chronic_conditions = ["None", "Diabetes", "Hypertension", "Asthma", "Heart Disease"]
    cities = ["Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi", "Pune", "Kolkata", "Vizag", "Vijayawada", "Guntur"]
    states = ["Telangana", "Karnataka", "Tamil Nadu", "Maharashtra", "Delhi", "West Bengal", "Andhra Pradesh"]
    countries = ["India"]
    status_list = ["active", "inactive", "pending"]
    insurance_providers = ["Star Health", "Apollo Munich", "ICICI Lombard", "None"]

    dob = datetime(1970, 1, 1) + timedelta(days=random.randint(7000, 20000))
    created_ts = datetime.utcnow() - timedelta(days=random.randint(0, 100))
    updated_ts = created_ts + timedelta(days=random.randint(0, 10))

    city = random.choice(cities)
    state = random.choice(states)
    country = random.choice(countries)

    patient = {
        "patient_id": 1000 + id,
        "first_name": random.choice(first_names),
        "last_name": random.choice(last_names),
        "dob": dob.strftime("%Y-%m-%d"),
        "gender": random.choice(genders),
        "mobile": f"9{random.randint(100000000, 999999999)}",
        "email": f"user{id}@example.com",
        "address": f"{random.randint(1,100)}, {city}, {state}",
        "city": city,
        "state": state,
        "country": country,
        "pin_code": f"{random.randint(100000, 999999)}",
        "blood_group": random.choice(blood_groups),
        "marital_status": random.choice(marital_statuses),
        "emergency_contact_name": random.choice(first_names) + " " + random.choice(last_names),
        "emergency_contact_number": f"9{random.randint(100000000, 999999999)}",
        "allergies": random.choice(allergies),
        "chronic_conditions": random.choice(chronic_conditions),
        "insurance_provider": random.choice(insurance_providers),
        "insurance_number": f"INS{random.randint(100000,999999)}" if random.random() > 0.3 else "",
        "status": random.choice(status_list),
        "message": random.choice(["All good!", "Checkup needed", "Lab pending", "Critical", "Follow up"]),
        # --- Audit Columns (now 7 fields) ---
        "created_ts": created_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_ts": updated_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "created_by": "patients_api",
        "updated_by": "patients_api",
        "source_system": "patients_api",
        "is_active": True if random.choice(status_list) == "active" else False,
        "record_status": random.choice(["active", "inactive", "error"])
    }
    return patient

@app.route("/patients", methods=["GET"])
@require_api_key
def get_patients():
    patients = [generate_patient(i) for i in range(1, 11)]
    logger.info("Returning 10 dummy patients with business and audit columns")
    return jsonify({"patients": patients}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)


