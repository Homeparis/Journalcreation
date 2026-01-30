#!/usr/bin/env python3
"""
Zently Event Logger - Journal de bord pour la création du site Zently
Accessible via Claude Code avec logging horodaté et génération de résumés IA.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum

# Chemins des fichiers
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
JOURNAL_FILE = DATA_DIR / "journal.json"
SESSIONS_DIR = DATA_DIR / "sessions"

class TaskStatus(Enum):
    NOT_STARTED = "Non commencé"
    IN_PROGRESS = "En cours"
    COMPLETED = "Terminé"

def init_journal() -> dict:
    """Initialise ou charge le journal."""
    if JOURNAL_FILE.exists():
        with open(JOURNAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "project": {
            "name": "",
            "description": "",
            "created_at": None,
            "onboarding_complete": False
        },
        "tasks": [],
        "events": [],
        "sessions": []
    }

def save_journal(data: dict) -> None:
    """Sauvegarde le journal."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def log_event(message: str, event_type: str = "info") -> dict:
    """Enregistre un événement horodaté."""
    journal = init_journal()
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "message": message
    }
    journal["events"].append(event)
    save_journal(journal)
    return event

def setup_project(name: str, description: str) -> dict:
    """Configure le projet lors de l'onboarding."""
    journal = init_journal()
    journal["project"]["name"] = name
    journal["project"]["description"] = description
    journal["project"]["created_at"] = datetime.now().isoformat()
    save_journal(journal)
    log_event(f"Projet '{name}' initialisé", "setup")
    return journal["project"]

def parse_tasks_from_description(description: str) -> list:
    """
    Découpe une description de projet en tâches logiques.
    Retourne une liste de tâches suggérées.
    """
    # Cette fonction sera appelée par l'IA pour suggérer des tâches
    # basées sur l'analyse de la description
    return []

def add_task(title: str, description: str = "", parent_id: Optional[int] = None) -> dict:
    """Ajoute une tâche au projet."""
    journal = init_journal()
    task_id = len(journal["tasks"]) + 1
    task = {
        "id": task_id,
        "title": title,
        "description": description,
        "status": TaskStatus.NOT_STARTED.value,
        "parent_id": parent_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "notes": []
    }
    journal["tasks"].append(task)
    save_journal(journal)
    log_event(f"Tâche ajoutée: {title}", "task_created")
    return task

def update_task_status(task_id: int, status: str) -> Optional[dict]:
    """Met à jour le statut d'une tâche."""
    journal = init_journal()
    for task in journal["tasks"]:
        if task["id"] == task_id:
            old_status = task["status"]
            task["status"] = status
            task["updated_at"] = datetime.now().isoformat()
            save_journal(journal)
            log_event(f"Tâche #{task_id} '{task['title']}': {old_status} → {status}", "status_change")
            return task
    return None

def add_note_to_task(task_id: int, note: str) -> Optional[dict]:
    """Ajoute une note/compte-rendu à une tâche."""
    journal = init_journal()
    for task in journal["tasks"]:
        if task["id"] == task_id:
            note_entry = {
                "timestamp": datetime.now().isoformat(),
                "content": note
            }
            task["notes"].append(note_entry)
            task["updated_at"] = datetime.now().isoformat()
            save_journal(journal)
            log_event(f"Note ajoutée à la tâche #{task_id}", "note_added")
            return task
    return None

def get_progress() -> dict:
    """Calcule la progression globale du projet."""
    journal = init_journal()
    tasks = journal["tasks"]
    if not tasks:
        return {"total": 0, "completed": 0, "in_progress": 0, "not_started": 0, "percentage": 0}

    completed = sum(1 for t in tasks if t["status"] == TaskStatus.COMPLETED.value)
    in_progress = sum(1 for t in tasks if t["status"] == TaskStatus.IN_PROGRESS.value)
    not_started = sum(1 for t in tasks if t["status"] == TaskStatus.NOT_STARTED.value)

    return {
        "total": len(tasks),
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "percentage": round((completed / len(tasks)) * 100, 1)
    }

def generate_progress_bar(percentage: float, width: int = 30) -> str:
    """Génère une barre de progression ASCII."""
    filled = int(width * percentage / 100)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}] {percentage}%"

def start_session() -> dict:
    """Démarre une nouvelle session de travail."""
    journal = init_journal()
    session = {
        "id": len(journal["sessions"]) + 1,
        "started_at": datetime.now().isoformat(),
        "ended_at": None,
        "summary": None,
        "report": None
    }
    journal["sessions"].append(session)
    save_journal(journal)
    log_event(f"Session #{session['id']} démarrée", "session_start")
    return session

