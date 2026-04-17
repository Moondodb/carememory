# CareMemory

CareMemory is a medical follow-up agent designed for the Hindsight + CascadeFlow hackathon. It helps clinicians prepare for a patient consultation by remembering previous visits, symptoms, medications, allergies, instructions, and missed follow-ups.

Instead of starting every interaction from zero, the agent builds continuity across visits and produces a structured clinician-ready summary with alerts, changes since the last visit, and recommended next steps.

## Problem

In real clinics, follow-up visits are slower and riskier when important context is scattered across previous notes or forgotten entirely. Patients often repeat the same story, missed follow-ups go unnoticed, and medication or allergy context can be missed during a rushed consultation.

CareMemory addresses that by turning prior patient interactions into reusable memory for the next visit.

## Solution

CareMemory is a patient follow-up and clinical memory assistant that:

- stores patient visit details
- tracks symptom progression across visits
- highlights allergy and medication context
- surfaces missed follow-ups and unresolved issues
- generates a concise pre-consultation summary for clinicians

## Why Memory Matters

This project is intentionally built around persistent memory.

Without memory:
- the agent gives a generic response based only on the latest visit

With memory:
- the agent recalls prior symptoms
- notices what changed since the last consultation
- remembers allergies and earlier instructions
- highlights missed follow-ups and continuity risks

That before-and-after difference is the core of the demo.

## Features

- Interactive single-page UI for demo flow
- Patient roster with visit counts
- Visit timeline for each patient
- Consultation summary card
- Risk badge based on follow-up concerns
- Changes since last visit
- Important alerts
- Recommended next steps
- Raw API output for debugging/demo transparency
- FastAPI scaffold for full backend integration
- Zero-install Python demo server for easy local execution

## Tech Stack

- Python
- HTML, CSS, JavaScript
- Standard library HTTP server for the demo runtime
- FastAPI scaffold for the production-style backend
- Hindsight client integration scaffold for persistent memory

## Project Structure

```text
medical-memory-agent/
  app/
    __init__.py
    config.py
    llm.py
    main.py
    memory.py
    models.py
    repository.py
  data/
    patient_visits_demo.json
  templates/
    index.html
  demo_server.py
  requirements.txt
  .env.example
  .gitignore
  README.md
```

## Run Locally

### Option 1: Zero-install demo server

This works with the bundled Python runtime and does not require package installation.

```powershell
cd C:\Users\Krishna\Documents\Codex\2026-04-18-files-mentioned-by-the-user-hindsight\medical-memory-agent
& 'C:\Users\Krishna\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' demo_server.py
```

Then open:

[http://127.0.0.1:8000](http://127.0.0.1:8000)

### Option 2: FastAPI version

If package installation is available in your environment:

```powershell
cd C:\Users\Krishna\Documents\Codex\2026-04-18-files-mentioned-by-the-user-hindsight\medical-memory-agent
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

## Demo Flow

1. Start the app
2. Click `Load Demo Patients`
3. Select patient `P001`
4. Show the visit timeline
5. Click `Generate Summary`
6. Walk through:
   - clinician brief
   - risk badge
   - changes since last visit
   - important alerts
   - recommended next steps
   - recalled memories

## API Endpoints

- `GET /health`
- `GET /patients`
- `GET /patients/{patient_id}/history`
- `POST /patients/visit`
- `POST /agent/query`
- `POST /seed-demo`

## Hindsight Integration

The repository includes a FastAPI backend scaffold with a Hindsight memory service in:

- `app/main.py`
- `app/memory.py`

The intended production flow is:

1. retain each patient visit into Hindsight
2. recall relevant patient memories during follow-up
3. generate a stronger summary using remembered history

Official references:

- [Hindsight Quick Start](https://hindsight.vectorize.io/developer/api/quickstart)
- [Hindsight GitHub](https://github.com/vectorize-io/hindsight)

## Submission Angle

CareMemory is not a diagnostic AI doctor. It is a clinician support tool focused on continuity of care during follow-up visits. That makes it safer, more realistic, and better aligned with the hackathon requirement that memory should be central to the product value.

## Future Improvements

- Connect the live app to Hindsight for true persistent memory
- Add LLM-generated SOAP or clinician note output
- Add patient severity trend charts
- Add doctor dashboard filtering by risk level
- Add synthetic multi-patient datasets for richer demos
