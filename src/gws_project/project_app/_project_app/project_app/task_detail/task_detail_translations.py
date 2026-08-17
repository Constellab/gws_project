"""Translations for the Task Detail page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "task_detail.tab_action.create_subtask": "Create Subtask",
            "task_detail.tab_action.edit": "Edit",
            "task_detail.tab_action.view": "View",
            "task_detail.tab_action.create_note": "Create Note",
            "task_detail.tab_action.upload_file": "Upload File",
            "task_detail.tab.subtasks": "Subtasks",
            "task_detail.tab.description": "Description",
            "task_detail.tab.documents": "Documents",
            "task_detail.tab.activity": "Activity",
            "task_detail.sidebar.title": "Task details",
            "task_detail.sidebar.assigned_to": "Assigned to",
            "task_detail.sidebar.parent_task": "Parent task",
            "task_detail.sidebar.subtask_members": "Subtask members",
            "task_detail.sidebar.no_members": "No members assigned",
            "task_detail.sidebar.status": "Status",
            "task_detail.sidebar.priority": "Priority",
            "task_detail.sidebar.dates": "Dates",
            "task_detail.sidebar.created_by": "Created by",
            "task_detail.sidebar.created_at": "Created at",
            "task_detail.sidebar.last_modified_by": "Last modified by",
            "task_detail.sidebar.last_modified_at": "Last modified at",
        },
        "fr": {
            "task_detail.tab_action.create_subtask": "Créer une sous-tâche",
            "task_detail.tab_action.edit": "Modifier",
            "task_detail.tab_action.view": "Voir",
            "task_detail.tab_action.create_note": "Créer une note",
            "task_detail.tab_action.upload_file": "Importer un fichier",
            "task_detail.tab.subtasks": "Sous-tâches",
            "task_detail.tab.description": "Description",
            "task_detail.tab.documents": "Documents",
            "task_detail.tab.activity": "Activité",
            "task_detail.sidebar.title": "Détails de la tâche",
            "task_detail.sidebar.assigned_to": "Assigné à",
            "task_detail.sidebar.parent_task": "Tâche parente",
            "task_detail.sidebar.subtask_members": "Membres des sous-tâches",
            "task_detail.sidebar.no_members": "Aucun membre assigné",
            "task_detail.sidebar.status": "Statut",
            "task_detail.sidebar.priority": "Priorité",
            "task_detail.sidebar.dates": "Dates",
            "task_detail.sidebar.created_by": "Créé par",
            "task_detail.sidebar.created_at": "Créé le",
            "task_detail.sidebar.last_modified_by": "Modifié par",
            "task_detail.sidebar.last_modified_at": "Modifié le",
        },
    }
)
