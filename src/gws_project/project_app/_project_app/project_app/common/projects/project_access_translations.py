"""Translations for the "project or task not accessible" screen.

See gws_reflex_main's I18nState/translate/register_translations for the underlying
(session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "project_access.not_found.title": "This page no longer exists",
            "project_access.not_found.message": (
                "The project or task you are trying to open was not found. It may have "
                "been deleted, or the link may be out of date."
            ),
            "project_access.no_access.title": "You do not have access to this project",
            "project_access.no_access.message": (
                "You are not a member of the project this page belongs to. Ask one of "
                "its owners to add you to it."
            ),
            "project_access.back_to_projects": "Back to my projects",
        },
        "fr": {
            "project_access.not_found.title": "Cette page n'existe plus",
            "project_access.not_found.message": (
                "Le projet ou la tâche que vous essayez d'ouvrir est introuvable. Il a "
                "peut-être été supprimé, ou le lien n'est plus à jour."
            ),
            "project_access.no_access.title": "Vous n'avez pas accès à ce projet",
            "project_access.no_access.message": (
                "Vous n'êtes pas membre du projet auquel appartient cette page. "
                "Demandez à l'un de ses propriétaires de vous y ajouter."
            ),
            "project_access.back_to_projects": "Retour à mes projets",
        },
    }
)
