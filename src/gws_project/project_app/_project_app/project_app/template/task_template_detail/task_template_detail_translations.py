"""Translations for the task template detail page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "task_template_detail.update_menu_item": "Update Task Template",
            "task_template_detail.delete_menu_item": "Delete",
            "task_template_detail.create_subtask_button": "Create Subtask Template",
            "task_template_detail.view": "View",
            "task_template_detail.edit": "Edit",
            "task_template_detail.tab_subtasks": "Subtasks",
            "task_template_detail.tab_description": "Description",
            "task_template_detail.no_subtasks_allowed": "This task template does not allow subtasks",
            "task_template_detail.sidebar_title": "Task template details",
            "task_template_detail.parent_task_template": "Parent task template",
            "task_template_detail.assigned_role": "Assigned role",
            "task_template_detail.unassigned": "Unassigned",
            "task_template_detail.priority": "Priority",
            "task_template_detail.start_offset": "Start date offset (days)",
            "task_template_detail.duration": "Duration (days)",
            "task_template_detail.created_by": "Created by",
            "task_template_detail.created_at": "Created at",
            "task_template_detail.last_modified_by": "Last modified by",
            "task_template_detail.last_modified_at": "Last modified at",
            "task_template_detail.task_template_not_found": "Task template not found",
            "task_template_detail.delete_dialog_title": "Delete Task Template",
            "task_template_detail.delete_dialog_content": "Are you sure you want to delete this task template?",
            "task_template_detail.delete_dialog_warning": " This will also delete all its descendants (subtask templates, sub-subtask templates, etc.).",
            "task_template_detail.deleted_toast": "Task template deleted successfully",
        },
        "fr": {
            "task_template_detail.update_menu_item": "Modifier le modèle de tâche",
            "task_template_detail.delete_menu_item": "Supprimer",
            "task_template_detail.create_subtask_button": "Créer un modèle de sous-tâche",
            "task_template_detail.view": "Afficher",
            "task_template_detail.edit": "Modifier",
            "task_template_detail.tab_subtasks": "Sous-tâches",
            "task_template_detail.tab_description": "Description",
            "task_template_detail.no_subtasks_allowed": "Ce modèle de tâche n'autorise pas les sous-tâches",
            "task_template_detail.sidebar_title": "Détails du modèle de tâche",
            "task_template_detail.parent_task_template": "Modèle de tâche parent",
            "task_template_detail.assigned_role": "Rôle assigné",
            "task_template_detail.unassigned": "Non assigné",
            "task_template_detail.priority": "Priorité",
            "task_template_detail.start_offset": "Décalage de date de début (jours)",
            "task_template_detail.duration": "Durée (jours)",
            "task_template_detail.created_by": "Créé par",
            "task_template_detail.created_at": "Créé le",
            "task_template_detail.last_modified_by": "Dernière modification par",
            "task_template_detail.last_modified_at": "Dernière modification le",
            "task_template_detail.task_template_not_found": "Modèle de tâche introuvable",
            "task_template_detail.delete_dialog_title": "Supprimer le modèle de tâche",
            "task_template_detail.delete_dialog_content": "Êtes-vous sûr de vouloir supprimer ce modèle de tâche ?",
            "task_template_detail.delete_dialog_warning": " Cela supprimera également tous ses descendants (modèles de sous-tâches, modèles de sous-sous-tâches, etc.).",
            "task_template_detail.deleted_toast": "Modèle de tâche supprimé avec succès",
        },
    }
)
