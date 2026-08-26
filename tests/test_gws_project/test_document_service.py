import os
from datetime import date, datetime

from gws_core import (
    BadRequestException,
    BaseTestCase,
    RichText,
    RichTextFileService,
    Settings,
    TestMockSpaceService,
)
from PIL import Image

from gws_project.document.document_dto import ProjectDocumentType
from gws_project.document.document_service import DocumentService
from gws_project.document.project_document import (
    PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE,
    ProjectDocument,
)
from gws_project.document.project_file import ProjectFile
from gws_project.project.project import Project
from gws_project.project.project_dto import SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import CreateTaskDTO
from gws_project.task.task_service import TaskService
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_document_service
class TestDocumentService(BaseTestCase):
    """Test suite for the local DocumentService (files and notes)."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _create_project(self) -> Project:
        project_service = ProjectService(TestMockSpaceService())
        return project_service.create_project(
            SaveProjectDTO(
                name="Doc Test Project",
                start_date=datetime(2025, 1, 1),
                due_date=datetime(2025, 12, 31),
            )
        )

    def _create_task(self, project: Project) -> Task:
        task_service = TaskService()
        return task_service.create_root_task(
            project.id,
            CreateTaskDTO(
                title="Doc Test Task",
                start_date=date(2025, 2, 1),
                due_date=date(2025, 2, 28),
            ),
        )

    def _write_temp_file(self, name: str, content: bytes) -> str:
        temp_dir = Settings.make_temp_dir()
        path = os.path.join(temp_dir, name)
        with open(path, "wb") as file_handle:
            file_handle.write(content)
        return path

    def test_file_documents(self):
        """Upload, list, download, rename and delete a file document."""
        document_service = DocumentService()
        project = self._create_project()
        task = self._create_task(project)

        # ========== Upload to project ==========
        file_path = self._write_temp_file("report.pdf", b"pdf-bytes")
        project_doc = document_service.upload_document_to_project(
            project_id=project.id, file_path=file_path, filename="report.pdf"
        )

        self.assertEqual(project_doc.name, "report.pdf")
        self.assertEqual(project_doc.type, ProjectDocumentType.FILE)
        self.assertEqual(project_doc.project_id, project.id)
        self.assertIsNone(project_doc.task_id)
        self.assertEqual(project_doc.size, len(b"pdf-bytes"))
        # the source file was moved into the store
        self.assertFalse(os.path.exists(file_path))

        # ========== Upload to task ==========
        task_file_path = self._write_temp_file("task_doc.txt", b"task-bytes")
        task_doc = document_service.upload_document_to_task(
            task_id=task.id, file_path=task_file_path, filename="task_doc.txt"
        )
        self.assertEqual(task_doc.task_id, task.id)
        self.assertEqual(task_doc.project_id, project.id)

        # ========== Listing: project list excludes task documents ==========
        project_page = document_service.get_project_documents(project.id, page=0, size=20)
        self.assertEqual(project_page.total_number_of_items, 1)
        self.assertEqual(project_page.objects[0].id, project_doc.id)

        task_page = document_service.get_task_documents(task.id, page=0, size=20)
        self.assertEqual(task_page.total_number_of_items, 1)
        self.assertEqual(task_page.objects[0].id, task_doc.id)

        # ========== Download ==========
        downloaded = document_service.download_document_bytes(project_doc.id)
        self.assertEqual(downloaded, b"pdf-bytes")

        # ========== Rename (disk file untouched) ==========
        renamed = document_service.rename_document(project_doc.id, "renamed.pdf")
        self.assertEqual(renamed.name, "renamed.pdf")
        self.assertEqual(document_service.download_document_bytes(project_doc.id), b"pdf-bytes")

        with self.assertRaises(BadRequestException):
            document_service.rename_document(project_doc.id, "   ")

        # ========== Delete: row and disk file are removed ==========
        document = ProjectDocument.get_by_id(project_doc.id)
        disk_path = document.file.get_absolute_path()
        self.assertTrue(os.path.exists(disk_path))

        document_service.delete_document(project_doc.id)

        self.assertIsNone(ProjectDocument.get_by_id(project_doc.id))
        self.assertFalse(os.path.exists(disk_path))

    def test_notes(self):
        """Create, read and update rich-text notes."""
        document_service = DocumentService()
        project = self._create_project()
        task = self._create_task(project)

        # ========== Create notes ==========
        project_note = document_service.create_note_for_project(project.id, "Project Note")
        task_note = document_service.create_note_for_task(task.id, "Task Note")

        self.assertEqual(project_note.type, ProjectDocumentType.NOTE)
        self.assertIsNone(project_note.size)
        self.assertEqual(task_note.task_id, task.id)

        with self.assertRaises(BadRequestException):
            document_service.create_note_for_project(project.id, "  ")

        # ========== Read with content ==========
        note = document_service.get_note(project_note.id)
        self.assertEqual(note.name, "Project Note")
        self.assertIsNotNone(note.content)

        # ========== Update content ==========
        rich_text = RichText()
        rich_text.add_paragraph("Hello note")
        updated = document_service.update_note_content(project_note.id, rich_text.to_dto())
        self.assert_json(updated.content.to_json_dict(), rich_text.to_dto().to_json_dict())

        # ========== Update name ==========
        renamed = document_service.update_note_name(project_note.id, "Renamed Note")
        self.assertEqual(renamed.name, "Renamed Note")
        self.assertEqual(renamed.type, ProjectDocumentType.NOTE)
        # renaming preserves the content
        self.assert_json(renamed.content.to_json_dict(), rich_text.to_dto().to_json_dict())

        with self.assertRaises(BadRequestException):
            document_service.update_note_name(project_note.id, "   ")

        # ========== The mixed list contains the note ==========
        project_page = document_service.get_project_documents(project.id, page=0, size=20)
        self.assertEqual(project_page.total_number_of_items, 1)
        self.assertEqual(project_page.objects[0].type, ProjectDocumentType.NOTE)

        # get_note and update_note_name refuse a FILE document
        file_path = self._write_temp_file("file.txt", b"x")
        file_doc = document_service.upload_document_to_project(project.id, file_path)
        with self.assertRaises(BadRequestException):
            document_service.get_note(file_doc.id)
        with self.assertRaises(BadRequestException):
            document_service.update_note_name(file_doc.id, "Nope")
        with self.assertRaises(BadRequestException):
            document_service.download_document_bytes(project_note.id)

        # ========== Delete a note (no file on disk to clean) ==========
        document_service.delete_document(task_note.id)
        self.assertIsNone(ProjectDocument.get_by_id(task_note.id))
        # the other note is untouched
        self.assertIsNotNone(ProjectDocument.get_by_id(project_note.id))

    def test_delete_project_cleans_files(self):
        """Deleting a project removes its documents and their files on disk."""
        document_service = DocumentService()
        project_service = ProjectService(TestMockSpaceService())
        project = self._create_project()
        task = self._create_task(project)

        project_file = self._write_temp_file("p.txt", b"p")
        task_file = self._write_temp_file("t.txt", b"t")
        project_doc = document_service.upload_document_to_project(project.id, project_file)
        task_doc = document_service.upload_document_to_task(task.id, task_file)
        document_service.create_note_for_project(project.id, "Note")

        disk_paths = [
            ProjectDocument.get_by_id(project_doc.id).file.get_absolute_path(),
            ProjectDocument.get_by_id(task_doc.id).file.get_absolute_path(),
        ]

        project_service.delete_project(project.id)

        self.assertEqual(ProjectDocument.select().count(), 0)
        self.assertEqual(ProjectFile.select().count(), 0)
        for disk_path in disk_paths:
            self.assertFalse(os.path.exists(disk_path))

    def test_delete_task_cleans_files(self):
        """Deleting a task removes its subtree's documents and files on disk."""
        document_service = DocumentService()
        task_service = TaskService()
        project = self._create_project()

        parent_task = task_service.create_root_task(
            project.id,
            CreateTaskDTO(
                title="Parent",
                start_date=date(2025, 2, 1),
                due_date=date(2025, 2, 28),
                allow_subtasks=True,
            ),
        )
        subtask = task_service.create_sub_task(
            parent_task.id,
            CreateTaskDTO(
                title="Child",
                start_date=date(2025, 2, 1),
                due_date=date(2025, 2, 15),
            ),
        )

        sub_file = self._write_temp_file("sub.txt", b"s")
        sub_doc = document_service.upload_document_to_task(subtask.id, sub_file)
        disk_path = ProjectDocument.get_by_id(sub_doc.id).file.get_absolute_path()

        # a project-level document survives the task deletion
        project_file = self._write_temp_file("keep.txt", b"k")
        kept_doc = document_service.upload_document_to_project(project.id, project_file)

        task_service.delete_task(parent_task.id)

        self.assertIsNone(ProjectDocument.get_by_id(sub_doc.id))
        self.assertFalse(os.path.exists(disk_path))
        self.assertIsNotNone(ProjectDocument.get_by_id(kept_doc.id))

    ############################### NOTE IMAGES ###############################

    def _add_note_image(self, note_id: str) -> str:
        """Store an image for a note, like the rich text editor does, and return its path."""
        image = Image.new("RGB", (5, 5), color="blue")
        result = RichTextFileService.save_image(
            PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE, note_id, image, "png"
        )
        image_path = RichTextFileService.get_figure_file_path(
            PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE, note_id, result.filename
        )
        self.assertTrue(os.path.exists(image_path))
        return image_path

    def test_delete_note_cleans_images(self):
        """Deleting a note removes the images of its content."""
        document_service = DocumentService()
        project = self._create_project()

        note = document_service.create_note_for_project(project.id, "Note with image")
        image_path = self._add_note_image(note.id)

        document_service.delete_document(note.id)

        self.assertIsNone(ProjectDocument.get_by_id(note.id))
        self.assertFalse(os.path.exists(image_path))

    def test_delete_project_cleans_note_images(self):
        """Deleting a project removes the images of its notes (project and task level)."""
        document_service = DocumentService()
        project_service = ProjectService(TestMockSpaceService())
        project = self._create_project()
        task = self._create_task(project)

        project_note = document_service.create_note_for_project(project.id, "Project note")
        task_note = document_service.create_note_for_task(task.id, "Task note")
        image_paths = [
            self._add_note_image(project_note.id),
            self._add_note_image(task_note.id),
        ]

        project_service.delete_project(project.id)

        for image_path in image_paths:
            self.assertFalse(os.path.exists(image_path))

    def test_delete_task_cleans_note_images(self):
        """Deleting a task removes the images of its notes, and keeps the other ones."""
        document_service = DocumentService()
        task_service = TaskService()
        project = self._create_project()
        task = self._create_task(project)

        task_note = document_service.create_note_for_task(task.id, "Task note")
        task_image_path = self._add_note_image(task_note.id)

        # a project-level note survives the task deletion, its images must be kept
        kept_note = document_service.create_note_for_project(project.id, "Kept note")
        kept_image_path = self._add_note_image(kept_note.id)

        task_service.delete_task(task.id)

        self.assertIsNone(ProjectDocument.get_by_id(task_note.id))
        self.assertFalse(os.path.exists(task_image_path))
        self.assertTrue(os.path.exists(kept_image_path))
