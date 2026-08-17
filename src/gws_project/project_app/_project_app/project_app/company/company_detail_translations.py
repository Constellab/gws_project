"""Translations for the Company detail page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "company_detail.update_company": "Update Company",
            "company_detail.address": "Address",
            "company_detail.siren": "SIREN",
            "company_detail.phone": "Phone",
            "company_detail.created_by": "Created by",
            "company_detail.created_at": "Created at",
            "company_detail.last_modified_by": "Last modified by",
            "company_detail.last_modified_at": "Last modified at",
            "company_detail.projects_title": "Projects",
            "company_detail.column_title": "Title",
            "company_detail.column_dates": "Dates",
            "company_detail.column_progress": "Progress",
            "company_detail.column_manager": "Manager",
            "company_detail.no_projects": "No projects linked to this company yet.",
            "company_detail.back_to_companies": "← Companies",
        },
        "fr": {
            "company_detail.update_company": "Modifier l'entreprise",
            "company_detail.address": "Adresse",
            "company_detail.siren": "SIREN",
            "company_detail.phone": "Téléphone",
            "company_detail.created_by": "Créé par",
            "company_detail.created_at": "Créé le",
            "company_detail.last_modified_by": "Modifié par",
            "company_detail.last_modified_at": "Modifié le",
            "company_detail.projects_title": "Projets",
            "company_detail.column_title": "Titre",
            "company_detail.column_dates": "Dates",
            "company_detail.column_progress": "Avancement",
            "company_detail.column_manager": "Responsable",
            "company_detail.no_projects": "Aucun projet lié à cette entreprise pour le moment.",
            "company_detail.back_to_companies": "← Entreprises",
        },
    }
)
