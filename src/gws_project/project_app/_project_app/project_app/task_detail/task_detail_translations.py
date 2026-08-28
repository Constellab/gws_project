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
        },
    }
)
