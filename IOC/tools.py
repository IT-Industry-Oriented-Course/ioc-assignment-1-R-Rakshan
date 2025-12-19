import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validate_call
import database
import utils

# --- Tool Definitions ---

@validate_call
def search_patient(name: str) -> List[Dict[str, Any]]:
    """
    Search for a patient by name.
    
    Args:
        name: The name or partial name of the patient to search for.
        
    Returns:
        A list of patient objects matching the search criteria.
    """
    print(f"[TOOL EXECUTION] search_patient(name='{name}')")
    utils.log_audit("TOOL_EXECUTION", {"tool": "search_patient", "args": {"name": name}})
    return database.db_search_patients(name)

@validate_call
def check_insurance_eligibility(patient_id: str) -> Dict[str, Any]:
    """
    Check the insurance eligibility status for a given patient.
    
    Args:
        patient_id: The unique identifier of the patient.
        
    Returns:
        An object containing insurance status and coverage details.
    """
    print(f"[TOOL EXECUTION] check_insurance_eligibility(patient_id='{patient_id}')")
    utils.log_audit("TOOL_EXECUTION", {"tool": "check_insurance_eligibility", "args": {"patient_id": patient_id}})
    patient = database.db_get_patient(patient_id)
    if not patient:
        return {"resourceType": "Coverage", "error": "Patient not found", "status": "unknown"}
    
    insurance_id = patient.get("insurance_id")
    if not insurance_id:
        return {"resourceType": "Coverage", "error": "No insurance on file", "status": "none"}
        
    policy = database.db_check_insurance(insurance_id)
    return {
        "resourceType": "Coverage",
        "patient": {"reference": f"Patient/{patient_id}"},
        "identifier": [{"system": "http://benefits.org/ids", "value": insurance_id}],
        "status": policy["status"].lower(),
        "type": {"text": policy["coverage"]},
        "eligible": policy["status"] == "Active"
    }

@validate_call
def find_available_slots(department: Optional[str] = None, doctor_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Find available appointment slots based on department or specific doctor.
    
    Args:
        department: The medical department (e.g., 'Cardiology', 'Dermatology').
        doctor_id: The specific doctor's ID (optional).
        
    Returns:
        A list of available time slots.
    """
    print(f"[TOOL EXECUTION] find_available_slots(department='{department}', doctor_id='{doctor_id}')")
    utils.log_audit("TOOL_EXECUTION", {"tool": "find_available_slots", "args": {"department": department, "doctor_id": doctor_id}})
    slots = database.db_find_slots(doctor_id=doctor_id, department=department)
    # Limit to 10 slots to prevent context overflow in LLM
    return slots[:10]

@validate_call
def book_appointment(patient_id: str, slot_id: str) -> Dict[str, Any]:
    """
    Book an appointment for a patient in a specific slot.
    
    Args:
        patient_id: The ID of the patient.
        slot_id: The ID of the slot to book.
        
    Returns:
        Confirmation object with appointment details or error message.
    """
    print(f"[TOOL EXECUTION] book_appointment(patient_id='{patient_id}', slot_id='{slot_id}')")
    utils.log_audit("TOOL_EXECUTION", {"tool": "book_appointment", "args": {"patient_id": patient_id, "slot_id": slot_id}})
    result = database.db_book_slot(slot_id, patient_id)
    if result:
        return {"resourceType": "Appointment", "status": "booked", "appointment": result}
    else:
        return {"resourceType": "OperationOutcome", "issue": [{"severity": "error", "code": "conflict", "diagnostics": "Slot not available or invalid"}]}

# --- Schema Definitions ---

# We manually define schemas to ensure strict compliance and better descriptions
# than what simple introspection might provide.

TOOL_SCHEMAS = [
    {
        "name": "search_patient",
        "description": "Search for a patient by name or partial name. Returns a list of matches.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name or partial name of the patient to search for."
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "check_insurance_eligibility",
        "description": "Check the insurance eligibility status for a given patient ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "The unique identifier of the patient (e.g., 'pat_001')."
                }
            },
            "required": ["patient_id"]
        }
    },
    {
        "name": "find_available_slots",
        "description": "Find available appointment slots based on department or specific doctor.",
        "parameters": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "description": "The medical department (e.g., 'Cardiology', 'Dermatology'). Optional if doctor_id is provided."
                },
                "doctor_id": {
                    "type": "string",
                    "description": "The specific doctor's ID. Optional if department is provided."
                }
            },
            "required": []
        }
    },
    {
        "name": "book_appointment",
        "description": "Book an appointment for a patient in a specific slot. This action commits the booking.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "The ID of the patient."
                },
                "slot_id": {
                    "type": "string",
                    "description": "The ID of the slot to book."
                }
            },
            "required": ["patient_id", "slot_id"]
        }
    }
]

def get_all_tool_schemas():
    """
    Returns the list of schemas for all tools.
    """
    return TOOL_SCHEMAS
