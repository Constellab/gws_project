from datetime import date, datetime

from gws_core import (
    BaseTestCase,
    PageDTO,
    RichText,
    TestMockSpaceService,
)
from gws_core.space.space_dto import SpaceHierarchyObjectDTO
from gws_project.document.document_dto import ProjectDocumentType
from gws_project.document.document_service import DocumentService
from gws_project.document.project_document import ProjectDocument
from gws_project.document.space_migration_service import SpaceMigrationService
from gws_project.project.project import Project
from gws_project.project.project_dto import SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import CreateTaskDTO
from gws_project.task.task_service import TaskService
from gws_project.user.project_user_sync_service import ProjectUserSyncService


class MockSpaceServiceWithFolders(TestMockSpaceService):
    """Space mock exposing in-memory folder contents for the migration tests.

    Folder contents are registered with `add_folder_object(folder_id, object,
    tags)`; the tag filter of the search params is honored like the real route.
    """

    def __init__(self):
        super().__init__()
        # folder_id -> list of (SpaceHierarchyObjectDTO, tags: list[dict])
        self._folder_objects: dict[str, list[tuple[SpaceHierarchyObjectDTO, list[dict]]]] = {}
        self._document_bytes: dict[str, bytes] = {}

    def add_folder_object(
        self,
        folder_id: str,
        space_object: SpaceHierarchyObjectDTO,
        tags: list[dict] | None = None,
        content: bytes | None = None,
    ):
        self._folder_objects.setdefault(folder_id, []).append((space_object, tags or []))
        if content is not None:
            self._document_bytes[space_object.id] = content

    def search_project_children_objects_paginated(self, folder_id, search_params, page, size):
        objects = self._folder_objects.get(folder_id, [])

        # honor the tag EQ filter used by the migration
        tag_criteria = search_params.get_filter_criteria("tags")
        if tag_criteria is not None:
            objects = [(obj, tags) for (obj, tags) in objects if tag_criteria.value in tags]

        # single page is enough for tests (fewer than the migration page size)
        page_objects = [obj for (obj, _) in objects] if page == 0 else []
        return PageDTO.empty_page().with_objects(page_objects)

    def download_document_bytes(self, document_id: str, filename: str | None = None) -> bytes:
        return self._document_bytes[document_id]


def _space_object(id_: str, name: str, object_type: str, size: int | None = None):
    return SpaceHierarchyObjectDTO(
        id=id_,
        name=name,
        objectType=object_type,
        parentId=None,
        documentSize=size,
        lastModifiedAt=datetime(2025, 1, 1),
    )


