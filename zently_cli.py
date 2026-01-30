#!/usr/bin/env python3
"""
Zently CLI - Interface interactive pour le journal de bord
Usage: python zently_cli.py
"""

import sys
from zently_journal import (
    init_journal, get_status_display, add_task, update_task_status,
    add_note_to_task, get_task_details, start_session, end_session,
    save_session_summary, get_progress, generate_progress_bar,
    complete_onboarding, export_for_google_drive, get_all_summaries,
    show_help, log_event, TaskStatus
)

def clear_screen():
    print("\033[2J\033[H", end="")

def print_header():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    🗂️  ZENTLY EVENT LOGGER                    ║
║              Journal de bord pour la création web             ║
╚═══════════════════════════════════════════════════════════════╝
""")

def menu_principal():
    journal = init_journal()

    if not journal["project"]["onboarding_complete"]:
        print("\n⚠️  Onboarding non complété. Utilisez l'option 1 pour configurer le projet.")

    print("""
┌─────────────────────────────────────┐
│           MENU PRINCIPAL            │
├─────────────────────────────────────┤
│  1. 🚀 Onboarding (nouveau projet)  │
│  2. 📊 Voir l'état du projet        │
│  3. ➕ Ajouter une tâche            │
│  4. 📝 Mettre à jour une tâche      │
│  5. 📅 Gérer les sessions           │
│  6. 📤 Exporter pour Google Drive   │
│  7. ❓ Aide                         │
│  8. 🚪 Quitter                      │
└─────────────────────────────────────┘
""")
    return input("Choix: ").strip()

def menu_onboarding():
    print("\n" + "="*50)
    print("🚀 ONBOARDING - Configuration du projet")
    print("="*50)

    name = input("\nNom du projet: ").strip()
    if not name:
        name = "Zently"

    print("\nDécrivez votre projet (terminez par une ligne vide):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    description = "\n".join(lines)

    print("\n📋 Entrez les tâches du projet (une par ligne, ligne vide pour terminer):")
    tasks = []
    i = 1
    while True:
        task_title = input(f"  Tâche {i}: ").strip()
        if not task_title:
            break
        tasks.append({"title": task_title, "description": ""})
        i += 1

    result = complete_onboarding(name, description, tasks)
    print("\n✅ Onboarding complété!")
    print(f"   {result['tasks_count']} tâches créées")
    input("\nAppuyez sur Entrée pour continuer...")

def menu_update_task():
    journal = init_journal()

    print("\n" + "="*50)
    print("📝 MISE À JOUR D'UNE TÂCHE")
    print("="*50)

    print("\nTâches disponibles:")
    for task in journal["tasks"]:
        status_icon = {"Non commencé": "⬜", "En cours": "🔶", "Terminé": "✅"}.get(task["status"], "❓")
        print(f"  {status_icon} [{task['id']}] {task['title']} - {task['status']}")

    task_id = input("\nID de la tâche: ").strip()
    if not task_id.isdigit():
        print("❌ ID invalide")
        return

    task = get_task_details(int(task_id))
    if not task:
        print("❌ Tâche non trouvée")
        return

    print(f"\n📌 Tâche: {task['title']}")
    print(f"   Statut actuel: {task['status']}")

    print("""
Actions:
  1. Changer le statut
  2. Ajouter une note/compte-rendu
  3. Voir les détails complets
""")

    action = input("Action: ").strip()

    if action == "1":
        print("\nStatuts disponibles:")
        print("  1. Non commencé")
        print("  2. En cours")
        print("  3. Terminé")
        status_choice = input("Nouveau statut: ").strip()
        status_map = {"1": "Non commencé", "2": "En cours", "3": "Terminé"}
        if status_choice in status_map:
            update_task_status(int(task_id), status_map[status_choice])
            print(f"✅ Statut mis à jour: {status_map[status_choice]}")

    elif action == "2":
        print("\nEntrez votre compte-rendu (ligne vide pour terminer):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        note = "\n".join(lines)
        if note:
            add_note_to_task(int(task_id), note)
            print("✅ Note ajoutée")

    elif action == "3":
        print(f"\n{'='*50}")
        print(f"📌 {task['title']}")
        print(f"{'='*50}")
        print(f"ID: {task['id']}")
        print(f"Statut: {task['status']}")
        print(f"Créé le: {task['created_at']}")
        print(f"Mis à jour: {task['updated_at']}")
        if task.get('description'):
            print(f"Description: {task['description']}")
        if task.get('notes'):
            print(f"\nNotes ({len(task['notes'])}):")
            for note in task['notes']:
                print(f"  [{note['timestamp'][:10]}] {note['content'][:100]}")

    input("\nAppuyez sur Entrée pour continuer...")

def menu_sessions():
    print("\n" + "="*50)
    print("📅 GESTION DES SESSIONS")
    print("="*50)

    journal = init_journal()
    active_session = None
    for s in journal["sessions"]:
        if not s.get("ended_at"):
            active_session = s
            break

    if active_session:
        print(f"\n🔄 Session active: #{active_session['id']}")
        print(f"   Démarrée le: {active_session['started_at']}")
    else:
        print("\n⬜ Aucune session active")

    print("""
Actions:
  1. Démarrer une nouvelle session
  2. Terminer la session en cours
  3. Voir l'historique des sessions
""")

    action = input("Action: ").strip()

    if action == "1":
        session = start_session()
        print(f"✅ Session #{session['id']} démarrée")

    elif action == "2":
        if not active_session:
            print("❌ Aucune session active")
        else:
            print("\nEntrez votre compte-rendu de session (ligne vide pour terminer):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            report = "\n".join(lines)

            session = end_session(report)
            print(f"✅ Session #{session['id']} terminée")

            # Demander si on veut sauvegarder un résumé
            save_summary = input("\nVoulez-vous sauvegarder un résumé IA? (o/n): ").strip().lower()
            if save_summary == 'o':
                summary = input("Entrez le résumé (ou laissez vide pour utiliser le rapport): ").strip()
                if not summary:
                    summary = report
                filepath = save_session_summary(session['id'], summary)
                print(f"✅ Résumé sauvegardé: {filepath}")

    elif action == "3":
        print("\nHistorique des sessions:")
        for s in journal["sessions"]:
            status = "✅" if s.get("ended_at") else "🔄"
            print(f"  {status} Session #{s['id']} - {s['started_at'][:16]}")

    input("\nAppuyez sur Entrée pour continuer...")

def main():
    while True:
        clear_screen()
        print_header()

        # Afficher la progression
        progress = get_progress()
        if progress["total"] > 0:
            print(generate_progress_bar(progress["percentage"]))
            print()

        choice = menu_principal()

        if choice == "1":
            menu_onboarding()
        elif choice == "2":
            print("\n" + get_status_display())
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "3":
            print("\n➕ NOUVELLE TÂCHE")
            title = input("Titre: ").strip()
            if title:
                desc = input("Description (optionnel): ").strip()
                add_task(title, desc)
                print("✅ Tâche ajoutée")
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "4":
            menu_update_task()
        elif choice == "5":
            menu_sessions()
        elif choice == "6":
            filepath = export_for_google_drive()
            print(f"\n✅ Export créé: {filepath}")
            print("   Vous pouvez maintenant uploader ce fichier sur Google Drive")
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "7":
            print(show_help())
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "8":
            print("\n👋 Au revoir!")
            log_event("Session CLI terminée", "cli_exit")
            break
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main()
