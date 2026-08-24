"""Translations for the Project Detail page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "project_detail.create_task": "Create Task",
            "project_detail.view": "View",
            "project_detail.edit": "Edit",
            "project_detail.create_note": "Create Note",
            "project_detail.upload_file": "Upload File",
            "project_detail.update_project": "Update Project",
            "project_detail.manage_users": "Manage Users",
            "project_detail.delete_project": "Delete Project",
            "project_detail.delete_dialog.title": "Delete project",
            "project_detail.delete_dialog.content": (
                "Are you sure you want to delete this project? Its tasks, documents and "
                "notes will be permanently deleted. This action cannot be undone."
            ),
            "project_detail.toast.deleted": "Project deleted",
            "project_detail.tasks_tab": "Tasks",
            "project_detail.description_tab": "Description",
            "project_detail.documents_tab": "Documents",
            "project_detail.details_label": "Project details",
            "project_detail.manager": "Manager",
            "project_detail.company": "Company",
            "project_detail.dates": "Dates",
            "project_detail.members": "Members",
            "project_detail.no_team_members": "No team members",
            "project_detail.created_by": "Created by",
            "project_detail.created_at": "Created at",
            "project_detail.last_modified_by": "Last modified by",
            "project_detail.last_modified_at": "Last modified at",
        },
        "fr": {
            "project_detail.create_task": "Créer une tâche",
            "project_detail.view": "Voir",
            "project_detail.edit": "Modifier",
            "project_detail.create_note": "Créer une note",
            "project_detail.upload_file": "Importer un fichier",
            "project_detail.update_project": "Modifier le projet",
            "project_detail.manage_users": "Gérer les utilisateurs",
            "project_detail.delete_project": "Supprimer le projet",
            "project_detail.delete_dialog.title": "Supprimer le projet",
            "project_detail.delete_dialog.content": (
                "Voulez-vous vraiment supprimer ce projet ? Ses tâches, ses documents et "
                "ses notes seront définitivement supprimés. Cette action est irréversible."
            ),
            "project_detail.toast.deleted": "Projet supprimé",
            "project_detail.tasks_tab": "Tâches",
            "project_detail.description_tab": "Description",
            "project_detail.documents_tab": "Documents",
            "project_detail.details_label": "Détails du projet",
            "project_detail.manager": "Responsable",
            "project_detail.company": "Entreprise",
            "project_detail.dates": "Dates",
            "project_detail.members": "Membres",
            "project_detail.no_team_members": "Aucun membre d'équipe",
            "project_detail.created_by": "Créé par",
            "project_detail.created_at": "Créé le",
            "project_detail.last_modified_by": "Modifié par",
            "project_detail.last_modified_at": "Modifié le",
        },
    }
)
