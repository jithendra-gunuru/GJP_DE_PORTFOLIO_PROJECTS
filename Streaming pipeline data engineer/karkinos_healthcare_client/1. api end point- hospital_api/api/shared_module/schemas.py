from pydantic import BaseModel, Field
from typing import Optional

class Patient(BaseModel):
    patient_id: int
    first_name: str
    last_name: str
    gender: str
    dob: str
    email: str
    mobile: str
    address: str
    city: str
    state: str
    country: str
    blood_group: str
    allergies: str
    chronic_conditions: str
    insurance_provider: str
    insurance_number: str
    marital_status: str
    is_active: bool
    record_status: str
    created_ts: str
    updated_ts: str
    created_by: str
    updated_by: str

# Example: patient = Patient(**data_dict)
