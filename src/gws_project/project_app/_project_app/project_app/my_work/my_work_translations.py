"""Translations for the My work page, registered at import time."""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "my_work.title": "My work",
            "my_work.due_prefix": "Due",
            "my_work.other_assignee": "{{name}}'s task",
            "my_work.reorder": "Drag to reorder your day",
            "my_work.day.planned": "{{hours}}h {{minutes}} planned",
            "my_work.day.planned_hours": "{{hours}}h planned",
            "my_work.day.planned_minutes": "{{minutes}} min planned",
            "my_work.day.nothing_planned": "Nothing planned",
            "my_work.day.empty": "Nothing scheduled today",
            "my_work.day.over_capacity": "Beyond the {{capacity}}h of a working day.",
            "my_work.rest.title": "Assigned to me, not on today's schedule",
            "my_work.rest.scheduled": "scheduled {{when}}",
            "my_work.rest.complete": "Mark as done",
            "my_work.rest.add_to_day": "Add to my day",
            "my_work.rest.day_full": "Your working day is full - rearrange today's schedule from the Planning",
            "my_work.rest.empty": "Nothing else assigned to you",
            "my_work.empty.title": "Nothing on your plate",
            "my_work.empty.description": "Tasks land here when someone assigns them to you, and slots when someone schedules your time.",
            "my_work.empty.link": "Open the task board",
            "my_work.toast.added": "Added to your day",
            "my_work.toast.completed": "Task completed",
        },
        "fr": {
            "my_work.title": "Mon travail",
            "my_work.due_prefix": "Échéance",
            "my_work.other_assignee": "tâche de {{name}}",
            "my_work.reorder": "Glisser pour réordonner votre journée",
            "my_work.day.planned": "{{hours}} h {{minutes}} planifiées",
            "my_work.day.planned_hours": "{{hours}} h planifiées",
            "my_work.day.planned_minutes": "{{minutes}} min planifiées",
            "my_work.day.nothing_planned": "Rien de planifié",
            "my_work.day.empty": "Rien de planifié aujourd'hui",
            "my_work.day.over_capacity": "Au-delà des {{capacity}} h d'une journée ouvrée.",
            "my_work.rest.title": "Assignées à moi, pas au programme du jour",
            "my_work.rest.scheduled": "planifiée {{when}}",
            "my_work.rest.complete": "Marquer comme terminé",
            "my_work.rest.add_to_day": "Ajouter à ma journée",
            "my_work.rest.day_full": "Votre journée ouvrée est complète - réorganisez le planning du jour depuis le Planning",
            "my_work.rest.empty": "Rien d'autre ne vous est assigné",
            "my_work.empty.title": "Rien à votre programme",
            "my_work.empty.description": "Les tâches arrivent ici lorsqu'on vous les assigne, et les créneaux lorsqu'on planifie votre temps.",
            "my_work.empty.link": "Ouvrir le tableau des tâches",
            "my_work.toast.added": "Ajoutée à votre journée",
            "my_work.toast.completed": "Tâche terminée",
        },
    }
)
