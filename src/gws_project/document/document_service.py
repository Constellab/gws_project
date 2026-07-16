import os

from gws_core import (
    BadRequestException,
    NotFoundException,
    PageDTO,
    Paginator,
    RichText,
    RichTextDTO,
    RichTextFileService,
)
from gws_core.impl.file.local_file_store import LocalFileStore

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.document.document_dto import (
    ProjectDocumentDTO,
    ProjectDocumentType,
    ProjectNoteDTO,
)
from gws_project.document.project_config import ProjectConfig
from gws_project.document.project_document import (
    PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE,
    ProjectDocument,
)
from gws_project.document.project_file import ProjectFile
from gws_project.project.project import Project
from gws_project.project.project_security_service import ProjectSecurityService, ProjectUserRole
from gws_project.task.task import Task


class DocumentService:
    """Service class for managing documents (files and notes) of projects and tasks.

    All storage is local: uploaded files live in the brick's dedicated
    ``LocalFileStore`` (registered as ``ProjectFile`` rows) and rich-text notes
    live in the ``ProjectDocument.content`` column. Space is not involved.
    """

    def get_store(self) -> LocalFileStore:
        """Return the brick's dedicated LocalFileStore (find-or-create).

        :return: The dedicated LocalFileStore
        :rtype: LocalFileStore
        """
        return ProjectConfig.get_instance().get_or_create_file_store()

    ################################ LISTING ################################

    def get_project_documents(
        self, project_id: str, page: int, size: int
    ) -> PageDTO[ProjectDocumentDTO]:
        """Get the documents (files and notes) attached directly to a project.

        :param project_id: The ID of the project
        :type project_id: str
        :param page: The page number (0-indexed)
        :type page: int
        :param size: Number of items per page
        :type size: int
        :return: Paginated list of documents of the project
        :rtype: PageDTO[ProjectDocumentDTO]
        """
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        paginator: Paginator[ProjectDocument] = Paginator(
            ProjectDocument.get_project_documents_query(project.id),
            page=page,
            nb_of_items_per_page=size,
        )
        return paginator.map_page(lambda document: document.to_dto())

    def get_task_documents(
        self, task_id: str, page: int, size: int
    ) -> PageDTO[ProjectDocumentDTO]:
        """Get the documents (files and notes) attached to a task.

        :param task_id: The ID of the task
        :type task_id: str
        :param page: The page number (0-indexed)
        :type page: int
        :param size: Number of items per page
        :type size: int
        :return: Paginated list of documents of the task
        :rtype: PageDTO[ProjectDocumentDTO]
        """
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        paginator: Paginator[ProjectDocument] = Paginator(
            ProjectDocument.get_task_documents_query(task.id),
            page=page,
            nb_of_items_per_page=size,
        )
        return paginator.map_page(lambda document: document.to_dto())

    ################################ UPLOAD ################################

    @ProjectDbManager.transaction()
    def upload_document_to_project(
        self, project_id: str, file_path: str, filename: str | None = None
    ) -> ProjectDocumentDTO:
        """Upload a document file to a project.

        :param project_id: The ID of the project
        :type project_id: str
        :param file_path: The path to the file to upload (the file is MOVED into the store)
        :type file_path: str
        :param filename: Optional custom filename for the uploaded document
        :type filename: Optional[str]
        :return: The created document
        :rtype: ProjectDocumentDTO
        """
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        document = self._create_file_document(
            project=project, task=None, file_path=file_path, filename=filename
        )
        return document.to_dto()

    @ProjectDbManager.transaction()
    def upload_document_to_task(
        self, task_id: str, file_path: str, filename: str | None = None
    ) -> ProjectDocumentDTO:
        """Upload a document file to a task.

        :param task_id: The ID of the task
        :type task_id: str
        :param file_path: The path to the file to upload (the file is MOVED into the store)
        :type file_path: str
        :param filename: Optional custom filename for the uploaded document
        :type filename: Optional[str]
        :return: The created document
        :rtype: ProjectDocumentDTO
        """
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        document = self._create_file_document(
            project=task.project, task=task, file_path=file_path, filename=filename
        )
        return document.to_dto()

    ################################ NOTES ################################

    @ProjectDbManager.transaction()
    def create_note_for_project(self, project_id: str, name: str) -> ProjectDocumentDTO:
        """Create an empty rich-text note attached to a project.

        :param project_id: The ID of the project
        :type project_id: str
        :param name: The name of the note
        :type name: str
        :return: The created note
        :rtype: ProjectDocumentDTO
        """
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        return self._create_note(project=project, task=None, name=name).to_dto()

    @ProjectDbManager.transaction()
    def create_note_for_task(self, task_id: str, name: str) -> ProjectDocumentDTO:
        """Create an empty rich-text note attached to a task.

        :param task_id: The ID of the task
        :type task_id: str
        :param name: The name of the note
        :type name: str
        :return: The created note
        :rtype: ProjectDocumentDTO
        """
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        return self._create_note(project=task.project, task=task, name=name).to_dto()

    def get_note(self, document_id: str) -> ProjectNoteDTO:
        """Get a note with its rich-text content.

        :param document_id: The ID of the note document
        :type document_id: str
        :return: The note with content
        :rtype: ProjectNoteDTO
        """
        document = self._get_and_check_document(document_id)

        if document.type != ProjectDocumentType.NOTE:
            raise BadRequestException("The document is not a note.")

        return document.to_note_dto()

    @ProjectDbManager.transaction()
    def update_note_name(self, document_id: str, name: str) -> ProjectNoteDTO:
        """Update the name (title) of a note.

        :param document_id: The ID of the note document
        :type document_id: str
        :param name: The new name for the note
        :type name: str
        :return: The updated note
        :rtype: ProjectNoteDTO
        :raises BadRequestException: If the document is not a note or the name is empty
        """
        if not name or not name.strip():
            raise BadRequestException("Note name cannot be empty")

        document = self._get_and_check_document(document_id)

        if document.type != ProjectDocumentType.NOTE:
            raise BadRequestException("The document is not a note.")

        document.name = name.strip()
        document.save()

        return document.to_note_dto()

    @ProjectDbManager.transaction()
    def update_note_content(self, document_id: str, content: RichTextDTO) -> ProjectNoteDTO:
        """Update the rich-text content of a note.

        :param document_id: The ID of the note document
        :type document_id: str
        :param content: The new rich-text content
        :type content: RichTextDTO
        :return: The updated note
        :rtype: ProjectNoteDTO
        """
        document = self._get_and_check_document(document_id)

        if document.type != ProjectDocumentType.NOTE:
            raise BadRequestException("The document is not a note.")

        document.content = content
        document.save()

        return document.to_note_dto()

    ################################ DOWNLOAD / RENAME / DELETE ################################

    def download_document_bytes(self, document_id: str) -> bytes:
        """Download a file document as bytes.

        :param document_id: The ID of the document to download
        :type document_id: str
        :return: The document bytes
        :rtype: bytes
        """
        document = self._get_and_check_document(document_id)

        if document.type != ProjectDocumentType.FILE or not document.file:
            raise BadRequestException("The document is not a file.")

        absolute_path = document.file.get_absolute_path()
        if not absolute_path or not os.path.exists(absolute_path):
            raise NotFoundException(
                f"The file of document '{document.name}' was not found in the file store."
            )

        with open(absolute_path, "rb") as file_handle:
            return file_handle.read()

    @ProjectDbManager.transaction()
    def rename_document(self, document_id: str, name: str) -> ProjectDocumentDTO:
        """Rename a document (file or note). Only the DB row is renamed, the
        file on disk is untouched.

        :param document_id: The ID of the document to rename
        :type document_id: str
        :param name: The new name for the document
        :type name: str
        :return: The renamed document
        :rtype: ProjectDocumentDTO
        """
        if not name or not name.strip():
            raise BadRequestException("Document name cannot be empty")

        document = self._get_and_check_document(document_id)

        document.name = name.strip()
        document.save()

        return document.to_dto()

    def delete_document(self, document_id: str) -> None:
        """Delete a document. For files, the file node is also removed from the
        store. This is a HARD delete: there is no trash, the document cannot be
        recovered.

        :param document_id: The ID of the document to delete
        :type document_id: str
        """
        self._delete_document_db(document_id)

        # if the transaction is successful, delete the images in the file system
        self._delete_documents_images([document_id])

    @ProjectDbManager.transaction()
    def _delete_document_db(self, document_id: str) -> None:
        """Delete a document and its file node in the database.

        :param document_id: The ID of the document to delete
        :type document_id: str
        """
        document = self._get_and_check_document(document_id)

        self._delete_document_and_file(document)

    def delete_documents_of_project(self, project: Project) -> None:
        """Delete all documents of a project (including its tasks' documents),
        their file nodes and their rich-text images. Called before deleting a
        project, because the DB CASCADE removes the rows but not the files on disk.

        :param project: The project being deleted
        :type project: Project
        """
        document_ids = [
            self._delete_document_and_file(document)
            for document in ProjectDocument.get_documents_of_project_and_subtree(project.id)
        ]

        self._delete_documents_images(document_ids)

    def delete_documents_of_tasks(self, tasks: list[Task]) -> None:
        """Delete all documents of the given tasks, their file nodes and their
        rich-text images. Called before deleting a task subtree, because the DB
        CASCADE removes the rows but not the files on disk.

        :param tasks: The tasks being deleted
        :type tasks: List[Task]
        """
        task_ids = [task.id for task in tasks]
        if not task_ids:
            return

        documents = list(ProjectDocument.select().where(ProjectDocument.task.in_(task_ids)))
        document_ids = [self._delete_document_and_file(document) for document in documents]

        self._delete_documents_images(document_ids)

    ################################ MIGRATION HELPERS ################################

    @ProjectDbManager.transaction()
    def create_migrated_file_document(
        self,
        project: Project,
        task: Task | None,
        file_path: str,
        name: str,
        space_document_id: str,
    ) -> ProjectDocument:
        """Create a FILE document from a file downloaded from Space (migration
        task only, no permission check).

        :param project: The project the document belongs to
        :type project: Project
        :param task: The task the document belongs to (None for project-level)
        :type task: Optional[Task]
        :param file_path: The path of the downloaded file (MOVED into the store)
        :type file_path: str
        :param name: The document name
        :type name: str
        :param space_document_id: The id of the Space document (idempotency)
        :type space_document_id: str
        :return: The created document
        :rtype: ProjectDocument
        """
        return self._create_file_document(
            project=project,
            task=task,
            file_path=file_path,
            filename=name,
            space_document_id=space_document_id,
        )

    @ProjectDbManager.transaction()
    def create_migrated_note(
        self,
        project: Project,
        task: Task | None,
        name: str,
        content: RichTextDTO,
        space_document_id: str,
    ) -> ProjectDocument:
        """Create a NOTE document from a Space Constellab document (migration
        task only, no permission check).

        :param project: The project the note belongs to
        :type project: Project
        :param task: The task the note belongs to (None for project-level)
        :type task: Optional[Task]
        :param name: The note name
        :type name: str
        :param content: The rich-text content fetched from Space
        :type content: RichTextDTO
        :param space_document_id: The id of the Space document (idempotency)
        :type space_document_id: str
        :return: The created note
        :rtype: ProjectDocument
        """
        note = self._create_note(project=project, task=task, name=name)
        note.content = content
        note.space_document_id = space_document_id
        note.save()
        return note

    ################################ INTERNALS ################################

    def _get_and_check_document(self, document_id: str) -> ProjectDocument:
        """Get a document and check that the current user has access to its project.

        :param document_id: The ID of the document
        :type document_id: str
        :return: The document
        :rtype: ProjectDocument
        :raises NotFoundException: If the document is not found
        :raises UnauthorizedException: If the user doesn't have access to the project
        """
        document: ProjectDocument | None = ProjectDocument.get_by_id(document_id)

        if not document:
            raise NotFoundException(f"No document found with ID {document_id}")

        security_service = ProjectSecurityService()
        security_service.get_and_check_role_for_project(document.project.id, ProjectUserRole.USER)

        return document

    def _delete_document_and_file(self, document: ProjectDocument) -> str:
        """Delete a document row and, for FILE documents, its ProjectFile row
        and file node in the store.

        The rich-text images of the document are NOT deleted here: this runs inside a
        transaction, so the images are deleted by the caller once it is committed (a
        rollback must not leave a document pointing at a deleted image directory). Use
        :meth:`_delete_documents_images` with the returned id.

        :param document: The document to delete
        :type document: ProjectDocument
        :return: The id of the deleted document, to delete its images after the commit
        :rtype: str
        """
        document_id: str = document.id
        file: ProjectFile | None = document.file
        document.delete_instance()

        if file is not None:
            file.delete_file_from_store()
            file.delete_instance()

        return document_id

    def _delete_documents_images(self, document_ids: list[str]) -> None:
        """Delete the rich-text image directories of documents.

        MUST be called after the DB deletion is committed, never inside the transaction:
        the files cannot be restored by a rollback.

        :param document_ids: The ids of the deleted documents
        :type document_ids: List[str]
        """
        for document_id in document_ids:
            RichTextFileService.delete_object_dir(
                PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE, document_id
            )

    def _create_file_document(
        self,
        project: Project,
        task: Task | None,
        file_path: str,
        filename: str | None = None,
        space_document_id: str | None = None,
    ) -> ProjectDocument:
        """Move a file into the dedicated store and create the ProjectFile +
        ProjectDocument rows. On failure the file node is removed from the
        store to avoid orphan files.

        :param project: The project the document belongs to
        :type project: Project
        :param task: The task the document belongs to (None for project-level)
        :type task: Optional[Task]
        :param file_path: The path of the source file (MOVED into the store)
        :type file_path: str
        :param filename: Optional custom filename
        :type filename: Optional[str]
        :param space_document_id: Optional Space document id (migration)
        :type space_document_id: Optional[str]
        :return: The created document
        :rtype: ProjectDocument
        """
        name = filename or os.path.basename(file_path)

        store = self.get_store()
        # the store moves the file and de-duplicates the destination name
        node = store.add_node_from_path(file_path, name)

        try:
            project_file = ProjectFile(
                file_store=store.id,
                path=os.path.relpath(node.path, store.path),
                name=name,
                size=os.path.getsize(node.path),
            )
            project_file.save()

            document = ProjectDocument(
                project=project,
                task=task,
                type=ProjectDocumentType.FILE,
                name=name,
                file=project_file,
                space_document_id=space_document_id,
            )
            document.save()
            return document
        except Exception:
            # remove the moved node so a DB failure doesn't leave an orphan file
            store.delete_node_path(node.path)
            raise

    def _create_note(self, project: Project, task: Task | None, name: str) -> ProjectDocument:
        """Create an empty NOTE document.

        :param project: The project the note belongs to
        :type project: Project
        :param task: The task the note belongs to (None for project-level)
        :type task: Optional[Task]
        :param name: The note name
        :type name: str
        :return: The created note
        :rtype: ProjectDocument
        """
        if not name or not name.strip():
            raise BadRequestException("Note name cannot be empty")

        note = ProjectDocument(
            project=project,
            task=task,
            type=ProjectDocumentType.NOTE,
            name=name.strip(),
            content=RichText().to_dto(),
        )
        note.save()
        return note
