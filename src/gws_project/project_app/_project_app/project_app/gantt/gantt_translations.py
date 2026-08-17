"""Translations for the Gantt page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "gantt.title": "Project Timeline",
            "gantt.filter.search_placeholder": "Search project title...",
            "gantt.filter.all_managers": "All Managers",
            "gantt.filter.all_companies": "All Companies",
            "gantt.filter.clear": "Clear",
            "gantt.view_mode.day": "Day",
            "gantt.view_mode.week": "Week",
            "gantt.view_mode.month": "Month",
            "gantt.view_mode.year": "Year",
            "gantt.empty_state.title": "No Projects Available",
            "gantt.empty_state.description": "Create a project with tasks to see the Gantt chart.",
        },
        "fr": {
            "gantt.title": "Chronologie des projets",
            "gantt.filter.search_placeholder": "Rechercher un titre de projet...",
            "gantt.filter.all_managers": "Tous les responsables",
            "gantt.filter.all_companies": "Toutes les entreprises",
            "gantt.filter.clear": "Effacer",
            "gantt.view_mode.day": "Jour",
            "gantt.view_mode.week": "Semaine",
            "gantt.view_mode.month": "Mois",
            "gantt.view_mode.year": "Année",
            "gantt.empty_state.title": "Aucun projet disponible",
            "gantt.empty_state.description": "Créez un projet avec des tâches pour afficher le diagramme de Gantt.",
        },
    }
)
