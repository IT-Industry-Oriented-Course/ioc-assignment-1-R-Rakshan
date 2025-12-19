import datetime
import json
import os

AUDIT_FILE = "audit.log"

def log_audit(action_type: str, details: dict, user: str = "system"):
    """
    Logs an action to the audit file for compliance.
    
    Args:
        action_type: The type of action (e.g., "TOOL_EXECUTION", "AGENT_DECISION").
        details: A dictionary containing details of the action.
        user: The user performing the action (default: "system").
    """
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user": user,
        "action_type": action_type,
        "details": details
    }
    
    # Append to log file
    with open(AUDIT_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
        
    return entry
