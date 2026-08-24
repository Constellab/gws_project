"""Translations for the Admin page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "admin.title": "Admin",
            "admin.language.title": "Language",
            "admin.roles.title": "Roles",
            "admin.roles.user_column": "User",
            "admin.roles.role_column": "Role",
            "admin.roles.role_admin": "Admin",
            "admin.roles.role_member": "Member",
            "admin.roles.updated": "Role updated",
            "admin.working_hours.title": "Working Hours",
            "admin.working_hours.admin_only": "Only administrators can view and edit working hours.",
            "admin.working_hours.working_days": "Working days",
            "admin.working_hours.weekly_hours": "Weekly working hours (h)",
            "admin.working_hours.invalid_weekly_hours": "Please enter a valid number of hours",
            "admin.working_hours.timezone": "Timezone",
            "admin.working_hours.day_start_time": "Day start",
            "admin.working_hours.day_end_time": "Day end",
            "admin.working_hours.lunch_start_time": "Lunch break start",
            "admin.working_hours.lunch_end_time": "Lunch break end",
            "admin.working_hours.save": "Save",
            "admin.working_hours.saved": "Working hours saved",
            "admin.working_hours.unauthorized": "You are not authorized to edit working hours",
            "admin.day.mon": "Monday",
            "admin.day.tue": "Tuesday",
            "admin.day.wed": "Wednesday",
            "admin.day.thu": "Thursday",
            "admin.day.fri": "Friday",
            "admin.day.sat": "Saturday",
            "admin.day.sun": "Sunday",
        },
        "fr": {
            "admin.title": "Administration",
            "admin.language.title": "Langue",
            "admin.roles.title": "Rôles",
            "admin.roles.user_column": "Utilisateur",
            "admin.roles.role_column": "Rôle",
            "admin.roles.role_admin": "Admin",
            "admin.roles.role_member": "Membre",
            "admin.roles.updated": "Rôle mis à jour",
            "admin.working_hours.title": "Horaires de travail",
            "admin.working_hours.admin_only": "Seuls les administrateurs peuvent consulter et modifier les horaires de travail.",
            "admin.working_hours.working_days": "Jours travaillés",
            "admin.working_hours.weekly_hours": "Heures de travail hebdomadaires (h)",
            "admin.working_hours.invalid_weekly_hours": "Veuillez saisir un nombre d'heures valide",
            "admin.working_hours.timezone": "Fuseau horaire",
            "admin.working_hours.day_start_time": "Début de journée",
            "admin.working_hours.day_end_time": "Fin de journée",
            "admin.working_hours.lunch_start_time": "Début de la pause déjeuner",
            "admin.working_hours.lunch_end_time": "Fin de la pause déjeuner",
            "admin.working_hours.save": "Enregistrer",
            "admin.working_hours.saved": "Horaires de travail enregistrés",
            "admin.working_hours.unauthorized": "Vous n'êtes pas autorisé à modifier les horaires de travail",
            "admin.day.mon": "Lundi",
            "admin.day.tue": "Mardi",
            "admin.day.wed": "Mercredi",
            "admin.day.thu": "Jeudi",
            "admin.day.fri": "Vendredi",
            "admin.day.sat": "Samedi",
            "admin.day.sun": "Dimanche",
        },
    }
)
