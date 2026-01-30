"""
Zently API - Vercel Serverless Function
"""
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
from datetime import datetime
import os

# Pour Vercel, on utilise /tmp pour le stockage
DATA_FILE = Path("/tmp/journal.json")

def load_journal():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Charger depuis le fichier initial si existe
    initial_file = Path(__file__).parent.parent / "data" / "journal.json"
    if initial_file.exists():
        with open(initial_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            save_journal(data)
            return data
    return {
        "project": {"name": "", "description": "", "created_at": None, "onboarding_complete": False},
        "tasks": [],
        "events": [],
        "sessions": []
    }

def save_journal(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        journal = load_journal()

        # Calculer les stats
        tasks = journal.get("tasks", [])
        total = len(tasks)
        completed = sum(1 for t in tasks if t["status"] == "Terminé")
        in_progress = sum(1 for t in tasks if t["status"] == "En cours")
        percentage = round((completed / total) * 100, 1) if total > 0 else 0

        response = {
            "project": journal["project"],
            "stats": {
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "percentage": percentage
            },
            "tasks": tasks,
            "sessions": journal.get("sessions", []),
            "recent_events": journal.get("events", [])[-10:]
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))

        journal = load_journal()
        action = post_data.get("action")

        if action == "update_task":
            task_id = post_data.get("task_id")
            new_status = post_data.get("status")
            for task in journal["tasks"]:
                if task["id"] == task_id:
                    task["status"] = new_status
                    task["updated_at"] = datetime.now().isoformat()
                    journal["events"].append({
                        "timestamp": datetime.now().isoformat(),
                        "type": "status_change",
                        "message": f"Tâche #{task_id}: → {new_status}"
                    })
                    break

        elif action == "add_note":
            task_id = post_data.get("task_id")
            note = post_data.get("note")
            for task in journal["tasks"]:
                if task["id"] == task_id:
                    task.setdefault("notes", []).append({
                        "timestamp": datetime.now().isoformat(),
                        "content": note
                    })
                    break

        elif action == "start_session":
            session = {
                "id": len(journal["sessions"]) + 1,
                "started_at": datetime.now().isoformat(),
                "ended_at": None,
                "report": None
            }
            journal["sessions"].append(session)
            journal["events"].append({
                "timestamp": datetime.now().isoformat(),
                "type": "session_start",
                "message": f"Session #{session['id']} démarrée"
            })

        elif action == "end_session":
            report = post_data.get("report", "")
            for session in journal["sessions"]:
                if not session.get("ended_at"):
                    session["ended_at"] = datetime.now().isoformat()
                    session["report"] = report
                    journal["events"].append({
                        "timestamp": datetime.now().isoformat(),
                        "type": "session_end",
                        "message": f"Session #{session['id']} terminée"
                    })
                    break

        save_journal(journal)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": True}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
