from flask import Flask, jsonify
import sys
import os
import random
from datetime import datetime, timedelta

# Import shared_module for logging and API auth
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared_module'))
from utils import get_logger
from auth import require_api_key

app = Flask(__name__)
logger = get_logger("appointments_api")

@app.route("/health", methods=["GET"])
@require_api_key
def health_check():
    logger.info("Health check endpoint called.")
    return jsonify({"status": "ok", "service": "appointments_api"}), 200

def generate_appointment(id):
    appointment_types = ["Consultation", "Follow-up", "Lab Test", "Procedure", "Vaccination", "Emergency"]
    departments = ["Cardiology", "Neurology", "Oncology", "Orthopedics", "Dermatology", "General"]
    doctors = ["Dr. Reddy", "Dr. Sharma", "Dr. Gupta", "Dr. Singh", "Dr. Patel", "Dr. Das"]
    statuses = ["scheduled", "completed", "cancelled", "no-show", "in-progress"]
    payment_modes = ["Cash", "Card", "Insurance", "UPI"]
    reasons = [
        "Routine Checkup", "Chest Pain", "Fever", "Injury", "Test Results", "Vaccination", "Follow-up Visit"
    ]
    visit_types = ["In-person", "Telemedicine"]
    priority_levels = ["High", "Medium", "Low"]

    patient_id = 1000 + id
    doctor_name = random.choice(doctors)
    scheduled_date = datetime.utcnow() - timedelta(days=random.randint(0, 60))
    actual_date = scheduled_date + timedelta(hours=random.randint(0, 72))
    created_ts = scheduled_date - timedelta(days=random.randint(0, 10))
    updated_ts = actual_date + timedelta(days=random.randint(0, 3))

    appointment = {
        "appointment_id": 2000 + id,
        "patient_id": patient_id,
        "appointment_type": random.choice(appointment_types),
        "department": random.choice(departments),
        "doctor_name": doctor_name,
        "scheduled_date": scheduled_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actual_date": actual_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "visit_type": random.choice(visit_types),
        "priority": random.choice(priority_levels),
        "reason": random.choice(reasons),
        "status": random.choice(statuses),
        "consultation_fee": round(random.uniform(200, 2000), 2),
        "payment_mode": random.choice(payment_modes),
        "paid_amount": round(random.uniform(0, 2000), 2),
        "insurance_claimed": random.choice([True, False]),
        "remarks": random.choice(["N/A", "Patient late", "Urgent", "Cancelled by doctor", "All went well"]),
        # --- Audit Columns (7) ---
        "created_ts": created_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_ts": updated_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "created_by": "appointments_api",
        "updated_by": "appointments_api",
        "source_system": "appointments_api",
        "is_active": True if random.choice(statuses) in ["scheduled", "in-progress", "completed"] else False,
        "record_status": random.choice(["active", "inactive", "error"])
    }
    return appointment

@app.route("/appointments", methods=["GET"])
@require_api_key
def get_appointments():
    appointments = [generate_appointment(i) for i in range(1, 11)]  # 10 records
    logger.info("Returning 10 dummy appointments with business and audit columns")
    return jsonify({"appointments": appointments}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)

