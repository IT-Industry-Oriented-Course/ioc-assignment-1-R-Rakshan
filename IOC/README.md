# Clinical Workflow Agent POC

This is a Proof of Concept (POC) for a Function-Calling LLM Agent designed for clinical workflow automation.

## Features
- **Function Calling:** Orchestrates workflows by calling specific tools (Search Patient, Check Insurance, Find Slots, Book Appointment).
- **Safety:** strictly prohibits medical advice and diagnosis.
- **Validation:** Uses Pydantic for runtime validation of tool inputs.
- **Dry Run:** Supports a `--dry-run` mode to simulate actions without side effects.
- **Mock Database:** Includes a local in-memory database for testing.

## Prerequisites
- Python 3.8+
- A Hugging Face API Key (provided in the code as default for this POC)

### Installing Python (Windows)
If you do not have Python installed, you can install it easily using `winget` in PowerShell:

```powershell
winget install -e --id Python.Python.3.12
```

**Note:** After installation, you must **restart your terminal** (close and reopen VS Code/Trae) for the `python` and `pip` commands to be recognized.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 🖥️ Web UI (Streamlit)
For the best experience, run the web interface:

```bash
streamlit run app.py
```

### 💻 CLI Mode
Run the agent in interactive terminal mode:

```bash
python main.py
```

Run in **Dry Run** mode (no bookings committed):

```bash
python main.py --dry-run
```

## Example Scenarios

Try these inputs:
1. "Schedule a cardiology follow-up for patient Ravi Kumar next week and check insurance eligibility"
2. "Find available dermatology slots for Dr. James Wilson"
3. "Check insurance status for patient Ravi Kumar"

## Architecture
- `agent.py`: Core LLM logic using Hugging Face Inference API.
- `tools.py`: Clinical tools definitions and JSON schemas.
- `database.py`: Mock data store (Patients, Doctors, Slots, Insurance).
- `main.py`: CLI entry point.
