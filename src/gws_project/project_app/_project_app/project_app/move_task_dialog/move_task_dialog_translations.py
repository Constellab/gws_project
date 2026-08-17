"""Translations for the Move Task dialog. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "move_task.projects_root": "Projects",
            "move_task.folder_empty": "This folder is empty.",
            "move_task.no_projects_found": "No projects found.",
            "move_task.assignee_column": "Assignee",
            "move_task.manager_column": "Manager",
            "move_task.name_column": "Name",
            "move_task.title": "Move Task",
            "move_task.cancel": "Cancel",
            "move_task.move_here": "Move here",
            "move_task.select_destination_error": "Please select a destination project.",
            "move_task.moved_success": "Task moved successfully",
        },
        "fr": {
            "move_task.projects_root": "Projets",
            "move_task.folder_empty": "Ce dossier est vide.",
            "move_task.no_projects_found": "Aucun projet trouvé.",
            "move_task.assignee_column": "Assigné à",
            "move_task.manager_column": "Responsable",
            "move_task.name_column": "Nom",
            "move_task.title": "Déplacer la tâche",
            "move_task.cancel": "Annuler",
            "move_task.move_here": "Déplacer ici",
            "move_task.select_destination_error": "Veuillez sélectionner un projet de destination.",
            "move_task.moved_success": "Tâche déplacée avec succès",
        },
    }
)
