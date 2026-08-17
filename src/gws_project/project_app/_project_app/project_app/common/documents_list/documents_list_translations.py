"""Translations for the Documents list component. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "documents_list.title": "Documents",
            "documents_list.create_note": "Create Note",
            "documents_list.upload_file": "Upload File",
            "documents_list.loading": "Loading documents...",
            "documents_list.loading_short": "Loading...",
            "documents_list.load_more": "Load More",
            "documents_list.empty_state": "No documents found",
            "documents_list.rename_dialog.title": "Rename Document",
            "documents_list.rename_dialog.description": "Enter a new name for the document.",
            "documents_list.rename_dialog.name_label": "Document Name",
            "documents_list.rename_dialog.name_placeholder": "Enter document name",
            "documents_list.rename_dialog.cancel": "Cancel",
            "documents_list.rename_dialog.renaming": "Renaming...",
            "documents_list.rename_dialog.submit": "Rename",
            "documents_list.create_note_dialog.title": "Create Note",
            "documents_list.create_note_dialog.name_label": "Note Name",
            "documents_list.create_note_dialog.name_placeholder": "Enter note name",
            "documents_list.create_note_dialog.cancel": "Cancel",
            "documents_list.create_note_dialog.creating": "Creating...",
            "documents_list.create_note_dialog.submit": "Create",
        },
        "fr": {
            "documents_list.title": "Documents",
            "documents_list.create_note": "Créer une note",
            "documents_list.upload_file": "Importer un fichier",
            "documents_list.loading": "Chargement des documents...",
            "documents_list.loading_short": "Chargement...",
            "documents_list.load_more": "Charger plus",
            "documents_list.empty_state": "Aucun document trouvé",
            "documents_list.rename_dialog.title": "Renommer le document",
            "documents_list.rename_dialog.description": "Saisissez un nouveau nom pour le document.",
            "documents_list.rename_dialog.name_label": "Nom du document",
            "documents_list.rename_dialog.name_placeholder": "Saisissez le nom du document",
            "documents_list.rename_dialog.cancel": "Annuler",
            "documents_list.rename_dialog.renaming": "Renommage...",
            "documents_list.rename_dialog.submit": "Renommer",
            "documents_list.create_note_dialog.title": "Créer une note",
            "documents_list.create_note_dialog.name_label": "Nom de la note",
            "documents_list.create_note_dialog.name_placeholder": "Saisissez le nom de la note",
            "documents_list.create_note_dialog.cancel": "Annuler",
            "documents_list.create_note_dialog.creating": "Création...",
            "documents_list.create_note_dialog.submit": "Créer",
        },
    }
)
