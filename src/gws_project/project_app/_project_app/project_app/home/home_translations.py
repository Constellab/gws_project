"""Translations for the Home page, registered at import time."""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "home.quick_access.title": "What would you like to do?",
            "home.quick_access.subtitle": "Pick one to get started.",
            "home.card.my_work.title": "Get on with my work",
            "home.card.my_work.description": (
                "Your day and the tasks assigned to you, across every project."
            ),
            "home.card.projects.title": "Browse my projects",
            "home.card.projects.description": (
                "Open a project to reach its tasks, its notes and its team."
            ),
            "home.card.planning.title": "Plan the team",
            "home.card.planning.description": (
                "Schedule and confirm who works on what, day by day."
            ),
            "home.card.kanban.title": "Move tasks along",
            "home.card.kanban.description": (
                "Every task of every project on one board, sorted by status."
            ),
            # Counts under the cards. Each fragment stands on its own so it reads correctly
            # for any number, without the app needing plural rules.
            "home.stat.my_work.empty": "Nothing on your plate",
            "home.stat.my_work.today": "{{count}} scheduled today",
            "home.stat.my_work.assigned": "{{count}} waiting",
            "home.stat.my_work.overdue": "{{count}} overdue",
            "home.stat.projects.empty": "No project yet",
            "home.stat.projects": "{{ongoing}} ongoing of {{total}}",
            "home.activity.title": "What the team has been doing",
            "home.activity.window": "Last {{days}} days",
            "home.activity.truncated": "Showing the {{count}} most recent only.",
            "home.activity.today": "Today",
            "home.activity.yesterday": "Yesterday",
            "home.activity.commented": "commented",
            "home.activity.commented_with": "commented: {{excerpt}}",
            "home.activity.empty.title": "Nothing new from your colleagues",
            "home.activity.empty.description": (
                "Changes and comments made by the other members of your projects show up "
                "here. Your own are not repeated back to you."
            ),
        },
        "fr": {
            "home.quick_access.title": "Que voulez-vous faire ?",
            "home.quick_access.subtitle": "Choisissez un point de départ.",
            "home.card.my_work.title": "Avancer sur mon travail",
            "home.card.my_work.description": (
                "Votre journée et les tâches qui vous sont assignées, tous projets confondus."
            ),
            "home.card.projects.title": "Parcourir mes projets",
            "home.card.projects.description": (
                "Ouvrez un projet pour accéder à ses tâches, ses notes et son équipe."
            ),
            "home.card.planning.title": "Planifier l'équipe",
            "home.card.planning.description": (
                "Organisez et confirmez qui travaille sur quoi, jour par jour."
            ),
            "home.card.kanban.title": "Faire avancer les tâches",
            "home.card.kanban.description": (
                "Toutes les tâches de tous les projets sur un tableau, par statut."
            ),
            "home.stat.my_work.empty": "Rien à votre programme",
            "home.stat.my_work.today": "{{count}} planifiée(s) aujourd'hui",
            "home.stat.my_work.assigned": "{{count}} en attente",
            "home.stat.my_work.overdue": "{{count}} en retard",
            "home.stat.projects.empty": "Aucun projet",
            "home.stat.projects": "{{ongoing}} en cours sur {{total}}",
            "home.activity.title": "Ce que l'équipe a fait",
            "home.activity.window": "Ces {{days}} derniers jours",
            "home.activity.truncated": "Seules les {{count}} plus récentes sont affichées.",
            "home.activity.today": "Aujourd'hui",
            "home.activity.yesterday": "Hier",
            "home.activity.commented": "a commenté",
            "home.activity.commented_with": "a commenté : {{excerpt}}",
            "home.activity.empty.title": "Rien de nouveau chez vos collègues",
            "home.activity.empty.description": (
                "Les modifications et commentaires des autres membres de vos projets "
                "apparaissent ici. Les vôtres ne vous sont pas répétés."
            ),
        },
    }
)