def end_session(report: str) -> dict:
    """Termine la session avec un compte-rendu."""
    journal = init_journal()
    if not journal["sessions"]:
        return {"error": "Aucune session active"}

    current_session = journal["sessions"][-1]
    if current_session["ended_at"]:
        return {"error": "La session est déjà terminée"}

    current_session["ended_at"] = datetime.now().isoformat()
    current_session["report"] = report
    save_journal(journal)
    log_event(f"Session #{current_session['id']} terminée", "session_end")
    return current_session

def save_session_summary(session_id: int, summary: str) -> str:
    """Sauvegarde le résumé de session en Markdown."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    journal = init_journal()

    # Trouver la session
    session = None
    for s in journal["sessions"]:
        if s["id"] == session_id:
            session = s
            break

    if not session:
        return ""

    # Créer le fichier Markdown
    filename = f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = SESSIONS_DIR / filename

    # Enrichir le résumé avec les métadonnées
    progress = get_progress()
    full_content = f"""# Résumé Session #{session_id} - Projet Zently

**Date**: {session.get('started_at', 'N/A')}
**Durée**: {_calculate_duration(session.get('started_at'), session.get('ended_at'))}

## Progression Globale
{generate_progress_bar(progress['percentage'])}

- Tâches terminées: {progress['completed']}/{progress['total']}
- En cours: {progress['in_progress']}
- Non commencées: {progress['not_started']}

## Résumé de la Session
{summary}

## Compte-rendu Original
{session.get('report', 'N/A')}

---
*Généré automatiquement par Zently Event Logger*
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_content)

    # Mettre à jour la session avec le chemin du résumé
    session["summary_file"] = str(filepath)
    save_journal(journal)
    log_event(f"Résumé de session sauvegardé: {filename}", "summary_saved")

    return str(filepath)

def _calculate_duration(start: Optional[str], end: Optional[str]) -> str:
    """Calcule la durée entre deux timestamps."""
    if not start or not end:
        return "N/A"
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        delta = end_dt - start_dt
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}min"
    except:
        return "N/A"

def get_all_summaries() -> list:
    """Récupère tous les résumés de sessions pour l'analyse IA."""
    summaries = []
    if SESSIONS_DIR.exists():
        for file in sorted(SESSIONS_DIR.glob("*.md")):
            with open(file, 'r', encoding='utf-8') as f:
                summaries.append({
                    "filename": file.name,
                    "content": f.read()
                })
    return summaries

def get_status_display() -> str:
    """Affiche l'état complet du projet."""
    journal = init_journal()
    progress = get_progress()

    output = []
    output.append("=" * 60)
    output.append(f"🗂️  PROJET: {journal['project'].get('name', 'Non configuré')}")
    output.append("=" * 60)

    if journal['project'].get('description'):
        output.append(f"\n📝 Description: {journal['project']['description'][:100]}...")

    output.append(f"\n📊 PROGRESSION GLOBALE")
    output.append(generate_progress_bar(progress['percentage']))
    output.append(f"   {progress['completed']}/{progress['total']} tâches terminées")

    output.append(f"\n📋 TÂCHES ({len(journal['tasks'])})")
    output.append("-" * 40)

    status_icons = {
        TaskStatus.NOT_STARTED.value: "⬜",
        TaskStatus.IN_PROGRESS.value: "🔶",
        TaskStatus.COMPLETED.value: "✅"
    }

    for task in journal["tasks"]:
        icon = status_icons.get(task["status"], "❓")
        indent = "  " if task.get("parent_id") else ""
        output.append(f"{indent}{icon} [{task['id']}] {task['title']} - {task['status']}")
        if task.get("notes"):
            output.append(f"{indent}    └─ {len(task['notes'])} note(s)")

    output.append(f"\n📅 SESSIONS ({len(journal['sessions'])})")
    output.append("-" * 40)
    for session in journal["sessions"][-5:]:  # 5 dernières sessions
        status = "✅" if session.get("ended_at") else "🔄"
        output.append(f"{status} Session #{session['id']} - {session['started_at'][:10]}")

    output.append(f"\n📜 DERNIERS ÉVÉNEMENTS ({len(journal['events'])})")
    output.append("-" * 40)
    for event in journal["events"][-5:]:  # 5 derniers événements
        output.append(f"[{event['timestamp'][:19]}] {event['message']}")

    return "\n".join(output)

def get_task_details(task_id: int) -> Optional[dict]:
    """Récupère les détails complets d'une tâche."""
    journal = init_journal()
    for task in journal["tasks"]:
        if task["id"] == task_id:
            return task
    return None

