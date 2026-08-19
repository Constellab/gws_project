"""Translations for the portfolio Gantt chart. Registered once at import time.

``gantt_chart.locale`` is not a label but the BCP 47 tag handed to the chart, which uses it
for every date it renders as well as for the month names on the time axis.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "gantt_chart.locale": "en-GB",
            "gantt_chart.column_project": "Project / task",
            "gantt_chart.column_meta": "Period · progress",
            "gantt_chart.group_late": "Late",
            "gantt_chart.group_ongoing": "Ongoing",
            "gantt_chart.group_done": "Completed",
            "gantt_chart.project_one": "project",
            "gantt_chart.project_many": "projects",
            "gantt_chart.task_one": "task",
            "gantt_chart.task_many": "tasks",
            "gantt_chart.late_by": "{n} days late",
            "gantt_chart.done": "complete",
            "gantt_chart.empty": "No project matches the filters.",
        },
        "fr": {
            "gantt_chart.locale": "fr-FR",
            "gantt_chart.column_project": "Projet / tâche",
            "gantt_chart.column_meta": "Période · avancement",
            "gantt_chart.group_late": "En retard",
            "gantt_chart.group_ongoing": "En cours",
            "gantt_chart.group_done": "Terminé",
            "gantt_chart.project_one": "projet",
            "gantt_chart.project_many": "projets",
            "gantt_chart.task_one": "tâche",
            "gantt_chart.task_many": "tâches",
            "gantt_chart.late_by": "En retard de {n} j",
            "gantt_chart.done": "réalisé",
            "gantt_chart.empty": "Aucun projet ne correspond aux filtres.",
        },
    }
)
