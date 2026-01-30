#!/usr/bin/env python3
"""
Zently Event Logger - Interface Web Streamlit
Déployable gratuitement sur Streamlit Cloud
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path

# Configuration
st.set_page_config(
    page_title="Zently Journal",
    page_icon="🗂️",
    layout="wide"
)

# Chemins
DATA_DIR = Path(__file__).parent / "data"
JOURNAL_FILE = DATA_DIR / "journal.json"
SESSIONS_DIR = DATA_DIR / "sessions"

# === FONCTIONS DE BASE ===

def load_journal():
    """Charge le journal."""
    if JOURNAL_FILE.exists():
        with open(JOURNAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "project": {"name": "", "description": "", "created_at": None, "onboarding_complete": False},
        "tasks": [],
        "events": [],
        "sessions": []
    }

def save_journal(data):
    """Sauvegarde le journal."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def log_event(journal, message, event_type="info"):
    """Enregistre un événement."""
    journal["events"].append({
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "message": message
    })
    return journal

# === INTERFACE ===

def main():
    journal = load_journal()

    # Header
    st.title("🗂️ Zently Event Logger")

    if journal["project"].get("name"):
        st.caption(f"Projet: **{journal['project']['name']}**")

    # Sidebar - Navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("", ["📊 Dashboard", "📋 Tâches", "📅 Sessions", "📜 Événements", "⚙️ Configuration"])

    # === DASHBOARD ===
    if page == "📊 Dashboard":
        show_dashboard(journal)

    # === TÂCHES ===
    elif page == "📋 Tâches":
        show_tasks(journal)

    # === SESSIONS ===
    elif page == "📅 Sessions":
        show_sessions(journal)

    # === ÉVÉNEMENTS ===
    elif page == "📜 Événements":
        show_events(journal)

    # === CONFIGURATION ===
    elif page == "⚙️ Configuration":
        show_config(journal)


def show_dashboard(journal):
    """Affiche le dashboard principal."""
    st.header("📊 Dashboard")

    tasks = journal.get("tasks", [])

    if not tasks:
        st.warning("Aucune tâche. Allez dans Configuration pour l'onboarding.")
        return

    # Métriques
    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "Terminé")
    in_progress = sum(1 for t in tasks if t["status"] == "En cours")
    not_started = sum(1 for t in tasks if t["status"] == "Non commencé")
    percentage = round((completed / total) * 100, 1) if total > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Progression", f"{percentage}%")
    col2.metric("Terminées", f"{completed}/{total}")
    col3.metric("En cours", in_progress)
    col4.metric("Non commencées", not_started)

    # Barre de progression
    st.progress(percentage / 100)

    # Liste des tâches en cours
    st.subheader("🔶 Tâches en cours")
    current_tasks = [t for t in tasks if t["status"] == "En cours"]
    if current_tasks:
        for task in current_tasks:
            st.info(f"**[{task['id']}] {task['title']}** - {task.get('description', '')}")
    else:
        st.caption("Aucune tâche en cours")

    # Sessions actives
    st.subheader("📅 Session active")
    active_sessions = [s for s in journal.get("sessions", []) if not s.get("ended_at")]
    if active_sessions:
        s = active_sessions[-1]
        st.success(f"Session #{s['id']} - Démarrée le {s['started_at'][:16]}")
    else:
        st.caption("Aucune session active")


def show_tasks(journal):
    """Affiche et gère les tâches."""
    st.header("📋 Gestion des Tâches")

    tasks = journal.get("tasks", [])

    if not tasks:
        st.warning("Aucune tâche créée.")
        return

    # Filtres
    status_filter = st.selectbox("Filtrer par statut", ["Tous", "Non commencé", "En cours", "Terminé"])

    filtered_tasks = tasks if status_filter == "Tous" else [t for t in tasks if t["status"] == status_filter]

    for task in filtered_tasks:
        status_icon = {"Non commencé": "⬜", "En cours": "🔶", "Terminé": "✅"}.get(task["status"], "❓")

        with st.expander(f"{status_icon} [{task['id']}] {task['title']} - {task['status']}"):
            st.write(f"**Description:** {task.get('description', 'N/A')}")
            st.write(f"**Créé:** {task['created_at'][:10]}")

            # Changer le statut
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox(
                    "Statut",
                    ["Non commencé", "En cours", "Terminé"],
                    index=["Non commencé", "En cours", "Terminé"].index(task["status"]),
                    key=f"status_{task['id']}"
                )
                if new_status != task["status"]:
                    if st.button(f"Mettre à jour", key=f"btn_status_{task['id']}"):
                        task["status"] = new_status
                        task["updated_at"] = datetime.now().isoformat()
                        journal = log_event(journal, f"Tâche #{task['id']}: {task['status']} → {new_status}", "status_change")
                        save_journal(journal)
                        st.rerun()

            # Notes
            st.write("**Notes:**")
            for note in task.get("notes", []):
                st.caption(f"[{note['timestamp'][:10]}] {note['content']}")

            # Ajouter une note
            with col2:
                new_note = st.text_area("Nouvelle note", key=f"note_{task['id']}", height=100)
                if st.button("Ajouter note", key=f"btn_note_{task['id']}"):
                    if new_note:
                        task.setdefault("notes", []).append({
                            "timestamp": datetime.now().isoformat(),
                            "content": new_note
                        })
                        journal = log_event(journal, f"Note ajoutée à tâche #{task['id']}", "note_added")
                        save_journal(journal)
                        st.rerun()


