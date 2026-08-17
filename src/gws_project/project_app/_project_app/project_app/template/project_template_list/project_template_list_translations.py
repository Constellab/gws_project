"""Translations for the project template list page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "project_template_list.title": "Templates",
            "project_template_list.column_name": "Name",
            "project_template_list.column_created_by": "Created By",
            "project_template_list.column_created_at": "Created At",
            "project_template_list.empty_title": "No templates found",
            "project_template_list.empty_subtitle": "Create your first template to get started",
            "project_template_list.error_unauthenticated": "You must be authenticated to view templates",
            "project_template_list.error_loading": "Error loading templates: {{error}}",
            "project_template_list.error_deleting": "Error deleting template: {{error}}",
        },
        "fr": {
            "project_template_list.title": "Modèles",
            "project_template_list.column_name": "Nom",
            "project_template_list.column_created_by": "Créé par",
            "project_template_list.column_created_at": "Créé le",
            "project_template_list.empty_title": "Aucun modèle trouvé",
            "project_template_list.empty_subtitle": "Créez votre premier modèle pour commencer",
            "project_template_list.error_unauthenticated": "Vous devez être authentifié pour consulter les modèles",
            "project_template_list.error_loading": "Erreur lors du chargement des modèles : {{error}}",
            "project_template_list.error_deleting": "Erreur lors de la suppression du modèle : {{error}}",
        },
    }
)
