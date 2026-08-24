"""Translations of the task history: the sentence of each event, and the values it names.

A history row is stored language-neutral (see the brick's `task_history_value`), so both
the task's Activity tab and the Home feed build their line from these templates. The
templates are predicates: the component renders the actor's name in front of them, which
is why they read "changed the status..." and not "<name> changed the status...".

`{{task}}` is the wording for the task the event happened on: the Activity tab lists the
events under the task itself ("this task"), while the Home feed names the task on a line
of its own ("the task").
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "task_history.subject.timeline": "this task",
            "task_history.subject.feed": "the task",
            "task_history.created": "created {{task}}",
            "task_history.title_changed": 'renamed {{task}} from "{{old}}" to "{{new}}"',
            "task_history.status_changed": "changed the status from {{old}} to {{new}}",
            "task_history.priority_changed": "changed the priority from {{old}} to {{new}}",
            # The values are ranges holding an arrow themselves, so they are quoted: without
            # it "from A → B to C → D" reads as one long chain of dates.
            "task_history.dates_changed": (
                'changed the dates from "{{old}}" to "{{new}}"'
            ),
            "task_history.assignee_changed": "changed the assignee from {{old}} to {{new}}",
            "task_history.assignee_set": "assigned {{task}} to {{new}}",
            "task_history.assignee_unset": "unassigned {{task}} (was {{old}})",
            "task_history.description_updated": "updated the description",
            # Generic line for an event type with no wording of its own yet.
            "task_history.changed": "updated {{task}}",
            "task_history.moved": "moved {{task}} from {{old}} to {{new}}",
            "task_history.type_changed": "changed {{task}} from {{old}} to {{new}}",
            "task_history.automatic_suffix": "(automatically updated from subtasks)",
            "task_history.status.BACKLOG": "Backlog",
            "task_history.status.TODO": "To do",
            "task_history.status.DOING": "Doing",
            "task_history.status.DONE": "Done",
            "task_history.priority.HIGH": "High",
            "task_history.priority.MEDIUM": "Medium",
            "task_history.priority.LOW": "Low",
            "task_history.task_type.LEAF": "a normal task",
            "task_history.task_type.PARENT": "a task with subtasks",
            # Stands in for a date the event left empty, on either side of a range.
            "task_history.no_date": "—",
        },
        "fr": {
            "task_history.subject.timeline": "cette tâche",
            "task_history.subject.feed": "la tâche",
            "task_history.created": "a créé {{task}}",
            "task_history.title_changed": (
                "a renommé {{task}} de « {{old}} » en « {{new}} »"
            ),
            "task_history.status_changed": "a changé le statut de {{old}} à {{new}}",
            "task_history.priority_changed": "a changé la priorité de {{old}} à {{new}}",
            "task_history.dates_changed": (
                "a changé les dates de « {{old}} » à « {{new}} »"
            ),
            "task_history.assignee_changed": "a changé l'assignation de {{old}} à {{new}}",
            "task_history.assignee_set": "a assigné {{task}} à {{new}}",
            "task_history.assignee_unset": "a désassigné {{task}} (était {{old}})",
            "task_history.description_updated": "a mis à jour la description",
            "task_history.changed": "a modifié {{task}}",
            "task_history.moved": "a déplacé {{task}} de {{old}} vers {{new}}",
            "task_history.type_changed": "a converti {{task}} de {{old}} en {{new}}",
            "task_history.automatic_suffix": (
                "(mis à jour automatiquement depuis les sous-tâches)"
            ),
            "task_history.status.BACKLOG": "Backlog",
            "task_history.status.TODO": "À faire",
            "task_history.status.DOING": "En cours",
            "task_history.status.DONE": "Terminé",
            "task_history.priority.HIGH": "Haute",
            "task_history.priority.MEDIUM": "Moyenne",
            "task_history.priority.LOW": "Basse",
            "task_history.task_type.LEAF": "tâche simple",
            "task_history.task_type.PARENT": "tâche avec sous-tâches",
            "task_history.no_date": "—",
        },
    }
)
