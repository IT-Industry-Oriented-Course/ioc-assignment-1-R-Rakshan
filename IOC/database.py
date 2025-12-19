from typing import List, Dict, Optional
from datetime import datetime, timedelta

# --- Mock Data Stores ---

PATIENTS = [
    {
        "resourceType": "Patient",
        "id": "pat_001",
        "name": [
            {
                "use": "official",
                "family": "Kumar",
                "given": ["Ravi"]
            }
        ],
        "dob": "1985-06-15",
        "gender": "male",
        "telecom": [
            {
                "system": "phone",
                "value": "555-0101",
                "use": "mobile"
            }
        ],
        "insurance_id": "ins_12345",
        "clinical_notes": [
            {"date": "2023-12-01", "author": "Dr. Sarah Smith", "note": "Patient reports mild chest pain. Recommended EKG."},
            {"date": "2024-01-15", "author": "Dr. James Wilson", "note": "Routine checkup. BP 120/80. No concerns."}
        ],
        "past_appointments": [
            {"date": "2023-12-01", "department": "Cardiology", "status": "Completed"},
            {"date": "2024-01-15", "department": "General Practice", "status": "Completed"}
        ]
    },
    {
        "resourceType": "Patient",
        "id": "pat_002",
        "name": [
            {
                "use": "official",
                "family": "Chen",
                "given": ["Linda"]
            }
        ],
        "dob": "1990-11-20",
        "gender": "female",
        "telecom": [
            {
                "system": "phone",
                "value": "555-0102",
                "use": "mobile"
            }
        ],
        "insurance_id": "ins_67890",
        "clinical_notes": [
            {"date": "2024-02-10", "author": "Dr. James Wilson", "note": "Patient presented with skin rash. Prescribed topical cream."}
        ],
        "past_appointments": [
            {"date": "2024-02-10", "department": "Dermatology", "status": "Completed"}
        ]
    },
    {
        "resourceType": "Patient",
        "id": "pat_003",
        "name": [
            {
                "use": "official",
                "family": "Rodriguez",
                "given": ["Maria"]
            }
        ],
        "dob": "1978-03-12",
        "gender": "female",
        "telecom": [
            {
                "system": "phone",
                "value": "555-0103",
                "use": "mobile"
            }
        ],
        "insurance_id": "ins_12345",
        "clinical_notes": [
            {"date": "2024-01-05", "author": "Dr. Sarah Smith", "note": "Annual physical. Cholesterol slightly elevated. Diet changes recommended."},
            {"date": "2024-03-12", "author": "Dr. Sarah Smith", "note": "Follow-up on cholesterol. Levels improved."}
        ],
        "past_appointments": [
            {"date": "2024-01-05", "department": "Cardiology", "status": "Completed"},
            {"date": "2024-03-12", "department": "Cardiology", "status": "Completed"}
        ]
    },
    {
        "resourceType": "Patient",
        "id": "pat_004",
        "name": [
            {
                "use": "official",
                "family": "Johnson",
                "given": ["Robert", "Bob"]
            }
        ],
        "dob": "1955-08-30",
        "gender": "male",
        "telecom": [
            {
                "system": "phone",
                "value": "555-0104",
                "use": "home"
            }
        ],
        "insurance_id": "ins_99999",
        "clinical_notes": [
            {"date": "2023-11-15", "author": "Dr. James Wilson", "note": "Chronic back pain flare-up. Referred to PT."}
        ],
        "past_appointments": [
            {"date": "2023-11-15", "department": "General Practice", "status": "Completed"}
        ]
    },
    {
        "resourceType": "Patient",
        "id": "pat_005",
        "name": [
            {
                "use": "official",
                "family": "Okazaki",
                "given": ["Kenji"]
            }
        ],
        "dob": "2010-05-05",
        "gender": "male",
        "telecom": [
            {
                "system": "email",
                "value": "kenji.parent@example.com",
                "use": "home"
            }
        ],
        "insurance_id": "ins_12345",
        "clinical_notes": [],
        "past_appointments": []
    }
]

DOCTORS = [
    {
        "resourceType": "Practitioner",
        "id": "doc_001",
        "name": [
            {
                "use": "official",
                "family": "Smith",
                "given": ["Sarah"],
                "prefix": ["Dr"]
            }
        ],
        "department": "Cardiology",
        "specialty": ["Interventional Cardiology"]
    },
    {
        "resourceType": "Practitioner",
        "id": "doc_002",
        "name": [
            {
                "use": "official",
                "family": "Wilson",
                "given": ["James"],
                "prefix": ["Dr"]
            }
        ],
        "department": "Dermatology",
        "specialty": ["General Dermatology"]
    }
]

# Generate some slots for the next 7 days
SLOTS = []
base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
for day in range(1, 8):  # Next 7 days
    current_day = base_date + timedelta(days=day)
    # 9 AM, 10 AM, 2 PM
    for hour in [9, 10, 14]:
        slot_time = current_day.replace(hour=hour)
        SLOTS.append({
            "id": f"slot_{day}_{hour}_doc_001",
            "doctor_id": "doc_001",
            "start_time": slot_time.isoformat(),
            "duration_minutes": 30,
            "is_booked": False
        })
        SLOTS.append({
            "id": f"slot_{day}_{hour}_doc_002",
            "doctor_id": "doc_002",
            "start_time": slot_time.isoformat(),
            "duration_minutes": 30,
            "is_booked": False
        })

APPOINTMENTS = []

INSURANCE_POLICIES = {
    "ins_12345": {"status": "Active", "coverage": "Comprehensive", "provider": "BlueCross"},
    "ins_67890": {"status": "Expired", "coverage": "Basic", "provider": "Aetna"}
}

# --- Helper Functions for DB Access ---

def db_search_patients(name_query: str) -> List[Dict]:
    results = []
    query = name_query.lower()
    for p in PATIENTS:
        # Check given name or family name
        given = p["name"][0]["given"][0].lower()
        family = p["name"][0]["family"].lower()
        full_name = f"{given} {family}"
        
        if query in given or query in family or query in full_name:
            results.append(p)
    return results

def db_get_patient(patient_id: str) -> Optional[Dict]:
    for p in PATIENTS:
        if p["id"] == patient_id:
            return p
    return None

def db_check_insurance(insurance_id: str) -> Dict:
    return INSURANCE_POLICIES.get(insurance_id, {"status": "Unknown", "coverage": "None"})

def db_find_slots(doctor_id: Optional[str] = None, department: Optional[str] = None) -> List[Dict]:
    results = []
    
    # Filter doctors first if department is provided
    target_doctor_ids = set()
    if department:
        for doc in DOCTORS:
            if doc["department"].lower() == department.lower():
                target_doctor_ids.add(doc["id"])
    
    for slot in SLOTS:
        if slot["is_booked"]:
            continue
            
        if doctor_id and slot["doctor_id"] != doctor_id:
            continue
            
        if department and slot["doctor_id"] not in target_doctor_ids:
            continue
            
        results.append(slot)
    return results

def db_book_slot(slot_id: str, patient_id: str) -> Optional[Dict]:
    for slot in SLOTS:
        if slot["id"] == slot_id:
            if slot["is_booked"]:
                return None # Already booked
            
            slot["is_booked"] = True
            appointment = {
                "id": f"appt_{len(APPOINTMENTS) + 1}",
                "patient_id": patient_id,
                "slot_id": slot_id,
                "doctor_id": slot["doctor_id"],
                "time": slot["start_time"],
                "status": "Confirmed"
            }
            APPOINTMENTS.append(appointment)
            return appointment
    return None # Slot not found
