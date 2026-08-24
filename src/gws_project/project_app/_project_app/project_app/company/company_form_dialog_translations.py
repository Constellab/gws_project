"""Translations for the Company create/update form dialog. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "company_form_dialog.status_label": "Status",
            "company_form_dialog.error.name_required": "The company name is required",
            "company_form_dialog.toast.created": "Company created",
            "company_form_dialog.toast.updated": "Company updated",
            "company_form_dialog.logo_label": "Logo",
            "company_form_dialog.upload_logo": "Upload logo",
            "company_form_dialog.name_label": "Company Name*",
            "company_form_dialog.name_placeholder": "Enter company name",
            "company_form_dialog.address_label": "Address",
            "company_form_dialog.address_placeholder": "Enter company address",
            "company_form_dialog.siren_label": "Registration (SIREN)",
            "company_form_dialog.siren_placeholder": "9 digit SIREN",
            "company_form_dialog.phone_label": "Phone",
            "company_form_dialog.phone_placeholder": "Enter phone number",
            "company_form_dialog.new_company": "New Company",
            "company_form_dialog.update_company": "Update Company",
            "company_form_dialog.description_update": "Update the company details below.",
            "company_form_dialog.description_create": (
                "Fill in the details below to create a new company."
            ),
        },
        "fr": {
            "company_form_dialog.status_label": "Statut",
            "company_form_dialog.error.name_required": "Le nom de l'entreprise est obligatoire",
            "company_form_dialog.toast.created": "Entreprise créée",
            "company_form_dialog.toast.updated": "Entreprise modifiée",
            "company_form_dialog.logo_label": "Logo",
            "company_form_dialog.upload_logo": "Téléverser le logo",
            "company_form_dialog.name_label": "Nom de l'entreprise*",
            "company_form_dialog.name_placeholder": "Saisissez le nom de l'entreprise",
            "company_form_dialog.address_label": "Adresse",
            "company_form_dialog.address_placeholder": "Saisissez l'adresse de l'entreprise",
            "company_form_dialog.siren_label": "Immatriculation (SIREN)",
            "company_form_dialog.siren_placeholder": "SIREN à 9 chiffres",
            "company_form_dialog.phone_label": "Téléphone",
            "company_form_dialog.phone_placeholder": "Saisissez le numéro de téléphone",
            "company_form_dialog.new_company": "Nouvelle entreprise",
            "company_form_dialog.update_company": "Modifier l'entreprise",
            "company_form_dialog.description_update": (
                "Modifiez les informations de l'entreprise ci-dessous."
            ),
            "company_form_dialog.description_create": (
                "Renseignez les informations ci-dessous pour créer une nouvelle entreprise."
            ),
        },
    }
)
