import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "patient_visits_demo.json"
TEMPLATE_FILE = BASE_DIR / "templates" / "index.html"


@dataclass
class PatientVisit:
    patient_id: str
    patient_name: str
    age: int
    visit_date: str
    symptoms: list[str]
    medications: list[str]
    allergies: list[str]
    instructions: list[str]
    notes: str
    created_at: str


class DemoRepository:
    def __init__(self, data_file: Path) -> None:
        self.data_file = data_file
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self.data_file.write_text("[]", encoding="utf-8")

    def load_all(self) -> list[PatientVisit]:
        raw = json.loads(self.data_file.read_text(encoding="utf-8"))
        return [PatientVisit(**item) for item in raw]

    def save_all(self, visits: list[PatientVisit]) -> None:
        self.data_file.write_text(
            json.dumps([asdict(visit) for visit in visits], indent=2),
            encoding="utf-8",
        )

    def add_visit(self, payload: dict) -> PatientVisit:
        visits = self.load_all()
        visit = PatientVisit(
            patient_id=payload["patient_id"],
            patient_name=payload["patient_name"],
            age=int(payload["age"]),
            visit_date=payload["visit_date"],
            symptoms=payload.get("symptoms", []),
            medications=payload.get("medications", []),
            allergies=payload.get("allergies", []),
            instructions=payload.get("instructions", []),
            notes=payload.get("notes", ""),
            created_at=datetime.utcnow().isoformat(),
        )
        visits.append(visit)
        self.save_all(visits)
        return visit

    def get_history(self, patient_id: str) -> list[PatientVisit]:
        visits = [visit for visit in self.load_all() if visit.patient_id == patient_id]
        return sorted(visits, key=lambda item: item.visit_date)

    def list_patients(self) -> list[dict]:
        grouped: dict[str, list[PatientVisit]] = {}
        for visit in self.load_all():
            grouped.setdefault(visit.patient_id, []).append(visit)

        summaries = []
        for patient_id, visits in grouped.items():
            visits = sorted(visits, key=lambda item: item.visit_date)
            latest = visits[-1]
            summaries.append(
                {
                    "patient_id": patient_id,
                    "patient_name": latest.patient_name,
                    "total_visits": len(visits),
                    "last_visit_date": latest.visit_date,
                }
            )
        return sorted(summaries, key=lambda item: item["patient_id"])


def build_response(patient_id: str, question: str, history: list[PatientVisit]) -> dict:
    if not history:
        return {
            "patient_id": patient_id,
            "current_visit_summary": "No visit history found for this patient.",
            "changes_since_last_visit": [],
            "important_alerts": [],
            "suggested_follow_up_questions": ["Can you confirm the correct patient ID?"],
            "recalled_memories": [],
        }

    current = history[-1]
    previous = history[-2] if len(history) > 1 else None
    recalled_memories = [_visit_to_memory_text(item) for item in history[-5:]]

    changes = []
    if previous:
        new_symptoms = sorted(set(current.symptoms) - set(previous.symptoms))
        resolved_symptoms = sorted(set(previous.symptoms) - set(current.symptoms))
        new_medications = sorted(set(current.medications) - set(previous.medications))
        if new_symptoms:
            changes.append(f"New symptoms since the last visit: {', '.join(new_symptoms)}.")
        if resolved_symptoms:
            changes.append(f"Symptoms no longer listed: {', '.join(resolved_symptoms)}.")
        if new_medications:
            changes.append(f"New medications added since the last visit: {', '.join(new_medications)}.")
        if current.notes != previous.notes:
            changes.append("Clinical notes changed since the previous visit.")
    if not changes:
        changes.append("No major structured changes were detected between the last two visits.")

    alerts = []
    if current.allergies and not _contains_none(current.allergies):
        alerts.append(f"Medication safety check needed because allergies are recorded: {', '.join(current.allergies)}.")
    if previous and previous.instructions:
        alerts.append("Verify whether prior follow-up instructions were completed.")
    if "missed follow-up" in current.notes.lower():
        alerts.append("The notes mention a missed follow-up.")
    if len(current.symptoms) >= 3:
        alerts.append("Multiple active symptoms are recorded, so symptom progression should be clarified during the consultation.")

    risk_level = _risk_level(alerts)
    previous_context = (
        f"Previous recorded visit was on {previous.visit_date} with {_phrase(previous.symptoms)}."
        if previous
        else "This is the first recorded visit for this patient."
    )
    clinician_brief = (
        f"{current.patient_name} is returning for follow-up on {current.visit_date}. "
        f"Current issues include {_phrase(current.symptoms)}. "
        f"{previous_context} "
        f"Current medications are {_phrase(current.medications)} and allergies are {_phrase(current.allergies)}. "
        f"Main follow-up focus: assess progression, confirm adherence to prior instructions, and review any safety concerns."
    )
    next_steps = [
        "Confirm whether the patient followed the previous instructions and whether symptoms improved or worsened.",
        "Reconcile current medications with the recorded allergy history before suggesting any new plan.",
        "Capture updated symptom severity, duration, and any new red-flag developments in today's note.",
    ]
    visit_timeline = [
        {
            "visit_date": item.visit_date,
            "summary": f"{_phrase(item.symptoms)} | meds: {_phrase(item.medications)} | notes: {item.notes}",
        }
        for item in history
    ]

    return {
        "patient_id": patient_id,
        "patient_name": current.patient_name,
        "risk_level": risk_level,
        "clinician_brief": clinician_brief,
        "current_visit_summary": (
            f"Patient {current.patient_name}, age {current.age}, most recently visited on {current.visit_date} "
            f"with symptoms of {_phrase(current.symptoms)}. Current medications recorded: {_phrase(current.medications)}. "
            f"Known allergies: {_phrase(current.allergies)}. Instructions given: {_phrase(current.instructions)}."
        ),
        "changes_since_last_visit": changes,
        "important_alerts": alerts,
        "suggested_follow_up_questions": [
            "Have the symptoms improved, worsened, or stayed the same since the last visit?",
            "Were all prescribed medications taken as instructed, and did they help?",
            "Were any side effects, allergy concerns, or new symptoms noticed after the last visit?",
            f"Clinician question focus: {question}",
        ],
        "recommended_next_steps": next_steps,
        "visit_timeline": visit_timeline,
        "recalled_memories": recalled_memories,
    }


