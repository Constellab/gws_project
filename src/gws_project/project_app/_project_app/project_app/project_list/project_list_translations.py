"""Translations for the Project List page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "project_list.title": "My projects",
            "project_list.search_placeholder": "Search projects...",
            "project_list.all_managers": "All Managers",
            "project_list.all_companies": "All Companies",
            "project_list.clear": "Clear",
            "project_list.column_title": "Title",
            "project_list.column_company": "Company",
            "project_list.column_dates": "Dates",
            "project_list.column_progress": "Progress",
            "project_list.column_manager": "Manager",
            "project_list.empty_state": "No projects found",
        },
        "fr": {
            "project_list.title": "Mes projets",
            "project_list.search_placeholder": "Rechercher des projets...",
            "project_list.all_managers": "Tous les responsables",
            "project_list.all_companies": "Toutes les entreprises",
            "project_list.clear": "Effacer",
            "project_list.column_title": "Titre",
            "project_list.column_company": "Entreprise",
            "project_list.column_dates": "Dates",
            "project_list.column_progress": "Progression",
            "project_list.column_manager": "Responsable",
            "project_list.empty_state": "Aucun projet trouvé",
        },
    }
)
