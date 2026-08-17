"""Translations for the task list page (filter bar and list states), registered at import time."""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "task_list.search_placeholder": "Search tasks...",
            "task_list.all_statuses": "All Statuses",
            "task_list.all_priorities": "All Priorities",
            "task_list.all_assignees": "All Assignees",
            "task_list.clear": "Clear",
            "task_list.loading": "Loading tasks...",
            "task_list.empty": "No tasks found",
        },
        "fr": {
            "task_list.search_placeholder": "Rechercher des tâches...",
            "task_list.all_statuses": "Tous les statuts",
            "task_list.all_priorities": "Toutes les priorités",
            "task_list.all_assignees": "Tous les assignés",
            "task_list.clear": "Effacer",
            "task_list.loading": "Chargement des tâches...",
            "task_list.empty": "Aucune tâche trouvée",
        },
    }
)
