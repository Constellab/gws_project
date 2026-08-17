"""Translations for the project template detail page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "project_template_detail.update_menu_item": "Update Template",
            "project_template_detail.delete_menu_item": "Delete Template",
            "project_template_detail.delete_dialog_title": "Delete Template",
            "project_template_detail.delete_dialog_description": "Are you sure you want to delete this template? This action cannot be undone.",
            "project_template_detail.cancel": "Cancel",
            "project_template_detail.delete": "Delete",
            "project_template_detail.tab_task_templates": "Task Templates",
            "project_template_detail.tab_description": "Description",
            "project_template_detail.create_task_template_button": "Create Task Template",
            "project_template_detail.view": "View",
            "project_template_detail.edit": "Edit",
            "project_template_detail.sidebar_title": "Template details",
            "project_template_detail.roles": "Roles",
            "project_template_detail.created_by": "Created by",
            "project_template_detail.created_at": "Created at",
            "project_template_detail.last_modified_by": "Last modified by",
            "project_template_detail.last_modified_at": "Last modified at",
            "project_template_detail.template_not_found": "Template not found",
            "project_template_detail.deleted_toast": "Template deleted successfully",
            "project_template_detail.delete_error": "Error deleting template: {{error}}",
            "project_template_detail.description_updated_toast": "Description updated successfully",
            "project_template_detail.description_update_error": "Error updating description: {{error}}",
        },
        "fr": {
            "project_template_detail.update_menu_item": "Modifier le modèle",
            "project_template_detail.delete_menu_item": "Supprimer le modèle",
            "project_template_detail.delete_dialog_title": "Supprimer le modèle",
            "project_template_detail.delete_dialog_description": "Êtes-vous sûr de vouloir supprimer ce modèle ? Cette action est irréversible.",
            "project_template_detail.cancel": "Annuler",
            "project_template_detail.delete": "Supprimer",
            "project_template_detail.tab_task_templates": "Modèles de tâches",
            "project_template_detail.tab_description": "Description",
            "project_template_detail.create_task_template_button": "Créer un modèle de tâche",
            "project_template_detail.view": "Afficher",
            "project_template_detail.edit": "Modifier",
            "project_template_detail.sidebar_title": "Détails du modèle",
            "project_template_detail.roles": "Rôles",
            "project_template_detail.created_by": "Créé par",
            "project_template_detail.created_at": "Créé le",
            "project_template_detail.last_modified_by": "Dernière modification par",
            "project_template_detail.last_modified_at": "Dernière modification le",
            "project_template_detail.template_not_found": "Modèle introuvable",
            "project_template_detail.deleted_toast": "Modèle supprimé avec succès",
            "project_template_detail.delete_error": "Erreur lors de la suppression du modèle : {{error}}",
            "project_template_detail.description_updated_toast": "Description mise à jour avec succès",
            "project_template_detail.description_update_error": "Erreur lors de la mise à jour de la description : {{error}}",
        },
    }
)
