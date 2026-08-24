"""Translations shared by the task actions available on several screens.

The same confirmation dialogs and toasts back the task list, the task detail page and
the task actions menu, so their texts live here rather than being duplicated in each
module's own translation file.

See gws_reflex_main's I18nState/translate/register_translations for the underlying
(session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "task_actions.toast.not_found": "Task not found",
            "task_actions.toast.type_changed": "Task type changed",
            "task_actions.toast.deleted": "Task deleted",
            "task_actions.convert_to_leaf.title": "Convert to normal task",
            "task_actions.convert_to_leaf.content": (
                "Are you sure you want to convert this task to a normal task? "
                "Status, priority, dates and progress will become manually managed."
            ),
            "task_actions.convert_to_parent.title": "Convert to task with subtasks",
            "task_actions.convert_to_parent.content": (
                "Are you sure you want to convert this task to a task with subtasks? "
                "Status, priority, dates and progress will be automatically calculated "
                "from subtasks."
            ),
            "task_actions.delete.title": "Delete task",
            "task_actions.delete.content": "Are you sure you want to delete this task?",
            "task_actions.delete.descendants_warning": (
                "This will also delete all its descendants (subtasks, sub-subtasks, etc.)."
            ),
            "task_actions.delete.documents_warning": (
                "Its documents and notes will be permanently deleted."
            ),
            "task_actions.delete.descendants_documents_warning": (
                "This will also permanently delete all its descendants (subtasks, "
                "sub-subtasks, etc.) and their documents and notes."
            ),
        },
        "fr": {
            "task_actions.toast.not_found": "Tâche introuvable",
            "task_actions.toast.type_changed": "Type de tâche modifié",
            "task_actions.toast.deleted": "Tâche supprimée",
            "task_actions.convert_to_leaf.title": "Convertir en tâche simple",
            "task_actions.convert_to_leaf.content": (
                "Voulez-vous vraiment convertir cette tâche en tâche simple ? Le statut, "
                "la priorité, les dates et l'avancement devront être gérés manuellement."
            ),
            "task_actions.convert_to_parent.title": "Convertir en tâche avec sous-tâches",
            "task_actions.convert_to_parent.content": (
                "Voulez-vous vraiment convertir cette tâche en tâche avec sous-tâches ? "
                "Le statut, la priorité, les dates et l'avancement seront calculés à "
                "partir des sous-tâches."
            ),
            "task_actions.delete.title": "Supprimer la tâche",
            "task_actions.delete.content": "Voulez-vous vraiment supprimer cette tâche ?",
            "task_actions.delete.descendants_warning": (
                "Toutes ses descendantes (sous-tâches, sous-sous-tâches, etc.) seront "
                "également supprimées."
            ),
            "task_actions.delete.documents_warning": (
                "Ses documents et ses notes seront définitivement supprimés."
            ),
            "task_actions.delete.descendants_documents_warning": (
                "Toutes ses descendantes (sous-tâches, sous-sous-tâches, etc.) ainsi que "
                "leurs documents et leurs notes seront définitivement supprimés."
            ),
        },
    }
)
