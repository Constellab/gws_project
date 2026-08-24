"""Translations for the Task Form dialog. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "task_form.role_user_select_placeholder": "Select user (required)",
            "task_form.error.title_required": "The task title is required",
            "task_form.error.start_date_required": "The start date is required",
            "task_form.error.missing_roles": "Please assign users to all roles. Missing: {{roles}}",
            "task_form.toast.task_created": "Task created",
            "task_form.toast.subtask_created": "Subtask created",
            "task_form.toast.task_updated": "Task updated",
            "task_form.toast.tasks_added_from_template": "Tasks added from the template",
            "task_form.template.label": "Task Template (Optional)",
            "task_form.template.placeholder": "Select a template (optional)",
            "task_form.title_field.label": "Task Title*",
            "task_form.title_field.placeholder": "Enter task title",
            "task_form.assign_to.label": "Assign To",
            "task_form.assign_to.placeholder": "Select a user (default to yourself)",
            "task_form.task_type.label": "Task Type*",
            "task_form.task_type.single": "📋 Single task",
            "task_form.task_type.with_subtasks": "📁 Task with subtasks",
            "task_form.start_date.label": "Start Date",
            "task_form.end_date.label": "End Date",
            "task_form.status.label": "Status*",
            "task_form.priority.label": "Priority*",
            "task_form.auto_calc_message": (
                "Dates, status, and priority are automatically calculated from all "
                "descendant tasks."
            ),
            "task_form.template_start_date.label": "Start Date*",
            "task_form.role_assignments.label": "Role Assignments",
            "task_form.role_assignments.description": (
                "Assign a project member to each role. These users will be assigned "
                "to the corresponding tasks."
            ),
            "task_form.title.update": "Update Task",
            "task_form.title.create_sub": "Create New Subtask",
            "task_form.title.create_root": "Create New Task",
        },
        "fr": {
            "task_form.role_user_select_placeholder": "Sélectionner un utilisateur (requis)",
            "task_form.error.title_required": "Le titre de la tâche est obligatoire",
            "task_form.error.start_date_required": "La date de début est obligatoire",
            "task_form.error.missing_roles": "Attribuez un utilisateur à chaque rôle. Manquants : {{roles}}",
            "task_form.toast.task_created": "Tâche créée",
            "task_form.toast.subtask_created": "Sous-tâche créée",
            "task_form.toast.task_updated": "Tâche modifiée",
            "task_form.toast.tasks_added_from_template": "Tâches ajoutées depuis le modèle",
            "task_form.template.label": "Modèle de tâche (facultatif)",
            "task_form.template.placeholder": "Sélectionner un modèle (facultatif)",
            "task_form.title_field.label": "Titre de la tâche*",
            "task_form.title_field.placeholder": "Saisir le titre de la tâche",
            "task_form.assign_to.label": "Assigner à",
            "task_form.assign_to.placeholder": "Sélectionner un utilisateur (vous par défaut)",
            "task_form.task_type.label": "Type de tâche*",
            "task_form.task_type.single": "📋 Tâche simple",
            "task_form.task_type.with_subtasks": "📁 Tâche avec sous-tâches",
            "task_form.start_date.label": "Date de début",
            "task_form.end_date.label": "Date de fin",
            "task_form.status.label": "Statut*",
            "task_form.priority.label": "Priorité*",
            "task_form.auto_calc_message": (
                "Les dates, le statut et la priorité sont automatiquement calculés "
                "à partir de toutes les tâches descendantes."
            ),
            "task_form.template_start_date.label": "Date de début*",
            "task_form.role_assignments.label": "Attribution des rôles",
            "task_form.role_assignments.description": (
                "Attribuez un membre du projet à chaque rôle. Ces utilisateurs seront "
                "assignés aux tâches correspondantes."
            ),
            "task_form.title.update": "Modifier la tâche",
            "task_form.title.create_sub": "Créer une nouvelle sous-tâche",
            "task_form.title.create_root": "Créer une nouvelle tâche",
        },
    }
)
