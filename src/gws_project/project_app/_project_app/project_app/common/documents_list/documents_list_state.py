import os
from dataclasses import dataclass, field

import reflex as rx
from gws_core import (
    BaseModelDTO,
    DocumentUploadOverrideMode,
    FileHelper,
    Logger,
    SpaceFrontService,
    SpaceHierarchyObjectDTO,
    SpaceHierarchyObjectType,
)
from gws_project.document.document_service import DocumentService
from gws_project.project.project import Project
from gws_project.task.task import Task
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..projects.project_page_state import ProjectPageState


@dataclass
class PaginationState:
    """Dataclass for managing pagination state."""

    documents: list[SpaceHierarchyObjectDTO] = field(default_factory=list)
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
    size_pretty: str
    last_modified: str
    extension: str
    extension_color: str


# Map of file extensions to display colors
_EXTENSION_COLORS: dict[str, str] = {
    # PDF
    "pdf": "#DC2626",
    # Word
    "doc": "#2B579A",
    "docx": "#2B579A",
    "odt": "#2B579A",
    # Excel
    "xls": "#217346",
    "xlsx": "#217346",
    "csv": "#217346",
    "ods": "#217346",
    # PowerPoint
    "ppt": "#D24726",
    "pptx": "#D24726",
    "odp": "#D24726",
    # Images
    "png": "#9333EA",
    "jpg": "#9333EA",
    "jpeg": "#9333EA",
    "gif": "#9333EA",
    "svg": "#9333EA",
    "webp": "#9333EA",
    # Archives
    "zip": "#CA8A04",
    "tar": "#CA8A04",
    "gz": "#CA8A04",
    "rar": "#CA8A04",
    "7z": "#CA8A04",
    # Text / code
    "txt": "#64748B",
    "md": "#64748B",
    "json": "#0EA5E9",
    "xml": "#0EA5E9",
    "html": "#E34F26",
    "css": "#1572B6",
    "py": "#3776AB",
    "js": "#F7DF1E",
    "ts": "#3178C6",
}


def _get_extension_info(filename: str) -> tuple[str, str]:
    """Extract 3-letter extension label and color from a filename.

    :param filename: The document filename
    :type filename: str
    :return: Tuple of (extension label, color hex)
    :rtype: tuple[str, str]
    """
    ext = ""
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
    label = ext[:3].upper() if ext else "FILE"
    color = _EXTENSION_COLORS.get(ext, "#64748B")
    return label, color


class PaginationStateFront(BaseModelDTO):
    """Frontend DTO for pagination state."""

    documents: list[DocumentInfo]
    has_more: bool
    is_loading: bool


