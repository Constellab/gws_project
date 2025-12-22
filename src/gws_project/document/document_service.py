

from typing import Optional

from gws_core import (
    BadRequestException,
    DocumentUploadOverrideMode,
    PageDTO,
    SearchOperator,
    SpaceHierarchyObjectDTO,
    SpaceHierarchyObjectSearchParams,
    SpaceService,
)

from gws_project.project.project_security_service import ProjectSecurityService, ProjectUserRole
from gws_project.task.task_service import TaskService


class DocumentService:
    """Service class for managing documents in projects and tasks.

    This service handles document operations for both projects and tasks,
    including fetching and uploading documents to their respective space folders.

    :param space_service: Optional SpaceService instance to use for Space operations.
                         If not provided, a default SpaceService instance will be created.
    :type space_service: Optional[SpaceService]
    """

    def __init__(self, space_service: SpaceService | None = None, task_service: Optional['TaskService'] = None):
        """Initialize the DocumentService with optional SpaceService and TaskService instances.

        :param space_service: Optional SpaceService instance to use for Space operations
        :type space_service: Optional[SpaceService]
        :param task_service: Optional TaskService instance to use for task operations
        :type task_service: Optional[TaskService]
        """
        self._space_service = space_service if space_service is not None else SpaceService()
        self._task_service = task_service if task_service is not None else TaskService()

    def get_project_documents(self, project_id: str, page: int, size: int) -> PageDTO[SpaceHierarchyObjectDTO]:
        """Get documents of a project's space folder.

        :param project_id: The ID of the project
        :type project_id: str
        :param page: The page number (0-indexed)
        :type page: int
        :param size: Number of items per page
        :type size: int
        :return: Paginated list of documents in the project's space folder
        :rtype: PageDTO[SpaceHierarchyObjectDTO]
        """
        # Get the project and check permissions
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        search_params = SpaceHierarchyObjectSearchParams()
        search_params.add_object_type_filter(SearchOperator.NEQ, 'FOLDER')

        # Get paginated documents
        return self._space_service.search_project_children_objects_paginated(
            folder_id=project.space_folder_id,
            search_params=search_params,
            page=page,
            size=size
        )

    def get_task_documents(self, task_id: str, page: int, size: int) -> PageDTO[SpaceHierarchyObjectDTO]:
        """Get documents of a task's space folder.

        :param task_id: The ID of the task
        :type task_id: str
        :param page: The page number (0-indexed)
        :type page: int
        :param size: Number of items per page
        :type size: int
        :return: Paginated list of documents in the task's space folder
        :rtype: PageDTO[SpaceHierarchyObjectDTO]
        """
        # Get the task and check permissions
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # Get the space folder ID (from task or parent)
        space_folder_id = task.get_space_folder_id()

        # If no space folder exists, return empty page
        if not space_folder_id:
            return PageDTO.empty_page()

        search_params = SpaceHierarchyObjectSearchParams()
        search_params.add_object_type_filter(SearchOperator.NEQ, 'FOLDER')

        # filter the documents by the task's tag
        search_params.add_tag_filter(SearchOperator.EQ, task.get_space_tag())

        # Get paginated documents
        return self._space_service.search_project_children_objects_paginated(
            folder_id=space_folder_id,
            search_params=search_params,
            page=page,
            size=size
        )

    def upload_document_to_project(
        self,
        project_id: str,
        file_path: str,
        filename: str | None = None,
        override_mode: DocumentUploadOverrideMode = DocumentUploadOverrideMode.RENAME
    ) -> SpaceHierarchyObjectDTO:
        """Upload a document to a project's space folder without tagging.

        :param project_id: The ID of the project
        :type project_id: str
        :param file_path: The path to the file to upload
        :type file_path: str
        :param filename: Optional custom filename for the uploaded document
        :type filename: Optional[str]
        :param override_mode: Override mode for handling existing files (default: RENAME)
        :type override_mode: DocumentUploadOverrideMode
        :return: The uploaded document object
        :rtype: SpaceHierarchyObjectDTO
        :raises BadRequestException: If the project doesn't have a space folder
        """
        # Get the project and check permissions
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        # Ensure the project has a space folder
        if not project.space_folder_id:
            raise BadRequestException(
                f"Project with ID '{project_id}' does not have an associated space folder. "
                "Cannot upload document."
            )

        # Upload the document to the project's space folder
        uploaded_doc = self._space_service.upload_document(
            parent_folder_id=project.space_folder_id,
            file_path=file_path,
            override_mode=override_mode,
            filename=filename
        )

        return uploaded_doc

    def upload_document_to_task(
        self,
        task_id: str,
        file_path: str,
        filename: str | None = None,
        override_mode: DocumentUploadOverrideMode = DocumentUploadOverrideMode.RENAME
    ) -> SpaceHierarchyObjectDTO:
        """Upload a document to a task's space folder and tag it with the task's space tag.

        If the task doesn't have a space folder yet, one will be created automatically.

        :param task_id: The ID of the task
        :type task_id: str
        :param file_path: The path to the file to upload
        :type file_path: str
        :param filename: Optional custom filename for the uploaded document
        :type filename: Optional[str]
        :param override_mode: Override mode for handling existing files (default: RENAME)
        :type override_mode: DocumentUploadOverrideMode
        :return: The uploaded document object
        :rtype: SpaceHierarchyObjectDTO
        :raises BadRequestException: If the task's project doesn't have a space folder
        """
        # Get the task and check permissions
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        space_folder_id = self._task_service.get_or_create_space_folder_id(task_id)

        # Upload the document to the task's space folder
        uploaded_doc = self._space_service.upload_document(
            parent_folder_id=space_folder_id,
            file_path=file_path,
            override_mode=override_mode,
            filename=filename
        )

        # Tag the document with the task's space tag (for both root tasks and subtasks)
        space_tag = task.get_space_tag()
        self._space_service.add_or_replace_tags_on_object(
            entity_id=uploaded_doc.id,
            tags=[space_tag]
        )

        return uploaded_doc

    def rename_document(self, project_id: str, document_id: str, name: str) -> None:
        """Rename a document.

        :param project_id: The ID of the project (to verify user access)
        :type project_id: str
        :param document_id: The ID of the document to rename
        :type document_id: str
        :param name: The new name for the document
        :type name: str
        :raises BadRequestException: If the name is empty
        :raises UnauthorizedException: If the user doesn't have access to the project
        """
        # Verify user has access to the project
        security_service = ProjectSecurityService()
        security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        if not name or not name.strip():
            raise BadRequestException("Document name cannot be empty")

        self._space_service.rename_document(
            document_id=document_id,
            name=name.strip()
        )

    def delete_document(self, project_id: str, document_id: str) -> None:
        """Delete a document (move to trash).

        :param project_id: The ID of the project (to verify user access)
        :type project_id: str
        :param document_id: The ID of the document to delete
        :type document_id: str
        :raises UnauthorizedException: If the user doesn't have access to the project
        """
        # Verify user has access to the project
        security_service = ProjectSecurityService()
        security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        self._space_service.delete_document(document_id)

    def download_document_bytes(self, project_id: str, document_id: str, filename: str) -> bytes:
        """Download a document as bytes.

        :param project_id: The ID of the project (to verify user access)
        :type project_id: str
        :param document_id: The ID of the document to download
        :type document_id: str
        :param filename: The filename for the download
        :type filename: str
        :return: The document bytes
        :rtype: bytes
        :raises UnauthorizedException: If the user doesn't have access to the project
        """
        # Verify user has access to the project
        security_service = ProjectSecurityService()
        security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        return self._space_service.download_document_bytes(
            document_id=document_id,
            filename=filename
        )
