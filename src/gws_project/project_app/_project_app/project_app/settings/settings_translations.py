"""Translations for the Settings page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "settings.title": "Settings",
            "settings.language.title": "Language",
            "settings.roles.title": "Roles",
            "settings.roles.user_column": "User",
            "settings.roles.role_column": "Role",
            "settings.roles.role_admin": "Admin",
            "settings.roles.role_member": "Member",
            "settings.roles.updated": "Role updated",
            "settings.working_hours.title": "Working Hours",
            "settings.working_hours.admin_only": "Only administrators can view and edit working hours.",
            "settings.working_hours.working_days": "Working days",
            "settings.working_hours.weekly_hours": "Weekly working hours (h)",
            "settings.working_hours.invalid_weekly_hours": "Please enter a valid number of hours",
            "settings.working_hours.timezone": "Timezone",
            "settings.working_hours.day_start_time": "Day start",
            "settings.working_hours.day_end_time": "Day end",
            "settings.working_hours.lunch_start_time": "Lunch break start",
            "settings.working_hours.lunch_end_time": "Lunch break end",
            "settings.working_hours.save": "Save",
            "settings.working_hours.saved": "Working hours saved",
            "settings.working_hours.unauthorized": "You are not authorized to edit working hours",
            "settings.day.mon": "Monday",
            "settings.day.tue": "Tuesday",
            "settings.day.wed": "Wednesday",
            "settings.day.thu": "Thursday",
            "settings.day.fri": "Friday",
            "settings.day.sat": "Saturday",
            "settings.day.sun": "Sunday",
        },
        "fr": {
            "settings.title": "Paramètres",
            "settings.language.title": "Langue",
            "settings.roles.title": "Rôles",
            "settings.roles.user_column": "Utilisateur",
            "settings.roles.role_column": "Rôle",
            "settings.roles.role_admin": "Admin",
            "settings.roles.role_member": "Membre",
            "settings.roles.updated": "Rôle mis à jour",
            "settings.working_hours.title": "Horaires de travail",
            "settings.working_hours.admin_only": "Seuls les administrateurs peuvent consulter et modifier les horaires de travail.",
            "settings.working_hours.working_days": "Jours travaillés",
            "settings.working_hours.weekly_hours": "Heures de travail hebdomadaires (h)",
            "settings.working_hours.invalid_weekly_hours": "Veuillez saisir un nombre d'heures valide",
            "settings.working_hours.timezone": "Fuseau horaire",
            "settings.working_hours.day_start_time": "Début de journée",
            "settings.working_hours.day_end_time": "Fin de journée",
            "settings.working_hours.lunch_start_time": "Début de la pause déjeuner",
            "settings.working_hours.lunch_end_time": "Fin de la pause déjeuner",
            "settings.working_hours.save": "Enregistrer",
            "settings.working_hours.saved": "Horaires de travail enregistrés",
            "settings.working_hours.unauthorized": "Vous n'êtes pas autorisé à modifier les horaires de travail",
            "settings.day.mon": "Lundi",
            "settings.day.tue": "Mardi",
            "settings.day.wed": "Mercredi",
            "settings.day.thu": "Jeudi",
            "settings.day.fri": "Vendredi",
            "settings.day.sat": "Samedi",
            "settings.day.sun": "Dimanche",
        },
    }
)
