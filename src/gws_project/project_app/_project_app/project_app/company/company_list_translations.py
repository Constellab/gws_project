"""Translations for the Company list page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "company_list.title": "Companies",
            "company_list.search_placeholder": "Search companies...",
            "company_list.all_statuses": "All Statuses",
            "company_list.clear": "Clear",
            "company_list.column_name": "Name",
            "company_list.column_phone": "Phone",
            "company_list.column_address": "Address",
            "company_list.empty": "No companies found",
        },
        "fr": {
            "company_list.title": "Entreprises",
            "company_list.search_placeholder": "Rechercher des entreprises...",
            "company_list.all_statuses": "Tous les statuts",
            "company_list.clear": "Effacer",
            "company_list.column_name": "Nom",
            "company_list.column_phone": "Téléphone",
            "company_list.column_address": "Adresse",
            "company_list.empty": "Aucune entreprise trouvée",
        },
    }
)
