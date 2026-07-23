import os

from gws_core import (
    MessageDispatcher,
    RichText,
    RichTextFileService,
    SpaceService,
)

from gws_project.document.document_dto import ProjectDocumentType
from gws_project.document.project_document import (
    PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE,
    ProjectDocument,
)


class NoteImageMigrationService:
    """Repair the embedded images of notes migrated out of Space.

    The main Space removal migration (:class:`SpaceMigrationService`) was run
    before project notes supported images. It copied each Constellab document's
    rich-text content verbatim into a local NOTE ``ProjectDocument``, so the
    ``FIGURE`` blocks kept their original Space filenames — but the image
    **bytes** were never downloaded into the note's local per-document
    directory (``.../note/project_document/{document_id}/{filename}``, see
    :data:`PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE`). The note editor loads
    figures from that directory, so the migrated images are broken.

    This service downloads the missing figure bytes from Space and writes them
    under each note's directory, keeping the same filename so the content JSON
    (and therefore the figure references) is left untouched.

    It is **idempotent** (a figure whose file already exists on disk is
    skipped, so a note whose images are already present is a no-op),
    **error-resilient** (a per-figure or per-note failure is logged and
    reported but never aborts the run) and **non-destructive** (Space is only
    read from, never written to; the note content is never mutated).

    :param space_service: The SpaceService to use (mockable in tests)
    :type space_service: Optional[SpaceService]
    :param dry_run: If True, only report what would be repaired without
        downloading or writing anything
    :type dry_run: bool
    :param message_dispatcher: Optional dispatcher used to log progress,
        warnings and errors (with tracebacks) as the migration runs
    :type message_dispatcher: Optional[MessageDispatcher]
    """

    _space_service: SpaceService
    _dry_run: bool
    _message_dispatcher: MessageDispatcher

    def __init__(
        self,
        space_service: SpaceService | None = None,
        dry_run: bool = True,
        message_dispatcher: MessageDispatcher | None = None,
    ):
        self._space_service = (
            space_service if space_service is not None else SpaceService("gws-project")
        )
        self._dry_run = dry_run
        self._message_dispatcher = (
            message_dispatcher if message_dispatcher is not None else MessageDispatcher()
        )

    def migrate_all_notes(self) -> dict:
        """Repair the images of every note migrated from Space and return the report.

        Only notes with a ``space_document_id`` are considered: those are the
        ones created by the Space migration whose figure bytes may be missing.
        Notes created locally after the upgrade already store their images on
        disk and are ignored.

        :return: The migration report
        :rtype: dict
        """
        notes: list[ProjectDocument] = list(
            ProjectDocument.select().where(
                (ProjectDocument.type == ProjectDocumentType.NOTE)
                & (ProjectDocument.space_document_id.is_null(False))
            )
        )

        report: dict = {"dry_run": self._dry_run, "notes": []}

        self._message_dispatcher.notify_info_message(
            f"Starting note image repair of {len(notes)} migrated note(s) "
            f"(dry_run={self._dry_run})"
        )

        for note in notes:
            try:
                report["notes"].append(self.migrate_note(note))
            except Exception as err:
                # A note-level failure (e.g. corrupt content) must not abort the
                # whole run: log it, record it and move on.
                self._message_dispatcher.notify_error_message(
                    f"Failed to repair images of note '{note.name}' (id={note.id})",
                    exception=err,
                )
                report["notes"].append(
                    {
                        "document_id": note.id,
                        "name": note.name,
                        "space_document_id": note.space_document_id,
                        "note_error": str(err),
                    }
                )

        report["totals"] = self._compute_totals(report["notes"])
        return report

    def migrate_note(self, note: ProjectDocument) -> dict:
        """Download the missing figure bytes of one migrated note (idempotent).

        :param note: The NOTE document to repair
        :type note: ProjectDocument
        :return: The per-note report entry
        :rtype: dict
        """
        entry: dict = {
            "document_id": note.id,
            "name": note.name,
            "space_document_id": note.space_document_id,
            "project_id": note.project.id,
            "figures_total": 0,
            "figures_repaired": [],
            "figures_already_present": 0,
            "errors": [],
        }

        if not note.content:
            return entry

        rich_text = RichText(note.content)
        figures = rich_text.get_figures_data()
        entry["figures_total"] = len(figures)

        for figure in figures:
            self._migrate_figure(note, figure.filename, entry)

        return entry

    def _migrate_figure(self, note: ProjectDocument, filename: str, entry: dict) -> None:
        """Download one figure image if it is missing locally (idempotent,
        error-resilient).

        :param note: The NOTE document the figure belongs to
        :type note: ProjectDocument
        :param filename: The figure filename as referenced in the content JSON
        :type filename: str
        :param entry: The per-note report entry (mutated in place)
        :type entry: dict
        """
        if not filename:
            entry["errors"].append(
                {"filename": None, "error": "figure block has no filename"}
            )
            return

        try:
            # also validates the filename (must stay inside the note directory)
            target_path = RichTextFileService.get_figure_file_path(
                PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE, note.id, filename
            )

            if os.path.exists(target_path):
                entry["figures_already_present"] += 1
                return

            if self._dry_run:
                entry["figures_repaired"].append(filename)  # would repair
                return

            file_bytes = self._space_service.get_constellab_document_figure(
                note.space_document_id, filename
            )

            RichTextFileService.create_object_dir(
                PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE, note.id
            )
            with open(target_path, "wb") as file_handle:
                file_handle.write(file_bytes)

            entry["figures_repaired"].append(filename)
        except Exception as err:
            self._message_dispatcher.notify_error_message(
                f"Error repairing figure '{filename}' of note '{note.name}' "
                f"(document_id={note.id}, space_document_id={note.space_document_id})",
                exception=err,
            )
            entry["errors"].append({"filename": filename, "error": str(err)})

    def _compute_totals(self, note_entries: list[dict]) -> dict:
        """Aggregate the per-note entries into global totals.

        :param note_entries: The per-note report entries
        :type note_entries: List[dict]
        :return: The totals of the report
        :rtype: dict
        """
        return {
            "notes": len(note_entries),
            "failed_notes": sum(1 for entry in note_entries if "note_error" in entry),
            "figures_total": sum(
                entry.get("figures_total", 0) for entry in note_entries
            ),
            "figures_repaired": sum(
                len(entry.get("figures_repaired", [])) for entry in note_entries
            ),
            "figures_already_present": sum(
                entry.get("figures_already_present", 0) for entry in note_entries
            ),
            "errors": sum(len(entry.get("errors", [])) for entry in note_entries),
        }