def complete_onboarding(project_name: str, project_description: str, tasks: list) -> dict:
    """Complète l'onboarding avec le projet et les tâches."""
    journal = init_journal()

    # Configuration du projet
    setup_project(project_name, project_description)

    # Ajout des tâches
    for task_data in tasks:
        add_task(
            title=task_data.get("title", ""),
            description=task_data.get("description", ""),
            parent_id=task_data.get("parent_id")
        )

    journal = init_journal()
    journal["project"]["onboarding_complete"] = True
    save_journal(journal)
    log_event("Onboarding complété", "onboarding")

    return {
        "project": journal["project"],
        "tasks_count": len(journal["tasks"]),
        "status": get_status_display()
    }

def export_for_google_drive() -> str:
    """Exporte toutes les données en format prêt pour Google Drive."""
    journal = init_journal()
    progress = get_progress()

    export_content = f"""# Journal de Bord - {journal['project'].get('name', 'Projet Zently')}

## Informations Projet
- **Nom**: {journal['project'].get('name', 'N/A')}
- **Créé le**: {journal['project'].get('created_at', 'N/A')}
- **Description**: {journal['project'].get('description', 'N/A')}

## Progression
{generate_progress_bar(progress['percentage'])}

| Statut | Nombre |
|--------|--------|
| Terminées | {progress['completed']} |
| En cours | {progress['in_progress']} |
| Non commencées | {progress['not_started']} |

## Tâches

"""
    for task in journal["tasks"]:
        status_emoji = {"Non commencé": "⬜", "En cours": "🔶", "Terminé": "✅"}.get(task["status"], "❓")
        export_content += f"### {status_emoji} {task['title']}\n"
        export_content += f"- **ID**: {task['id']}\n"
        export_content += f"- **Statut**: {task['status']}\n"
        export_content += f"- **Créé**: {task['created_at']}\n"
        if task.get("description"):
            export_content += f"- **Description**: {task['description']}\n"
        if task.get("notes"):
            export_content += "- **Notes**:\n"
            for note in task["notes"]:
                export_content += f"  - [{note['timestamp'][:10]}] {note['content']}\n"
        export_content += "\n"

    export_content += "## Historique des Sessions\n\n"
    for session in journal["sessions"]:
        status = "Terminée" if session.get("ended_at") else "En cours"
        export_content += f"### Session #{session['id']} ({status})\n"
        export_content += f"- Début: {session['started_at']}\n"
        if session.get("ended_at"):
            export_content += f"- Fin: {session['ended_at']}\n"
        if session.get("report"):
            export_content += f"- Compte-rendu: {session['report'][:200]}...\n"
        export_content += "\n"

    # Sauvegarder le fichier d'export
    export_file = DATA_DIR / f"export_zently_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(export_file, 'w', encoding='utf-8') as f:
        f.write(export_content)

    log_event(f"Export créé: {export_file.name}", "export")
    return str(export_file)


# === INTERFACE POUR CLAUDE CODE ===

def show_help():
    """Affiche l'aide du journal."""
    return """
╔══════════════════════════════════════════════════════════════╗
║           ZENTLY EVENT LOGGER - Guide d'utilisation          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  COMMANDES DISPONIBLES (via Python):                         ║
║                                                              ║
║  📋 GESTION DU PROJET                                        ║
║  • get_status_display()     - Afficher l'état du projet      ║
║  • complete_onboarding()    - Configurer le projet           ║
║  • get_progress()           - Obtenir la progression         ║
║                                                              ║
║  📝 GESTION DES TÂCHES                                       ║
║  • add_task(title, desc)    - Ajouter une tâche              ║
║  • update_task_status(id, status) - Changer le statut        ║
║  • add_note_to_task(id, note)     - Ajouter un compte-rendu  ║
║  • get_task_details(id)     - Détails d'une tâche            ║
║                                                              ║
║  📅 SESSIONS DE TRAVAIL                                      ║
║  • start_session()          - Démarrer une session           ║
║  • end_session(report)      - Terminer avec compte-rendu     ║
║  • save_session_summary()   - Sauvegarder résumé IA          ║
║                                                              ║
║  📤 EXPORT                                                   ║
║  • export_for_google_drive() - Export Markdown complet       ║
║  • get_all_summaries()       - Récupérer tous les résumés    ║
║                                                              ║
║  STATUTS DES TÂCHES:                                         ║
║  • "Non commencé" | "En cours" | "Terminé"                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

if __name__ == "__main__":
    print(show_help())
    print("\n" + get_status_display())