# test_space_migration
class TestSpaceMigration(BaseTestCase):
    """Test suite for the MigrateProjectDataFromSpace logic."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _setup_project(self) -> tuple[Project, Task, Task, MockSpaceServiceWithFolders, dict]:
        """Create a project + root task + subtask with legacy Space folders and
        a mock Space populated with documents. Returns the Space object ids in
        a dict (ids are unique per setup because tests share the database)."""
        project_service = ProjectService(TestMockSpaceService())
        task_service = TaskService()

        project = project_service.create_project(
            SaveProjectDTO(
                name="Legacy Project",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 12, 31),
            )
        )
        # keep within the 36-char space_folder_id column
        project_folder_id = f"fp-{project.id[:8]}"
        project.space_folder_id = project_folder_id
        project.save()

        root_task = task_service.create_root_task(
            project.id,
            CreateTaskDTO(
                title="Root Task",
                start_date=date(2025, 2, 1),
                end_date=date(2025, 2, 28),
                allow_subtasks=True,
            ),
        )
        subtask = task_service.create_sub_task(
            root_task.id,
            CreateTaskDTO(
                title="Subtask",
                start_date=date(2025, 2, 1),
                end_date=date(2025, 2, 15),
            ),
        )
        task_folder_id = f"ft-{root_task.id[:8]}"
        root_task.space_folder_id = task_folder_id
        root_task.save()

        mock_space = MockSpaceServiceWithFolders()

        uid = project.id[:8]
        ids = {
            "file": f"space-doc-1-{uid}",
            "note": f"space-note-1-{uid}",
            "scenario": f"space-scn-1-{uid}",
            "subtask_file": f"space-doc-2-{uid}",
            "orphan_file": f"space-doc-3-{uid}",
        }

        # project folder: one file, one Constellab document, one scenario link
        mock_space.add_folder_object(
            project_folder_id,
            _space_object(ids["file"], "report.pdf", "DOCUMENT", size=9),
            content=b"pdf-bytes",
        )
        mock_space.add_folder_object(
            project_folder_id,
            _space_object(ids["note"], "Meeting notes", "CONSTELLAB_DOCUMENT"),
        )
        mock_space.add_folder_object(
            project_folder_id,
            _space_object(ids["scenario"], "Analysis", "SCENARIO"),
        )

        # root task folder: one file tagged for the subtask, one orphan file
        # (tag pointing to a deleted task)
        mock_space.add_folder_object(
            task_folder_id,
            _space_object(ids["subtask_file"], "subtask_doc.txt", "DOCUMENT", size=4),
            tags=[{"key": "task", "value": subtask.id}],
            content=b"data",
        )
        mock_space.add_folder_object(
            task_folder_id,
            _space_object(ids["orphan_file"], "orphan.txt", "DOCUMENT", size=6),
            tags=[{"key": "task", "value": "deleted-task-id"}],
            content=b"orphan",
        )

        # Constellab document content
        rich_text = RichText()
        rich_text.add_paragraph("Migrated note content")
        mock_space.set_constellab_document_content_mock(ids["note"], rich_text.to_dto())

        return project, root_task, subtask, mock_space, ids

    def test_migration(self):
        """Dry run first, then real migration, then idempotent re-run."""
        project, root_task, subtask, mock_space, ids = self._setup_project()

        # ========== Dry run: full report, nothing written ==========
        dry_report = SpaceMigrationService(
            space_service=mock_space, dry_run=True
        ).migrate_all_projects()

        self.assertTrue(dry_report["dry_run"])
        self.assertEqual(dry_report["totals"]["projects"], 1)
        self.assertEqual(dry_report["totals"]["migrated_files"], 3)
        self.assertEqual(dry_report["totals"]["migrated_notes"], 1)
        self.assertEqual(dry_report["totals"]["skipped"], 1)
        self.assertEqual(dry_report["totals"]["orphans"], 1)
        self.assertEqual(dry_report["totals"]["errors"], 0)
        self.assertEqual(dry_report["totals"]["total_bytes"], 9 + 4 + 6)
        self.assertEqual(ProjectDocument.select().count(), 0)

        # ========== Real run ==========
        report = SpaceMigrationService(
            space_service=mock_space, dry_run=False
        ).migrate_all_projects()

        self.assertEqual(report["totals"]["migrated_files"], 3)
        self.assertEqual(report["totals"]["migrated_notes"], 1)
        self.assertEqual(report["totals"]["errors"], 0)
        self.assertEqual(ProjectDocument.select().count(), 4)

        # project-level file
        project_doc = ProjectDocument.get(ProjectDocument.space_document_id == ids["file"])
        self.assertEqual(project_doc.type, ProjectDocumentType.FILE)
        self.assertEqual(project_doc.project.id, project.id)
        self.assertIsNone(project_doc.task)
        document_service = DocumentService()
        self.assertEqual(document_service.download_document_bytes(project_doc.id), b"pdf-bytes")

        # note converted from the Constellab document
        note_doc = ProjectDocument.get(ProjectDocument.space_document_id == ids["note"])
        self.assertEqual(note_doc.type, ProjectDocumentType.NOTE)
        self.assertIsNotNone(note_doc.content)
        note_dto = document_service.get_note(note_doc.id)
        self.assertEqual(note_dto.name, "Meeting notes")

        # subtask document attached to the EXACT subtask
        subtask_doc = ProjectDocument.get(ProjectDocument.space_document_id == ids["subtask_file"])
        self.assertEqual(subtask_doc.task.id, subtask.id)

        # orphan attached to the root task
        orphan_doc = ProjectDocument.get(ProjectDocument.space_document_id == ids["orphan_file"])
        self.assertEqual(orphan_doc.task.id, root_task.id)
        project_entry = next(
            entry for entry in report["projects"] if entry["project_id"] == project.id
        )
        self.assertEqual(len(project_entry["orphans"]), 1)
        self.assertEqual(project_entry["orphans"][0]["id"], ids["orphan_file"])

        # the scenario link is skipped and reported
        self.assertEqual(project_entry["skipped"][0]["type"], "SCENARIO")

        # ========== Idempotent re-run: everything already migrated ==========
        rerun_report = SpaceMigrationService(
            space_service=mock_space, dry_run=False
        ).migrate_all_projects()

        self.assertEqual(rerun_report["totals"]["migrated_files"], 0)
        self.assertEqual(rerun_report["totals"]["migrated_notes"], 0)
        self.assertEqual(rerun_report["totals"]["already_migrated"], 4)
        self.assertEqual(rerun_report["totals"]["orphans"], 0)
        self.assertEqual(ProjectDocument.select().count(), 4)

    def test_migration_error_resilience(self):
        """A per-document error is reported and does not abort the run."""
        project, root_task, subtask, mock_space, ids = self._setup_project()

        # make one download fail by removing its bytes
        del mock_space._document_bytes[ids["file"]]

        report = SpaceMigrationService(
            space_service=mock_space, dry_run=False
        ).migrate_all_projects()

        self.assertEqual(report["totals"]["errors"], 1)
        # the other documents were still migrated
        self.assertEqual(report["totals"]["migrated_files"], 2)
        self.assertEqual(report["totals"]["migrated_notes"], 1)
        project_entry = next(
            entry for entry in report["projects"] if entry["project_id"] == project.id
        )
        self.assertEqual(project_entry["errors"][0]["id"], ids["file"])

    def test_migration_folder_listing_resilience(self):
        """A Space listing failure is reported and does not abort the run.

        Named to sort after ``test_migration`` because ``BaseTestCase`` wipes the
        DB per class (not per method): the project created here would otherwise
        leak into ``test_migration``'s global-count assertions.
        """
        project, root_task, subtask, mock_space, ids = self._setup_project()

        # make every Space listing raise (e.g. Space API unreachable)
        def raise_error(*args, **kwargs):
            raise Exception("Space API unreachable")

        mock_space.search_project_children_objects_paginated = raise_error

        report = SpaceMigrationService(
            space_service=mock_space, dry_run=False
        ).migrate_all_projects()

        # the run completed and the project was still processed (not aborted)
        project_entry = next(
            entry for entry in report["projects"] if entry["project_id"] == project.id
        )
        self.assertNotIn("project_error", project_entry)
        self.assertEqual(len(project_entry["migrated_files"]), 0)
        self.assertEqual(len(project_entry["migrated_notes"]), 0)
        # each failed listing is recorded as an error with its folder id
        self.assertGreater(len(project_entry["errors"]), 0)
        self.assertIn("folder_id", project_entry["errors"][0])
