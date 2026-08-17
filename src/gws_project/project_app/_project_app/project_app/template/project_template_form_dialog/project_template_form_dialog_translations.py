"""Translations for the project template create/update dialog. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "project_template_form_dialog.name_label": "Template Name*",
            "project_template_form_dialog.name_placeholder": "Enter template name",
            "project_template_form_dialog.create_title": "Create New Template",
            "project_template_form_dialog.update_title": "Update Template",
            "project_template_form_dialog.create_description": "Fill in the details below to create a new template.",
            "project_template_form_dialog.update_description": "Update the template details below.",
            "project_template_form_dialog.name_required": "Template name is required",
            "project_template_form_dialog.created_toast": "Template created successfully",
            "project_template_form_dialog.updated_toast": "Template updated successfully",
        },
        "fr": {
            "project_template_form_dialog.name_label": "Nom du modèle*",
            "project_template_form_dialog.name_placeholder": "Saisissez le nom du modèle",
            "project_template_form_dialog.create_title": "Créer un nouveau modèle",
            "project_template_form_dialog.update_title": "Modifier le modèle",
            "project_template_form_dialog.create_description": "Renseignez les informations ci-dessous pour créer un nouveau modèle.",
            "project_template_form_dialog.update_description": "Modifiez les informations du modèle ci-dessous.",
            "project_template_form_dialog.name_required": "Le nom du modèle est requis",
            "project_template_form_dialog.created_toast": "Modèle créé avec succès",
            "project_template_form_dialog.updated_toast": "Modèle mis à jour avec succès",
        },
    }
)
