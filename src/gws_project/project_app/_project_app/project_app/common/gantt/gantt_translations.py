"""Translations for the shared Gantt chart component. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "gantt_chart.empty_state.title": "No Projects Available",
            "gantt_chart.empty_state.description": "Create a project with tasks to see the Gantt chart.",
        },
        "fr": {
            "gantt_chart.empty_state.title": "Aucun projet disponible",
            "gantt_chart.empty_state.description": "Créez un projet avec des tâches pour afficher le diagramme de Gantt.",
        },
    }
)
