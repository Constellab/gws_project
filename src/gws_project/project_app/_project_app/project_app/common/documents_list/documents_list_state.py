import os
from dataclasses import dataclass, field
from typing import List, Optional

import reflex as rx
from gws_core import (BaseModelDTO, DocumentUploadOverrideMode,
                      SpaceFrontService, SpaceHierarchyObjectDTO,
                      SpaceHierarchyObjectType)
from gws_project.document.document_service import DocumentService
from gws_project.project.project import Project
from gws_project.task.task import Task
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..project_page_state import ProjectPageState


@dataclass
class PaginationState:
    """Dataclass for managing pagination state."""
    documents: List[SpaceHierarchyObjectDTO] = field(default_factory=list)
    page: int = 0
    page_size: int = 20
    has_more: bool = True
    is_loading: bool = False


class DocumentInfo(BaseModelDTO):
    """DTO for document information."""
    id: str
    name: str
    url: str
    type: SpaceHierarchyObjectType


class PaginationStateFront(BaseModelDTO):
    """Frontend DTO for pagination state."""
    documents: List[DocumentInfo]
    has_more: bool
    is_loading: bool


class DocumentsListState(ReflexMainState):
    """State for managing the documents list.

    This state handles fetching and displaying documents for a specific project or task folder
    with pagination support. Documents are fetched reactively based on ProjectPageState.
    """

    _cached_object_id: Optional[str] = None

    # We use 1 big object to store all info
    # so the front only uses the pagination_state method and all the parameters are refreshed in front
    _pagination: PaginationState = PaginationState()

    is_uploading: bool = False
    progress: int = 0

    # ===== Rename Document Dialog =====
    rename_dialog_open: bool = False
    rename_document_id: Optional[str] = None
    rename_document_name: str = ""
    is_renaming: bool = False

    @rx.var
    async def pagination_state(self) -> PaginationStateFront:
        """Return the pagination state with documents, fetching them reactively based on ProjectPageState.

        This method automatically fetches documents when the current object changes.

        :return: PaginationStateFront with documents and pagination info
        :rtype: PaginationStateFront
        """
        # Get current object from ProjectPageState
        current_object = await self._get_current_object()

        # If no object or different object, fetch documents
        if current_object and (not self._cached_object_id or self._cached_object_id != current_object.id):
            await self._fetch_initial_documents(current_object)

        # Convert to DocumentInfo
        space_front_service = SpaceFrontService()
        documents = [
            DocumentInfo(
                id=doc.id,
                name=doc.name,
                url=space_front_service.get_hierarchy_object_url(
                    object_id=doc.id,
                    object_type=doc.objectType
                ),
                type=doc.objectType
            )
            for doc in self._pagination.documents
        ]

        return PaginationStateFront(
            documents=documents,
            has_more=self._pagination.has_more,
            is_loading=self._pagination.is_loading
        )

    async def _fetch_initial_documents(self, current_object: Task | Project):
        """Fetch the initial page of documents for a new object.

        :param current_object: The current task or project object
        :type current_object: Task | Project
        """
        # Reset state for new object
        self._cached_object_id = current_object.id
        self._pagination = PaginationState()

        # Fetch first page
        await self._fetch_documents_page(current_object=current_object, page=0, append=False)

    async def _get_current_object(self) -> Optional[Task | Project]:
        """Get the current object from ProjectPageState.

        :return: The current Task or Project object, or None if not found
        :rtype: Optional[Task | Project]
        """
        project_page_state = await self.get_state(ProjectPageState)
        return await project_page_state.get_object()

    async def _get_project_id(self) -> Optional[str]:
        """Get the project ID from the current object.

        :return: The project ID or None if no current object
        :rtype: Optional[str]
        """
        current_object = await self._get_current_object()
        if not current_object:
            return None

        if isinstance(current_object, Task):
            return current_object.project.id
        else:  # Project
            return current_object.id

    async def _fetch_documents_page(self, current_object: Task | Project, page: int, append: bool = False):
        """Fetch a page of documents from the appropriate service.

        :param current_object: The current task or project object
        :type current_object: Task | Project
        :param page: The page number to fetch
        :type page: int
        :param append: Whether to append to existing documents or replace them
        :type append: bool
        :return: Number of documents loaded
        :rtype: int
        """
        self._pagination = PaginationState(
            documents=self._pagination.documents,
            page=self._pagination.page,
            page_size=self._pagination.page_size,
            has_more=self._pagination.has_more,
            is_loading=True
        )

        try:
            with await self.authenticate_user():
                document_service = DocumentService()

                # Use the appropriate service method based on object type
                if isinstance(current_object, Task):
                    page_result = document_service.get_task_documents(
                        task_id=current_object.id,
                        page=page,
                        size=self._pagination.page_size
                    )
                else:  # Project
                    page_result = document_service.get_project_documents(
                        project_id=current_object.id,
                        page=page,
                        size=self._pagination.page_size
                    )

                if append:
                    new_documents = self._pagination.documents + page_result.objects
                else:
                    new_documents = page_result.objects

                self._pagination = PaginationState(
                    documents=new_documents,
                    page=self._pagination.page,
                    page_size=self._pagination.page_size,
                    has_more=len(page_result.objects) >= self._pagination.page_size,
                    is_loading=False
                )

                return len(page_result.objects)

        except Exception:
            self._pagination = PaginationState(
                documents=self._pagination.documents,
                page=self._pagination.page,
                page_size=self._pagination.page_size,
                has_more=self._pagination.has_more,
                is_loading=False
            )
            raise

    async def load_more_documents(self):
        """Load the next page of documents."""
        if not self._pagination.has_more or self._pagination.is_loading:
            return

        current_object = await self._get_current_object()
        if not current_object:
            return

        next_page = self._pagination.page + 1

        await self._fetch_documents_page(
            current_object=current_object,
            page=next_page,
            append=True
        )

    @rx.event
    async def handle_upload(self, files: List[rx.UploadFile]):
        """Handle file upload to the project or task folder.

        :param files: List of uploaded files from Reflex
        :type files: List[rx.UploadFile]
        """
        try:
            current_object = await self._get_current_object()
            if not current_object:
                yield rx.toast.error("No project or task selected")
                return

            if not current_object.space_folder_id:
                yield rx.toast.error("Folder not found")
                return

            if not files:
                yield rx.toast.error("No files selected")
                return

            uploaded_count = 0
            failed_count = 0

            for file in files:
                if not file.name:
                    continue

                temp_file_path = None
                try:
                    # Read file data and save to Reflex upload directory
                    data = await file.read()
                    path = rx.get_upload_dir() / file.name

                    # Write file to upload directory
                    with path.open("wb") as f:
                        f.write(data)

                    temp_file_path = str(path)

                    with await self.authenticate_user():
                        document_service = DocumentService()

                        # Use the appropriate service method based on object type
                        if isinstance(current_object, Task):
                            uploaded_doc = document_service.upload_document_to_task(
                                task_id=current_object.id,
                                file_path=temp_file_path,
                                filename=file.name,
                                override_mode=DocumentUploadOverrideMode.RENAME
                            )
                        else:  # Project
                            uploaded_doc = document_service.upload_document_to_project(
                                project_id=current_object.id,
                                file_path=temp_file_path,
                                filename=file.name,
                                override_mode=DocumentUploadOverrideMode.RENAME
                            )

                        # Add the uploaded document to the beginning of the list
                        self._pagination = PaginationState(
                            documents=[uploaded_doc] + self._pagination.documents,
                            page=self._pagination.page,
                            page_size=self._pagination.page_size,
                            has_more=self._pagination.has_more,
                            is_loading=self._pagination.is_loading
                        )
                        uploaded_count += 1

                except Exception as e:
                    failed_count += 1
                    yield rx.toast.error(f"Failed to upload {file.name}: {str(e)}")
                finally:
                    # Clean up temporary file
                    if temp_file_path and os.path.exists(temp_file_path):
                        try:
                            os.remove(temp_file_path)
                        except Exception:
                            pass  # Ignore cleanup errors

            # Show success message
            if uploaded_count > 0:
                if uploaded_count == 1:
                    yield rx.toast.success(f"Successfully uploaded {uploaded_count} file")
                else:
                    yield rx.toast.success(f"Successfully uploaded {uploaded_count} files")

            if failed_count > 0:
                yield rx.toast.warning(f"{failed_count} file(s) failed to upload")
        finally:
            self.is_uploading = False

    @rx.event
    def handle_upload_progress(self, progress: dict):
        if progress["progress"] < 1:
            self.is_uploading = True

    def open_rename_dialog(self, document_id: str, current_name: str):
        """Open the rename dialog for a document.

        :param document_id: The ID of the document to rename
        :type document_id: str
        :param current_name: The current name of the document
        :type current_name: str
        """
        self.rename_document_id = document_id
        self.rename_document_name = current_name
        self.rename_dialog_open = True

    def close_rename_dialog(self):
        """Close the rename dialog."""
        self.rename_dialog_open = False
        self.rename_document_id = None
        self.rename_document_name = ""

    @rx.event(background=True)  # type: ignore
    async def handle_rename_document(self):
        """Handle the rename document action."""
        if not self.rename_document_id or not self.rename_document_name.strip():
            yield rx.toast.error("Document name cannot be empty")
            return

        project_id: str = None
        async with self:
            project_id = await self._get_project_id()
        if not project_id:
            yield rx.toast.error("Project not found")
            return

        document_id = self.rename_document_id
        document_name = self.rename_document_name.strip()

        async with self:
            self.is_renaming = True

        try:
            with await self.authenticate_user():
                document_service = DocumentService()
                document_service.rename_document(
                    project_id=project_id,
                    document_id=document_id,
                    name=document_name
                )

            # Update the document name in the local list
            updated_documents = []
            for doc in self._pagination.documents:
                if doc.id == document_id:
                    # Create a new document object with updated name
                    updated_doc = SpaceHierarchyObjectDTO(
                        id=doc.id,
                        name=document_name,
                        objectType=doc.objectType,
                        parentId=doc.parentId,
                    )
                    updated_documents.append(updated_doc)
                else:
                    updated_documents.append(doc)

            async with self:
                self._pagination = PaginationState(
                    documents=updated_documents,
                    page=self._pagination.page,
                    page_size=self._pagination.page_size,
                    has_more=self._pagination.has_more,
                    is_loading=self._pagination.is_loading
                )

                self.close_rename_dialog()
            yield rx.toast.success("Document renamed successfully")

        except Exception as e:
            yield rx.toast.error(f"Failed to rename document: {str(e)}")
        finally:
            async with self:
                self.is_renaming = False

    # ===== Download Document =====
    @rx.event
    async def handle_download_document(self, document_id: str, document_name: str):
        """Handle document download using DocumentService.

        :param document_id: The ID of the document to download
        :type document_id: str
        :param document_name: The name of the document
        :type document_name: str
        """
        try:
            project_id = await self._get_project_id()
            if not project_id:
                yield rx.toast.error("Project not found")
                return

            with await self.authenticate_user():
                document_service = DocumentService()
                # Download document bytes directly
                file_data = document_service.download_document_bytes(
                    project_id=project_id,
                    document_id=document_id,
                    filename=document_name
                )

            # Trigger download with raw bytes
            yield rx.download(data=file_data, filename=document_name)

        except Exception as e:
            yield rx.toast.error(f"Failed to download document: {str(e)}")

    # ===== Delete Document =====
    @rx.event
    async def open_delete_document_dialog(self, document_id: str, document_name: str):
        """Open the delete document confirmation dialog.

        :param document_id: The ID of the document to delete
        :type document_id: str
        :param document_name: The name of the document to delete
        :type document_name: str
        """
        delete_dialog_state = await self.get_state(ConfirmDialogState)

        delete_dialog_state.open_dialog(
            title="Delete Document",
            content=f"Are you sure you want to delete '{document_name}'? This will move it to trash.",
            action=lambda: self._delete_document_action(document_id)
        )

    async def _delete_document_action(self, document_id: str):
        """Action to delete the document after confirmation.

        :param document_id: The ID of the document to delete
        :type document_id: str
        """
        try:
            project_id = await self._get_project_id()
            if not project_id:
                yield rx.toast.error("Project not found")
                return

            with await self.authenticate_user():
                document_service = DocumentService()
                document_service.delete_document(
                    project_id=project_id,
                    document_id=document_id
                )

            # Remove the document from the local list
            filtered_documents = [doc for doc in self._pagination.documents if doc.id != document_id]
            self._pagination = PaginationState(
                documents=filtered_documents,
                page=self._pagination.page,
                page_size=self._pagination.page_size,
                has_more=self._pagination.has_more,
                is_loading=self._pagination.is_loading
            )

            yield rx.toast.success("Document deleted successfully")

        except Exception as e:
            yield rx.toast.error(f"Failed to delete document: {str(e)}")

    @rx.event
    def set_rename_document_name(self, name: str):
        """Set the new name for the document being renamed.

        :param name: The new document name
        :type name: str
        """
        self.rename_document_name = name
