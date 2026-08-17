"""Translations for the Task Activity tab. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "task_activity.edited": "(edited)",
            "task_activity.cancel": "Cancel",
            "task_activity.save": "Save",
            "task_activity.comment_button": "Comment",
            "task_activity.no_activity": "No activity yet",
        },
        "fr": {
            "task_activity.edited": "(modifié)",
            "task_activity.cancel": "Annuler",
            "task_activity.save": "Enregistrer",
            "task_activity.comment_button": "Commenter",
            "task_activity.no_activity": "Aucune activité pour le moment",
        },
    }
)
