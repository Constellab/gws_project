"""Translations for the Planning page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "planning.title": "Planning",
            "planning.week.current": "Today",
            "planning.duplicate_previous_week": "Duplicate previous week",
            "planning.filters.all_projects": "All Projects",
            "planning.filters.all_companies": "All Companies",
            "planning.filters.all_users": "All Users",
            "planning.filters.clear": "Clear",
            "planning.banner.reopen": "Show hidden alerts",
            "planning.banner.overload_prefix": "Overloaded this week:",
            "planning.banner.overlap_prefix": "Overlapping slots:",
            "planning.banner.overdue_prefix": "Overdue and not scheduled this week:",
            "planning.due_prefix": "Due",
            "planning.toast.invalid_drop": "Invalid drop data",
            "planning.toast.invalid_move": "Invalid move data",
            "planning.toast.invalid_resize": "Invalid resize data",
            "planning.toast.create_failed": "Failed to create the slot: {{error}}",
            "planning.toast.move_failed": "Failed to move the slot: {{error}}",
            "planning.toast.resize_failed": "Failed to resize the slot: {{error}}",
            "planning.toast.delete_failed": "Failed to delete the slot: {{error}}",
            "planning.toast.load_previous_week_failed": (
                "Failed to load the previous week: {{error}}"
            ),
            "planning.toast.no_person_selected": "Select at least one person to duplicate",
            "planning.toast.duplicated": "{{count}} slot(s) duplicated from last week",
            "planning.toast.duplicate_failed": (
                "Failed to duplicate the previous week: {{error}}"
            ),
            "planning.grid.lunch": "Lunch",
            "planning.grid.scheduled": "Scheduled",
            "planning.duplicate.title": "Duplicate previous week",
            "planning.duplicate.description": "Choose which people's slots to duplicate into this week.",
            "planning.duplicate.cancel": "Cancel",
            "planning.duplicate.confirm": "Duplicate",
            "planning.duplicate.no_slots": "No slots were planned last week.",
        },
        "fr": {
            "planning.title": "Planning",
            "planning.week.current": "Aujourd'hui",
            "planning.duplicate_previous_week": "Dupliquer la semaine précédente",
            "planning.filters.all_projects": "Tous les projets",
            "planning.filters.all_companies": "Toutes les entreprises",
            "planning.filters.all_users": "Tous les utilisateurs",
            "planning.filters.clear": "Effacer",
            "planning.banner.reopen": "Afficher les alertes masquées",
            "planning.banner.overload_prefix": "En surcharge cette semaine :",
            "planning.banner.overlap_prefix": "Créneaux qui se chevauchent :",
            "planning.banner.overdue_prefix": "En retard et non planifiées cette semaine :",
            "planning.due_prefix": "Échéance",
            "planning.toast.invalid_drop": "Données de dépôt invalides",
            "planning.toast.invalid_move": "Données de déplacement invalides",
            "planning.toast.invalid_resize": "Données de redimensionnement invalides",
            "planning.toast.create_failed": "Échec de la création du créneau : {{error}}",
            "planning.toast.move_failed": "Échec du déplacement du créneau : {{error}}",
            "planning.toast.resize_failed": "Échec du redimensionnement du créneau : {{error}}",
            "planning.toast.delete_failed": "Échec de la suppression du créneau : {{error}}",
            "planning.toast.load_previous_week_failed": (
                "Échec du chargement de la semaine précédente : {{error}}"
            ),
            "planning.toast.no_person_selected": (
                "Sélectionnez au moins une personne à dupliquer"
            ),
            "planning.toast.duplicated": (
                "{{count}} créneau(x) dupliqué(s) depuis la semaine dernière"
            ),
            "planning.toast.duplicate_failed": (
                "Échec de la duplication de la semaine précédente : {{error}}"
            ),
            "planning.grid.lunch": "Déjeuner",
            "planning.grid.scheduled": "Planifié",
            "planning.duplicate.title": "Dupliquer la semaine précédente",
            "planning.duplicate.description": "Choisissez les personnes dont les créneaux doivent être dupliqués sur cette semaine.",
            "planning.duplicate.cancel": "Annuler",
            "planning.duplicate.confirm": "Dupliquer",
            "planning.duplicate.no_slots": "Aucun créneau n'a été planifié la semaine précédente.",
        },
    }
)
