"""Translations for the shared task/project details sidebar. Registered once at import time.

These texts are shared by the detail pages (where the sidebar is the page's right panel)
and by the details panel opened from Kanban, Gantt, Planning and My work, so they live in
a common module rather than in either page's translations.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            # Task sections
            "details_sidebar.task.title": "Task details",
            "details_sidebar.task.assigned_to": "Assigned to",
            "details_sidebar.task.parent_task": "Parent task",
            "details_sidebar.task.subtask_members": "Subtask members",
            "details_sidebar.task.no_members": "No members assigned",
            "details_sidebar.task.status": "Status",
            "details_sidebar.task.priority": "Priority",
            "details_sidebar.task.dates": "Dates",
            "details_sidebar.task.project": "Project",
            # Project sections
            "details_sidebar.project.title": "Project details",
            "details_sidebar.project.manager": "Manager",
            "details_sidebar.project.company": "Company",
            "details_sidebar.project.dates": "Dates",
            "details_sidebar.project.members": "Members",
            "details_sidebar.project.no_members": "No team members",
            # Metadata rows, shared by both
            "details_sidebar.created_by": "Created by",
            "details_sidebar.created_at": "Created at",
            "details_sidebar.last_modified_by": "Last modified by",
            "details_sidebar.last_modified_at": "Last modified at",
            # Details panel
            "details_sidebar.panel.open_task": "Open this task",
            "details_sidebar.panel.open_project": "Open this project",
            "details_sidebar.panel.close": "Close",
        },
        "fr": {
            # Task sections
            "details_sidebar.task.title": "Détails de la tâche",
            "details_sidebar.task.assigned_to": "Assigné à",
            "details_sidebar.task.parent_task": "Tâche parente",
            "details_sidebar.task.subtask_members": "Membres des sous-tâches",
            "details_sidebar.task.no_members": "Aucun membre assigné",
            "details_sidebar.task.status": "Statut",
            "details_sidebar.task.priority": "Priorité",
            "details_sidebar.task.dates": "Dates",
            "details_sidebar.task.project": "Projet",
            # Project sections
            "details_sidebar.project.title": "Détails du projet",
            "details_sidebar.project.manager": "Responsable",
            "details_sidebar.project.company": "Entreprise",
            "details_sidebar.project.dates": "Dates",
            "details_sidebar.project.members": "Membres",
            "details_sidebar.project.no_members": "Aucun membre d'équipe",
            # Metadata rows, shared by both
            "details_sidebar.created_by": "Créé par",
            "details_sidebar.created_at": "Créé le",
            "details_sidebar.last_modified_by": "Modifié par",
            "details_sidebar.last_modified_at": "Modifié le",
            # Details panel
            "details_sidebar.panel.open_task": "Ouvrir cette tâche",
            "details_sidebar.panel.open_project": "Ouvrir ce projet",
            "details_sidebar.panel.close": "Fermer",
        },
    }
)
