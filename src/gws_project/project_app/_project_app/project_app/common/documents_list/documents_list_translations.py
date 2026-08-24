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
            "documents_list.delete_dialog.title": "Delete document",
            "documents_list.delete_dialog.content": (
                "Are you sure you want to permanently delete '{{name}}'? "
                "This action cannot be undone."
            ),
            "documents_list.toast.no_target": "No project or task selected",
            "documents_list.toast.no_file": "No file selected",
            "documents_list.toast.upload_failed": "Failed to upload {{name}}: {{error}}",
            "documents_list.toast.upload_success_one": "File uploaded",
            "documents_list.toast.upload_success_many": "{{count}} files uploaded",
            "documents_list.toast.upload_partial_failure": "{{count}} file(s) failed to upload",
            "documents_list.toast.name_empty": "The document name cannot be empty",
            "documents_list.toast.rename_success": "Document renamed",
            "documents_list.toast.rename_failed": "Failed to rename the document: {{error}}",
            "documents_list.toast.download_failed": "Failed to download the document: {{error}}",
            "documents_list.toast.delete_success": "Document deleted",
            "documents_list.toast.delete_failed": "Failed to delete the document: {{error}}",
            "documents_list.toast.note_name_empty": "The note name cannot be empty",
            "documents_list.toast.note_created": "Note created",
            "documents_list.toast.note_failed": "Failed to create the note: {{error}}",
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
            "documents_list.delete_dialog.title": "Supprimer le document",
            "documents_list.delete_dialog.content": (
                "Voulez-vous vraiment supprimer définitivement '{{name}}' ? "
                "Cette action est irréversible."
            ),
            "documents_list.toast.no_target": "Aucun projet ni tâche sélectionné",
            "documents_list.toast.no_file": "Aucun fichier sélectionné",
            "documents_list.toast.upload_failed": "Échec de l'import de {{name}} : {{error}}",
            "documents_list.toast.upload_success_one": "Fichier importé",
            "documents_list.toast.upload_success_many": "{{count}} fichiers importés",
            "documents_list.toast.upload_partial_failure": "{{count}} fichier(s) n'ont pas pu être importés",
            "documents_list.toast.name_empty": "Le nom du document ne peut pas être vide",
            "documents_list.toast.rename_success": "Document renommé",
            "documents_list.toast.rename_failed": "Échec du renommage du document : {{error}}",
            "documents_list.toast.download_failed": "Échec du téléchargement du document : {{error}}",
            "documents_list.toast.delete_success": "Document supprimé",
            "documents_list.toast.delete_failed": "Échec de la suppression du document : {{error}}",
            "documents_list.toast.note_name_empty": "Le nom de la note ne peut pas être vide",
            "documents_list.toast.note_created": "Note créée",
            "documents_list.toast.note_failed": "Échec de la création de la note : {{error}}",
        },
    }
)
