"""Translations for the Note detail page. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "note_detail.actions.rename": "Rename",
            "note_detail.delete_dialog.title": "Delete note",
            "note_detail.delete_dialog.content": (
                "Are you sure you want to permanently delete '{{name}}'? "
                "This action cannot be undone."
            ),
            "note_detail.toast.name_empty": "The note name cannot be empty",
            "note_detail.toast.renamed": "Note renamed",
            "note_detail.toast.rename_failed": "Failed to rename the note: {{error}}",
            "note_detail.toast.deleted": "Note deleted",
            "note_detail.actions.delete": "Delete",
            "note_detail.rename_dialog.title": "Rename Note",
            "note_detail.rename_dialog.name_label": "Note Name",
            "note_detail.rename_dialog.name_placeholder": "Enter note name",
            "note_detail.rename_dialog.cancel": "Cancel",
            "note_detail.rename_dialog.renaming": "Renaming...",
            "note_detail.rename_dialog.submit": "Rename",
            "note_detail.sidebar.title": "Note details",
            "note_detail.sidebar.created_by": "Created by",
            "note_detail.sidebar.created_at": "Created at",
            "note_detail.sidebar.last_modified_by": "Last modified by",
            "note_detail.sidebar.last_modified_at": "Last modified at",
        },
        "fr": {
            "note_detail.actions.rename": "Renommer",
            "note_detail.delete_dialog.title": "Supprimer la note",
            "note_detail.delete_dialog.content": (
                "Voulez-vous vraiment supprimer définitivement '{{name}}' ? "
                "Cette action est irréversible."
            ),
            "note_detail.toast.name_empty": "Le nom de la note ne peut pas être vide",
            "note_detail.toast.renamed": "Note renommée",
            "note_detail.toast.rename_failed": "Échec du renommage de la note : {{error}}",
            "note_detail.toast.deleted": "Note supprimée",
            "note_detail.actions.delete": "Supprimer",
            "note_detail.rename_dialog.title": "Renommer la note",
            "note_detail.rename_dialog.name_label": "Nom de la note",
            "note_detail.rename_dialog.name_placeholder": "Saisissez le nom de la note",
            "note_detail.rename_dialog.cancel": "Annuler",
            "note_detail.rename_dialog.renaming": "Renommage...",
            "note_detail.rename_dialog.submit": "Renommer",
            "note_detail.sidebar.title": "Détails de la note",
            "note_detail.sidebar.created_by": "Créé par",
            "note_detail.sidebar.created_at": "Créé le",
            "note_detail.sidebar.last_modified_by": "Dernière modification par",
            "note_detail.sidebar.last_modified_at": "Dernière modification le",
        },
    }
)