def seed_demo_data(repo: DemoRepository) -> list[PatientVisit]:
    visits = [
        PatientVisit(
            patient_id="P001",
            patient_name="Ravi Kumar",
            age=45,
            visit_date=str(date(2026, 4, 15)),
            symptoms=["fever", "cough"],
            medications=["paracetamol"],
            allergies=["penicillin"],
            instructions=["rest", "follow up in 3 days", "increase fluids"],
            notes="Mild throat redness.",
            created_at=datetime.utcnow().isoformat(),
        ),
        PatientVisit(
            patient_id="P001",
            patient_name="Ravi Kumar",
            age=45,
            visit_date=str(date(2026, 4, 18)),
            symptoms=["cough", "fatigue", "low appetite"],
            medications=["paracetamol", "cough syrup"],
            allergies=["penicillin"],
            instructions=["follow up again if symptoms worsen", "track temperature twice daily"],
            notes="Missed follow-up call yesterday. Cough feels worse at night.",
            created_at=datetime.utcnow().isoformat(),
        ),
        PatientVisit(
            patient_id="P002",
            patient_name="Anita Sharma",
            age=59,
            visit_date=str(date(2026, 4, 17)),
            symptoms=["dizziness"],
            medications=["amlodipine"],
            allergies=["none known"],
            instructions=["monitor blood pressure", "return with readings"],
            notes="First blood pressure follow-up.",
            created_at=datetime.utcnow().isoformat(),
        ),
    ]
    repo.save_all(visits)
    return visits


class CareMemoryHandler(BaseHTTPRequestHandler):
    repo = DemoRepository(DATA_FILE)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._html(TEMPLATE_FILE.read_text(encoding="utf-8"))
            return

        if path == "/health":
            self._json({"status": "ok", "memory_backend": "local-demo"})
            return

        if path == "/patients":
            self._json(self.repo.list_patients())
            return

        if path.startswith("/patients/") and path.endswith("/history"):
            patient_id = path.split("/")[2]
            history = [asdict(item) for item in self.repo.get_history(patient_id)]
            if not history:
                self._json({"detail": "Patient not found."}, status=HTTPStatus.NOT_FOUND)
                return
            self._json(history)
            return

        if path == "/seed-demo":
            self._json({"detail": "Use POST /seed-demo to create demo data."}, status=HTTPStatus.METHOD_NOT_ALLOWED)
            return

        self._json({"detail": "Not found."}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        payload = self._read_json()

        if path == "/patients/visit":
            visit = self.repo.add_visit(payload)
            self._json(asdict(visit), status=HTTPStatus.CREATED)
            return

        if path == "/agent/query":
            patient_id = payload["patient_id"]
            history = self.repo.get_history(patient_id)
            if not history:
                self._json({"detail": "Patient history not found."}, status=HTTPStatus.NOT_FOUND)
                return
            self._json(build_response(patient_id, payload["question"], history))
            return

        if path == "/seed-demo":
            seeded = seed_demo_data(self.repo)
            self._json({"seeded": len(seeded), "patients": self.repo.list_patients()})
            return

        self._json({"detail": "Not found."}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:
        return

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        return json.loads(body)

    def _json(self, payload: dict | list, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _html(self, payload: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def _visit_to_memory_text(visit: PatientVisit) -> str:
    return (
        f"Patient ID {visit.patient_id} named {visit.patient_name}, age {visit.age}, "
        f"visited on {visit.visit_date}. Symptoms: {_phrase(visit.symptoms)}. "
        f"Medications: {_phrase(visit.medications)}. Allergies: {_phrase(visit.allergies)}. "
        f"Instructions: {_phrase(visit.instructions)}. Notes: {visit.notes or 'No additional notes'}."
    )


def _phrase(values: list[str]) -> str:
    return ", ".join(values) if values else "none recorded"


def _contains_none(values: list[str]) -> bool:
    normalized = {value.strip().lower() for value in values}
    return "none" in normalized or "none known" in normalized or "no known allergies" in normalized


def _risk_level(alerts: list[str]) -> str:
    if len(alerts) >= 3:
        return "high attention"
    if len(alerts) == 2:
        return "moderate attention"
    return "routine follow-up"


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), CareMemoryHandler)
    print(f"CareMemory demo server running at http://{host}:{port}")
    server.serve_forever()