class DocumentsListState(ReflexMainState):
    """State for managing the documents list.

    This state handles fetching and displaying documents for a specific project or task folder
    with pagination support. Documents are fetched reactively based on ProjectPageState.
    """

    _cached_object_id: str | None = None

    # We use 1 big object to store all info
    # so the front only uses the pagination_state method and all the parameters are refreshed in front
    _pagination: PaginationState = PaginationState()

    is_uploading: bool = False
    progress: int = 0

    # ===== Rename Document Dialog =====
    rename_dialog_open: bool = False
    rename_document_id: str | None = None
    rename_document_name: str = ""
    is_renaming: bool = False

    @rx.var
    async def pagination_state(self) -> PaginationStateFront:
        """Return the pagination state with documents.

        Documents are loaded on component mount via fetch_documents_on_mount event.

        :return: PaginationStateFront with documents and pagination info
        :rtype: PaginationStateFront
        """
        # Convert to DocumentInfo
        space_front_service = SpaceFrontService()
        documents = []
        for doc in self._pagination.documents:
            ext_label, ext_color = _get_extension_info(doc.name)
            documents.append(
                DocumentInfo(
                    id=doc.id,
                    name=doc.name,
                    url=space_front_service.get_hierarchy_object_url(
                        object_id=doc.id, object_type=doc.objectType
                    ),
                    type=doc.objectType,
                    size_pretty=FileHelper.get_file_size_pretty_text(doc.documentSize)
                    if doc.documentSize is not None
                    else "",
                    last_modified=doc.lastModifiedAt.strftime("%b %d, %Y")
                    if doc.lastModifiedAt
                    else "",
                    extension=ext_label,
                    extension_color=ext_color,
                )
            )

        return PaginationStateFront(
            documents=documents,
            has_more=self._pagination.has_more,
            is_loading=self._pagination.is_loading,
        )

    @rx.event(background=True)  # type: ignore
    async def fetch_documents_on_mount(self):
        """Event handler to fetch documents when the documents view is mounted.

        Checks if the current view mode is "documents" and if the current object is the same
        as cached. If different, loads the first page.
        """

        # Get current object and check if we need to fetch
        async with self:
            # # Check if we're in documents view mode
            # view_mode_state = await self.get_state(ViewModeState)
            # if view_mode_state.view_mode != "documents":
            #     return  # Don't load if not in documents view

            current_object = await self._get_current_object()
            if not current_object:
                return

            # Set loading state
            self._cached_object_id = current_object.id
            self._pagination = PaginationState(
                documents=[], page=0, page_size=20, has_more=True, is_loading=True
            )

        # Fetch documents outside of async with block
        try:
            with await self.authenticate_user():
                document_service = DocumentService()

                # Use the appropriate service method based on object type
                if isinstance(current_object, Task):
                    page_result = document_service.get_task_documents(
                        task_id=current_object.id, page=0, size=20
                    )
                else:  # Project
                    page_result = document_service.get_project_documents(
                        project_id=current_object.id, page=0, size=20
                    )

                async with self:
                    self._pagination = PaginationState(
                        documents=page_result.objects,
                        page=0,
                        page_size=20,
                        has_more=len(page_result.objects) >= 20,
                        is_loading=False,
                    )
        except Exception as e:
            async with self:
                self._pagination = PaginationState(
                    documents=[], page=0, page_size=20, has_more=False, is_loading=False
                )
            raise e

    async def _get_current_object(self) -> Task | Project | None:
        """Get the current object from ProjectPageState.

        :return: The current Task or Project object, or None if not found
        :rtype: Optional[Task | Project]
        """
        project_page_state = await self.get_state(ProjectPageState)
        return await project_page_state.get_object()

    @rx.var
    async def current_object_id(self) -> str | None:
        """Get the current object ID (project_id or task_id) to watch for changes.

        This var is used to detect URL changes and trigger document reloading.

        :return: The current object ID or None if no object
        :rtype: Optional[str]
        """
        current_object = await self._get_current_object()
        if not current_object:
            return None
        return current_object.id

    async def _get_project_id(self) -> str | None:
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

    async def _fetch_documents_page(
        self, current_object: Task | Project, page: int, append: bool = False
    ):
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
            is_loading=True,
        )

        try:
            with await self.authenticate_user():
                document_service = DocumentService()

                # Use the appropriate service method based on object type
                if isinstance(current_object, Task):
                    page_result = document_service.get_task_documents(
                        task_id=current_object.id, page=page, size=self._pagination.page_size
                    )
                else:  # Project
                    page_result = document_service.get_project_documents(
                        project_id=current_object.id, page=page, size=self._pagination.page_size
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
                    is_loading=False,
                )

                return len(page_result.objects)

        except Exception:
            self._pagination = PaginationState(
                documents=self._pagination.documents,
                page=self._pagination.page,
                page_size=self._pagination.page_size,
                has_more=self._pagination.has_more,
                is_loading=False,
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

        await self._fetch_documents_page(current_object=current_object, page=next_page, append=True)

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle file upload to the project or task folder.

        :param files: List of uploaded files from Reflex
        :type files: List[rx.UploadFile]
        """
        try:
            current_object = await self._get_current_object()
            if not current_object:
                yield rx.toast.error("No project or task selected")
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
                                override_mode=DocumentUploadOverrideMode.RENAME,
                            )
                        else:  # Project
                            uploaded_doc = document_service.upload_document_to_project(
                                project_id=current_object.id,
                                file_path=temp_file_path,
                                filename=file.name,
                                override_mode=DocumentUploadOverrideMode.RENAME,
                            )

                        # Add the uploaded document to the beginning of the list
                        self._pagination = PaginationState(
                            documents=[uploaded_doc] + self._pagination.documents,
                            page=self._pagination.page,
                            page_size=self._pagination.page_size,
                            has_more=self._pagination.has_more,
                            is_loading=self._pagination.is_loading,
                        )
                        uploaded_count += 1

                except Exception as e:
                    failed_count += 1
                    Logger.log_exception_stack_trace(e)
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

        project_id: str | None = None
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
                    project_id=project_id, document_id=document_id, name=document_name
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
                    is_loading=self._pagination.is_loading,
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
                    project_id=project_id, document_id=document_id, filename=document_name
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
            action=lambda: self._delete_document_action(document_id),
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
                document_service.delete_document(project_id=project_id, document_id=document_id)

            # Remove the document from the local list
            filtered_documents = [
                doc for doc in self._pagination.documents if doc.id != document_id
            ]
            self._pagination = PaginationState(
                documents=filtered_documents,
                page=self._pagination.page,
                page_size=self._pagination.page_size,
                has_more=self._pagination.has_more,
                is_loading=self._pagination.is_loading,
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
