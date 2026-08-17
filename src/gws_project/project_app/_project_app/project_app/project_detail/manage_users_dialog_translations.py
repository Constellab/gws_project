"""Translations for the Manage Users dialog. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "manage_users.update_role": "Update Role",
            "manage_users.remove_from_project": "Remove from Project",
            "manage_users.user_column": "User",
            "manage_users.role_column": "Role",
            "manage_users.actions_column": "Actions",
            "manage_users.title": "Manage Project Members",
            "manage_users.add_user": "Add User",
            "manage_users.description": "View and manage users for this project.",
            "manage_users.no_members_found": "No team members found.",
            "manage_users.close": "Close",
        },
        "fr": {
            "manage_users.update_role": "Modifier le rôle",
            "manage_users.remove_from_project": "Retirer du projet",
            "manage_users.user_column": "Utilisateur",
            "manage_users.role_column": "Rôle",
            "manage_users.actions_column": "Actions",
            "manage_users.title": "Gérer les membres du projet",
            "manage_users.add_user": "Ajouter un utilisateur",
            "manage_users.description": "Consultez et gérez les utilisateurs de ce projet.",
            "manage_users.no_members_found": "Aucun membre d'équipe trouvé.",
            "manage_users.close": "Fermer",
        },
    }
)
