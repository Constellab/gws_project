"""Translations for the Project User form dialog. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "project_user_form.group_label": "Group",
            "project_user_form.select_group_placeholder": "Select a group",
            "project_user_form.role_label": "Role",
            "project_user_form.select_role_placeholder": "Select a role",
            "project_user_form.update_title": "Update Group Role",
            "project_user_form.add_title": "Add Group to Project",
            "project_user_form.update_description": "Update the role of {{first_name}} {{last_name}}.",
            "project_user_form.add_description": "Select a group and assign them a role in this project.",
            "project_user_form.error.group_required": "Please select a group",
            "project_user_form.error.role_required": "Please select a role",
            "project_user_form.error.invalid_role": "Invalid role: {{role}}",
            "project_user_form.toast.added": "Added to the project",
            "project_user_form.toast.role_updated": "Group role updated",
        },
        "fr": {
            "project_user_form.group_label": "Groupe",
            "project_user_form.select_group_placeholder": "Sélectionner un groupe",
            "project_user_form.role_label": "Rôle",
            "project_user_form.select_role_placeholder": "Sélectionner un rôle",
            "project_user_form.update_title": "Modifier le rôle du groupe",
            "project_user_form.add_title": "Ajouter un groupe au projet",
            "project_user_form.update_description": "Modifier le rôle de {{first_name}} {{last_name}}.",
            "project_user_form.add_description": "Sélectionnez un groupe et attribuez-lui un rôle dans ce projet.",
            "project_user_form.error.group_required": "Sélectionnez un groupe",
            "project_user_form.error.role_required": "Sélectionnez un rôle",
            "project_user_form.error.invalid_role": "Rôle invalide : {{role}}",
            "project_user_form.toast.added": "Ajouté au projet",
            "project_user_form.toast.role_updated": "Rôle du groupe modifié",
        },
    }
)
