import os
from datetime import datetime

from gws_core import (
    BaseTestCase,
    RichText,
    RichTextFileService,
    TestMockSpaceService,
)
from gws_core.impl.rich_text.block.rich_text_block_figure import RichTextBlockFigure
from gws_project.document.document_dto import ProjectDocumentType
from gws_project.document.document_service import DocumentService
from gws_project.document.note_image_migration_service import NoteImageMigrationService
from gws_project.document.project_document import (
    PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE,
    ProjectDocument,
)
from gws_project.project.project import Project
from gws_project.project.project_dto import SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.user.project_user_sync_service import ProjectUserSyncService

# bytes returned by the mocked Space figure download
_FIGURE_BYTES = b"fake-png-bytes"


# test_note_image_migration
class TestNoteImageMigration(BaseTestCase):
    """Test suite for the MigrateNoteImagesFromSpace repair logic."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        ProjectUserSyncService().sync_all_users()

    def _create_project(self) -> Project:
        return ProjectService(TestMockSpaceService()).create_project(
            SaveProjectDTO(
                name="Note Image Project",
                start_date=datetime(2025, 1, 1),
                due_date=datetime(2025, 12, 31),
            )
        )

    def _figure(self, filename: str) -> RichTextBlockFigure:
        return RichTextBlockFigure(
            filename=filename,
            width=5,
            height=5,
            naturalWidth=5,
            naturalHeight=5,
        )

    def _create_migrated_note(
        self, project: Project, space_document_id: str, filenames: list[str]
    ) -> ProjectDocument:
        """Create a NOTE that mimics one migrated from Space: content with
        figure blocks referencing filenames, but no image bytes on disk."""
        rich_text = RichText()
        rich_text.add_paragraph("Migrated note")
        for filename in filenames:
            rich_text.add_figure(self._figure(filename))

        note = ProjectDocument(
            project=project,
            task=None,
            type=ProjectDocumentType.NOTE,
            name="Migrated note",
            content=rich_text.to_dto(),
            space_document_id=space_document_id,
        )
        note.save()
        return note

    def _mock_space(
        self, figures: dict[tuple[str, str], bytes]
    ) -> TestMockSpaceService:
        """A mock Space serving the given figure bytes, keyed by
        (space_document_id, filename)."""
        mock_space = TestMockSpaceService()
        for (document_id, filename), content in figures.items():
            mock_space.set_constellab_document_figure_mock(document_id, filename, content)
        return mock_space

    def _figure_path(self, note_id: str, filename: str) -> str:
        return RichTextFileService.get_figure_file_path(
            PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE, note_id, filename
        )

    def test_repair(self):
        """Dry run first, then real repair, then idempotent re-run."""
        project = self._create_project()
        note = self._create_migrated_note(
            project, "space-note-1", ["fig_a.png", "fig_b.png"]
        )
        mock_space = self._mock_space(
            {
                ("space-note-1", "fig_a.png"): _FIGURE_BYTES,
                ("space-note-1", "fig_b.png"): _FIGURE_BYTES,
            }
        )

        # ========== Dry run: nothing written ==========
        dry_report = NoteImageMigrationService(
            space_service=mock_space, dry_run=True
        ).migrate_all_notes()

        self.assertTrue(dry_report["dry_run"])
        self.assertEqual(dry_report["totals"]["notes"], 1)
        self.assertEqual(dry_report["totals"]["figures_total"], 2)
        self.assertEqual(dry_report["totals"]["figures_repaired"], 2)
        self.assertEqual(dry_report["totals"]["errors"], 0)
        # dry run writes nothing to disk
        self.assertFalse(os.path.exists(self._figure_path(note.id, "fig_a.png")))

        # ========== Real run ==========
        report = NoteImageMigrationService(
            space_service=mock_space, dry_run=False
        ).migrate_all_notes()

        self.assertEqual(report["totals"]["figures_repaired"], 2)
        self.assertEqual(report["totals"]["figures_already_present"], 0)
        self.assertEqual(report["totals"]["errors"], 0)
        # the bytes were downloaded and written under the note directory
        for filename in ["fig_a.png", "fig_b.png"]:
            path = self._figure_path(note.id, filename)
            self.assertTrue(os.path.exists(path))
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), _FIGURE_BYTES)

        # ========== Idempotent re-run: images already present ==========
        rerun_report = NoteImageMigrationService(
            space_service=mock_space, dry_run=False
        ).migrate_all_notes()

        self.assertEqual(rerun_report["totals"]["figures_repaired"], 0)
        self.assertEqual(rerun_report["totals"]["figures_already_present"], 2)

    def test_repair_error_resilience(self):
        """A per-figure download error is reported and does not abort the run."""
        project = self._create_project()
        note = self._create_migrated_note(
            project, "space-note-2", ["ok.png", "broken.png"]
        )
        # only "ok.png" has bytes; the missing "broken.png" makes the mock raise
        mock_space = self._mock_space({("space-note-2", "ok.png"): _FIGURE_BYTES})

        report = NoteImageMigrationService(
            space_service=mock_space, dry_run=False
        ).migrate_all_notes()

        self.assertEqual(report["totals"]["figures_repaired"], 1)
        self.assertEqual(report["totals"]["errors"], 1)
        # the good figure was still written
        self.assertTrue(os.path.exists(self._figure_path(note.id, "ok.png")))
        self.assertFalse(os.path.exists(self._figure_path(note.id, "broken.png")))
        note_entry = report["notes"][0]
        self.assertEqual(note_entry["errors"][0]["filename"], "broken.png")

    def test_local_notes_are_ignored(self):
        """Notes without a space_document_id (created locally) are not touched."""
        project = self._create_project()
        DocumentService().create_note_for_project(project.id, "Local note")

        report = NoteImageMigrationService(
            space_service=self._mock_space({}), dry_run=False
        ).migrate_all_notes()

        self.assertEqual(report["totals"]["notes"], 0)
