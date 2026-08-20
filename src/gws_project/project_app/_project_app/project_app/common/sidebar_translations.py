"""Translations for the sidebar navigation and footer, registered at import time."""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "sidebar.home": "Home",
            "sidebar.projects": "Projects",
            "sidebar.kanban": "Kanban",
            "sidebar.my_work": "My work",
            "sidebar.planning": "Planning",
            "sidebar.companies": "Companies",
            "sidebar.gantt": "Gantt",
            "sidebar.templates": "Templates",
            "sidebar.role_admin": "Admin",
            "sidebar.role_member": "Member",
        },
        "fr": {
            "sidebar.home": "Accueil",
            "sidebar.projects": "Projets",
            "sidebar.kanban": "Kanban",
            "sidebar.my_work": "Mon travail",
            "sidebar.planning": "Planning",
            "sidebar.companies": "Entreprises",
            "sidebar.gantt": "Gantt",
            "sidebar.templates": "Modèles",
            "sidebar.role_admin": "Admin",
            "sidebar.role_member": "Membre",
        },
    }
)
