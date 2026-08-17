"""Translations for the Kanban page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "kanban.title": "Task Board",
            "kanban.filters.search_placeholder": "Title",
            "kanban.filters.all_projects": "All Projects",
            "kanban.filters.all_users": "All Users",
            "kanban.filters.all_companies": "All Companies",
            "kanban.filters.date_all": "All",
            "kanban.filters.date_last_week": "Last Week",
            "kanban.filters.date_current_week": "Current Week",
            "kanban.filters.date_next_week": "Next Week",
            "kanban.filters.date_current_month": "Current Month",
            "kanban.filters.show_backlog": "Show Backlog",
            "kanban.filters.clear": "Clear",
        },
        "fr": {
            "kanban.title": "Tableau des tâches",
            "kanban.filters.search_placeholder": "Titre",
            "kanban.filters.all_projects": "Tous les projets",
            "kanban.filters.all_users": "Tous les utilisateurs",
            "kanban.filters.all_companies": "Toutes les entreprises",
            "kanban.filters.date_all": "Toutes",
            "kanban.filters.date_last_week": "Semaine dernière",
            "kanban.filters.date_current_week": "Semaine actuelle",
            "kanban.filters.date_next_week": "Semaine prochaine",
            "kanban.filters.date_current_month": "Mois actuel",
            "kanban.filters.show_backlog": "Afficher le backlog",
            "kanban.filters.clear": "Effacer",
        },
    }
)
