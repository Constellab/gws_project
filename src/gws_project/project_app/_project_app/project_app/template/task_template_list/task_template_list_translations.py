"""Translations for the task template list and its shared table component.

Registered once at import time. Covers both ``task_template_list_component.py`` /
``task_template_list_state.py`` (``task_template_list.*`` keys) and the shared
``task_template_table_component.py`` (``task_template_table.*`` keys), since the
table is a low-level reusable piece of the task template list feature.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "task_template_list.heading": "Task Templates",
            "task_template_list.create_button": "Create Task Template",
            "task_template_list.no_template_context": "No template context found",
            "task_template_list.invalid_template_context": "Invalid template context",
            "task_template_list.delete_dialog_title": "Delete Task Template",
            "task_template_list.delete_dialog_content": "Are you sure you want to delete this task template?",
            "task_template_list.delete_dialog_warning": " This will also delete all its descendants (subtask templates, sub-subtask templates, etc.).",
            "task_template_list.deleted_toast": "Task template deleted successfully",
            "task_template_table.column_title": "Title",
            "task_template_table.column_start_offset": "Start Offset (days)",
            "task_template_table.column_duration": "Duration (days)",
            "task_template_table.column_priority": "Priority",
            "task_template_table.column_assigned_role": "Assigned Role",
            "task_template_table.column_actions": "Actions",
            "task_template_table.empty_message": "No task templates found",
            "task_template_table.unassigned": "Unassigned",
            "task_template_table.update": "Update",
            "task_template_table.move_up": "Move up",
            "task_template_table.move_down": "Move down",
            "task_template_table.delete": "Delete",
        },
        "fr": {
            "task_template_list.heading": "Modèles de tâches",
            "task_template_list.create_button": "Créer un modèle de tâche",
            "task_template_list.no_template_context": "Aucun contexte de modèle trouvé",
            "task_template_list.invalid_template_context": "Contexte de modèle invalide",
            "task_template_list.delete_dialog_title": "Supprimer le modèle de tâche",
            "task_template_list.delete_dialog_content": "Êtes-vous sûr de vouloir supprimer ce modèle de tâche ?",
            "task_template_list.delete_dialog_warning": " Cela supprimera également tous ses descendants (modèles de sous-tâches, modèles de sous-sous-tâches, etc.).",
            "task_template_list.deleted_toast": "Modèle de tâche supprimé avec succès",
            "task_template_table.column_title": "Titre",
            "task_template_table.column_start_offset": "Décalage de début (jours)",
            "task_template_table.column_duration": "Durée (jours)",
            "task_template_table.column_priority": "Priorité",
            "task_template_table.column_assigned_role": "Rôle assigné",
            "task_template_table.column_actions": "Actions",
            "task_template_table.empty_message": "Aucun modèle de tâche trouvé",
            "task_template_table.unassigned": "Non assigné",
            "task_template_table.update": "Modifier",
            "task_template_table.move_up": "Monter",
            "task_template_table.move_down": "Descendre",
            "task_template_table.delete": "Supprimer",
        },
    }
)