def show_sessions(journal):
    """Gère les sessions de travail."""
    st.header("📅 Sessions de Travail")

    sessions = journal.get("sessions", [])
    active_session = next((s for s in sessions if not s.get("ended_at")), None)

    # Actions
    col1, col2 = st.columns(2)

    with col1:
        if not active_session:
            if st.button("🚀 Démarrer une session"):
                new_session = {
                    "id": len(sessions) + 1,
                    "started_at": datetime.now().isoformat(),
                    "ended_at": None,
                    "summary": None,
                    "report": None
                }
                journal["sessions"].append(new_session)
                journal = log_event(journal, f"Session #{new_session['id']} démarrée", "session_start")
                save_journal(journal)
                st.rerun()
        else:
            st.success(f"🔄 Session #{active_session['id']} en cours")

    with col2:
        if active_session:
            report = st.text_area("Compte-rendu de fin de session", height=150)
            if st.button("🏁 Terminer la session"):
                active_session["ended_at"] = datetime.now().isoformat()
                active_session["report"] = report
                journal = log_event(journal, f"Session #{active_session['id']} terminée", "session_end")
                save_journal(journal)
                st.success("Session terminée!")
                st.rerun()

    # Historique
    st.subheader("Historique des sessions")
    for s in reversed(sessions):
        status = "✅" if s.get("ended_at") else "🔄"
        with st.expander(f"{status} Session #{s['id']} - {s['started_at'][:10]}"):
            st.write(f"**Début:** {s['started_at']}")
            st.write(f"**Fin:** {s.get('ended_at', 'En cours')}")
            if s.get("report"):
                st.write(f"**Compte-rendu:** {s['report']}")


def show_events(journal):
    """Affiche l'historique des événements."""
    st.header("📜 Historique des Événements")

    events = journal.get("events", [])

    if not events:
        st.info("Aucun événement enregistré.")
        return

    # Afficher les événements récents en premier
    for event in reversed(events[-50:]):
        timestamp = event["timestamp"][:19].replace("T", " ")
        event_type = event.get("type", "info")

        type_colors = {
            "session_start": "🟢",
            "session_end": "🔴",
            "status_change": "🔶",
            "task_created": "➕",
            "note_added": "📝",
            "onboarding": "🚀",
            "setup": "⚙️"
        }
        icon = type_colors.get(event_type, "📌")

        st.text(f"{icon} [{timestamp}] {event['message']}")


def show_config(journal):
    """Configuration et onboarding."""
    st.header("⚙️ Configuration")

    # Onboarding
    if not journal["project"].get("onboarding_complete"):
        st.subheader("🚀 Onboarding")

        name = st.text_input("Nom du projet", value="Zently.fr")
        description = st.text_area("Description du projet", height=100)

        st.write("**Tâches** (une par ligne)")
        tasks_text = st.text_area("Liste des tâches", height=200,
            placeholder="Architecture & Infrastructure\nSystème d'authentification\nDashboard Hub Central\n...")

        if st.button("Valider l'onboarding"):
            journal["project"]["name"] = name
            journal["project"]["description"] = description
            journal["project"]["created_at"] = datetime.now().isoformat()
            journal["project"]["onboarding_complete"] = True

            # Créer les tâches
            for i, title in enumerate(tasks_text.strip().split("\n"), 1):
                if title.strip():
                    journal["tasks"].append({
                        "id": i,
                        "title": title.strip(),
                        "description": "",
                        "status": "Non commencé",
                        "parent_id": None,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                        "notes": []
                    })

            journal = log_event(journal, f"Onboarding complété - {len(journal['tasks'])} tâches", "onboarding")
            save_journal(journal)
            st.success("Onboarding complété!")
            st.rerun()

    else:
        st.success(f"Projet configuré: **{journal['project']['name']}**")
        st.write(journal["project"].get("description", ""))

        # Ajouter une tâche
        st.subheader("➕ Ajouter une tâche")
        new_title = st.text_input("Titre de la tâche")
        new_desc = st.text_input("Description (optionnel)")

        if st.button("Ajouter"):
            if new_title:
                new_id = max([t["id"] for t in journal["tasks"]], default=0) + 1
                journal["tasks"].append({
                    "id": new_id,
                    "title": new_title,
                    "description": new_desc,
                    "status": "Non commencé",
                    "parent_id": None,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "notes": []
                })
                journal = log_event(journal, f"Tâche ajoutée: {new_title}", "task_created")
                save_journal(journal)
                st.success(f"Tâche #{new_id} ajoutée!")
                st.rerun()

        # Export
        st.subheader("📤 Export")
        if st.button("Générer export Markdown"):
            export = generate_export(journal)
            st.download_button("Télécharger", export, "zently_export.md", "text/markdown")


def generate_export(journal):
    """Génère l'export Markdown."""
    tasks = journal.get("tasks", [])
    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "Terminé")
    percentage = round((completed / total) * 100, 1) if total > 0 else 0

    content = f"""# Journal de Bord - {journal['project'].get('name', 'Zently')}

## Progression: {percentage}% ({completed}/{total} tâches)

## Tâches

"""
    for task in tasks:
        icon = {"Non commencé": "⬜", "En cours": "🔶", "Terminé": "✅"}.get(task["status"], "❓")
        content += f"### {icon} [{task['id']}] {task['title']}\n"
        content += f"- Statut: {task['status']}\n"
        if task.get("notes"):
            content += "- Notes:\n"
            for note in task["notes"]:
                content += f"  - {note['content']}\n"
        content += "\n"

    return content


if __name__ == "__main__":
    main()
