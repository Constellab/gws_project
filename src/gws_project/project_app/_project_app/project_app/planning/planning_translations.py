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
            "planning.add_task.title": "Add a task",
            "planning.add_task.description": "Pick the task to schedule for {{target}}.",
            "planning.add_task.cancel": "Cancel",
            "planning.tasks.search_placeholder": "Search a task, project, person...",
            "planning.tasks.no_result": "No task matches your search.",
            "planning.tasks.help": (
                "Tasks to do and in progress.Backlog and done tasks are not listed."
            ),
            "planning.tasks.help_past_week": (
                "Tasks to do, in progress and done. Backlog tasks are not listed."
            ),
            "planning.warnings.button": "{{count}} warning(s)",
            "planning.warnings.title": "Warnings",
            "planning.warnings.close": "Close",
            "planning.warnings.overload": "Overloaded this week",
            "planning.warnings.overlap": "Overlapping slots",
            "planning.warnings.overdue": "Overdue and not scheduled this week",
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
            "planning.toast.duplicate_failed": ("Failed to duplicate the previous week: {{error}}"),
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
            "planning.add_task.title": "Ajouter une tâche",
            "planning.add_task.description": "Choisissez la tâche à planifier pour {{target}}.",
            "planning.add_task.cancel": "Annuler",
            "planning.tasks.search_placeholder": "Rechercher une tâche, un projet, une personne...",
            "planning.tasks.no_result": "Aucune tâche ne correspond à votre recherche.",
            "planning.tasks.help": (
                "Tâches à faire et en cours. "
                "Les tâches du backlog et terminées ne sont pas listées."
            ),
            "planning.tasks.help_past_week": (
                "Tâches à faire, en cours et terminées. Les tâches du backlog ne sont pas listées."
            ),
            "planning.warnings.button": "{{count}} avertissement(s)",
            "planning.warnings.title": "Avertissements",
            "planning.warnings.close": "Fermer",
            "planning.warnings.overload": "En surcharge cette semaine",
            "planning.warnings.overlap": "Créneaux qui se chevauchent",
            "planning.warnings.overdue": "En retard et non planifiées cette semaine",
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
            "planning.toast.no_person_selected": ("Sélectionnez au moins une personne à dupliquer"),
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
