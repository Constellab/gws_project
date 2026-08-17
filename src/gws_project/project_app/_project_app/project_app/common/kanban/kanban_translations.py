"""Translations for the shared Kanban board component. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "kanban_board.column.backlog": "Backlog",
            "kanban_board.column.todo": "To Do",
            "kanban_board.column.doing": "In Progress",
            "kanban_board.column.done": "Done",
            "kanban_board.card.unassigned": "Unassigned",
        },
        "fr": {
            "kanban_board.column.backlog": "Backlog",
            "kanban_board.column.todo": "À faire",
            "kanban_board.column.doing": "En cours",
            "kanban_board.column.done": "Terminé",
            "kanban_board.card.unassigned": "Non assigné",
        },
    }
)
