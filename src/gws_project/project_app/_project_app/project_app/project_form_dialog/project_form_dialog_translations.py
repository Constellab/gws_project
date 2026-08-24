"""Translations for the Project form dialog (create/update). Registered once
at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "project_form_dialog.name_label": "Project Name*",
            "project_form_dialog.error.name_required": "The project name is required",
            "project_form_dialog.error.start_date_required": "The start date is required",
            "project_form_dialog.error.end_date_required": "The end date is required",
            "project_form_dialog.error.missing_roles": (
                "Please assign users to all roles. Missing: {{roles}}"
            ),
            "project_form_dialog.toast.created": "Project created",
            "project_form_dialog.toast.updated": "Project updated",
            "project_form_dialog.name_placeholder": "Enter project name",
            "project_form_dialog.select_user_placeholder": "Select user (required)",
            "project_form_dialog.company_label": "Company (optional)",
            "project_form_dialog.no_company_placeholder": "No company",
            "project_form_dialog.manager_label": "Manager",
            "project_form_dialog.select_manager_placeholder": "Select project manager",
            "project_form_dialog.template_label": "Project Template (Optional)",
            "project_form_dialog.template_placeholder": "Select a template (optional)",
            "project_form_dialog.start_date_label": "Start Date*",
            "project_form_dialog.end_date_label": "End Date*",
            "project_form_dialog.role_assignments_label": "Role Assignments",
            "project_form_dialog.role_assignments_description": (
                "Assign a user to each role. These users will be added to the "
                "project and assigned to the corresponding tasks."
            ),
            "project_form_dialog.update_title": "Update Project",
            "project_form_dialog.create_title": "New Project",
            "project_form_dialog.update_description": "Update the project details below.",
            "project_form_dialog.create_description": "Fill in the details below to create a new project.",
            "project_form_dialog.create_button": "New Project",
        },
        "fr": {
            "project_form_dialog.name_label": "Nom du projet*",
            "project_form_dialog.error.name_required": "Le nom du projet est obligatoire",
            "project_form_dialog.error.start_date_required": "La date de début est obligatoire",
            "project_form_dialog.error.end_date_required": "La date de fin est obligatoire",
            "project_form_dialog.error.missing_roles": (
                "Attribuez un utilisateur à chaque rôle. Manquants : {{roles}}"
            ),
            "project_form_dialog.toast.created": "Projet créé",
            "project_form_dialog.toast.updated": "Projet modifié",
            "project_form_dialog.name_placeholder": "Saisissez le nom du projet",
            "project_form_dialog.select_user_placeholder": "Sélectionner un utilisateur (requis)",
            "project_form_dialog.company_label": "Entreprise (facultatif)",
            "project_form_dialog.no_company_placeholder": "Aucune entreprise",
            "project_form_dialog.manager_label": "Responsable",
            "project_form_dialog.select_manager_placeholder": "Sélectionner le responsable du projet",
            "project_form_dialog.template_label": "Modèle de projet (facultatif)",
            "project_form_dialog.template_placeholder": "Sélectionner un modèle (facultatif)",
            "project_form_dialog.start_date_label": "Date de début*",
            "project_form_dialog.end_date_label": "Date de fin*",
            "project_form_dialog.role_assignments_label": "Attribution des rôles",
            "project_form_dialog.role_assignments_description": (
                "Attribuez un utilisateur à chaque rôle. Ces utilisateurs seront "
                "ajoutés au projet et affectés aux tâches correspondantes."
            ),
            "project_form_dialog.update_title": "Modifier le projet",
            "project_form_dialog.create_title": "Nouveau projet",
            "project_form_dialog.update_description": "Modifiez les détails du projet ci-dessous.",
            "project_form_dialog.create_description": (
                "Renseignez les informations ci-dessous pour créer un nouveau projet."
            ),
            "project_form_dialog.create_button": "Nouveau projet",
        },
    }
)
