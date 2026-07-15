import os
from dataclasses import dataclass, field

import reflex as rx
from gws_core import BaseModelDTO, FileHelper, Logger
from gws_project.document.document_dto import ProjectDocumentDTO, ProjectDocumentType
from gws_project.document.document_service import DocumentService
from gws_project.project.project import Project
from gws_project.task.task import Task
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..project_app_router import ProjectAppRouter
from ..projects.project_page_state import ProjectPageState


class DocumentInfo(BaseModelDTO):
    """DTO for document information displayed in the documents list."""

    id: str
    name: str
    type: str  # "FILE" or "NOTE"
    size_pretty: str
    last_modified: str
    extension: str


@dataclass
class PaginationState:
    """Dataclass for managing pagination state."""

    documents: list[DocumentInfo] = field(default_factory=list)
    page: int = 0
    page_size: int = 20
    has_more: bool = True
    is_loading: bool = False


def _get_extension_label(filename: str) -> str:
    """Extract a short extension label from a filename.

    :param filename: The document filename
    :type filename: str
    :return: The extension label (e.g. "PDF")
    :rtype: str
    """
    ext = ""
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
    return ext[:3].upper() if ext else "FILE"


def _to_document_info(document: ProjectDocumentDTO) -> DocumentInfo:
    """Convert a ProjectDocumentDTO to the frontend DocumentInfo.

    :param document: The document DTO
    :type document: ProjectDocumentDTO
    :return: The frontend document info
    :rtype: DocumentInfo
    """
    is_note = document.type == ProjectDocumentType.NOTE
    return DocumentInfo(
        id=document.id,
        name=document.name,
        type=document.type.value,
        size_pretty=FileHelper.get_file_size_pretty_text(document.size)
        if document.size is not None
        else "",
        last_modified=document.last_modified_at.strftime("%b %d, %Y")
        if document.last_modified_at
        else "",
        extension="NOTE" if is_note else _get_extension_label(document.name),
    )


class DocumentsListState(rx.State):
    """State for managing the documents list.

    This state handles fetching and displaying documents (files and notes) for
    a specific project or task with pagination support. Documents are stored
    locally (brick DB + dedicated lab file store).
    """

    _cached_object_id: str | None = None

    # We use 1 big object to store all info
    # so the front only uses the pagination_state method and all the parameters are refreshed in front
    _pagination: PaginationState = PaginationState()

    is_uploading: bool = False
    progress: int = 0

    # ===== Create Note Dialog =====
    create_note_dialog_open: bool = False
    create_note_name: str = ""
    is_creating_note: bool = False

    # ===== Rename Document Dialog =====
    rename_dialog_open: bool = False
    rename_document_id: str | None = None
    rename_document_name: str = ""
    is_renaming: bool = False

    @rx.var
    async def pagination_state(self) -> PaginationState:
        """Return the pagination state with documents.

        Documents are loaded on component mount via fetch_documents_on_mount event.

        :return: PaginationState with documents and pagination info
        :rtype: PaginationState
        """
        return self._pagination

    @rx.event(background=True)  # type: ignore
    async def fetch_documents_on_mount(self):
        """Event handler to fetch documents when the documents view is mounted.

        Loads the first page of documents of the current project or task.
        """

        # Get current object and check if we need to fetch
        async with self:
            current_object = await self._get_current_object()
            if not current_object:
                return

            main_state = await self.get_state(ReflexMainState)

            # Set loading state
            self._cached_object_id = current_object.id
            self._pagination = PaginationState(
                documents=[], page=0, page_size=20, has_more=True, is_loading=True
            )

        # Fetch documents outside of async with block
        try:
            with await main_state.authenticate_user():
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
                        documents=[_to_document_info(doc) for doc in page_result.objects],
                        page=0,
                        page_size=20,
                        has_more=not page_result.is_last_page,
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

    async def _fetch_documents_page(
        self, current_object: Task | Project, page: int, append: bool = False
    ):
        """Fetch a page of documents from the document service.

        :param current_object: The current task or project object
        :type current_object: Task | Project
        :param page: The page number to fetch
        :type page: int
        :param append: Whether to append to existing documents or replace them
        :type append: bool
        """
        self._pagination = PaginationState(
            documents=self._pagination.documents,
            page=page,
            page_size=self._pagination.page_size,
            has_more=self._pagination.has_more,
            is_loading=True,
        )

        try:
            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
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

                new_page_documents = [_to_document_info(doc) for doc in page_result.objects]
                if append:
                    new_documents = self._pagination.documents + new_page_documents
                else:
                    new_documents = new_page_documents

                self._pagination = PaginationState(
                    documents=new_documents,
                    page=page,
                    page_size=self._pagination.page_size,
                    has_more=not page_result.is_last_page,
                    is_loading=False,
                )

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
        """Handle file upload to the project or task.

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

                    main_state = await self.get_state(ReflexMainState)
                    with await main_state.authenticate_user():
                        document_service = DocumentService()

                        # Use the appropriate service method based on object type
                        # (the file is MOVED into the store)
                        if isinstance(current_object, Task):
                            uploaded_doc = document_service.upload_document_to_task(
                                task_id=current_object.id,
                                file_path=temp_file_path,
                                filename=file.name,
                            )
                        else:  # Project
                            uploaded_doc = document_service.upload_document_to_project(
                                project_id=current_object.id,
                                file_path=temp_file_path,
                                filename=file.name,
                            )

                        # Add the uploaded document to the beginning of the list
                        self._pagination = PaginationState(
                            documents=[_to_document_info(uploaded_doc)]
                            + self._pagination.documents,
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
                    # Clean up temporary file (the store moves it, so it only
                    # remains on failure)
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

        document_id = self.rename_document_id
        document_name = self.rename_document_name.strip()

        async with self:
            self.is_renaming = True
            main_state = await self.get_state(ReflexMainState)

        try:
            with await main_state.authenticate_user():
                document_service = DocumentService()
                document_service.rename_document(document_id=document_id, name=document_name)

            # Update the document name in the local list
            updated_documents = []
            for doc in self._pagination.documents:
                if doc.id == document_id:
                    # Create a new document object with updated name
                    updated_documents.append(doc.model_copy(update={"name": document_name}))
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
            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
                document_service = DocumentService()
                # Download document bytes directly
                file_data = document_service.download_document_bytes(document_id=document_id)

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
            content=f"Are you sure you want to permanently delete '{document_name}'? "
            "This action cannot be undone.",
            action=lambda: self._delete_document_action(document_id),
        )

    async def _delete_document_action(self, document_id: str):
        """Action to delete the document after confirmation.

        :param document_id: The ID of the document to delete
        :type document_id: str
        """
        try:
            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
                document_service = DocumentService()
                document_service.delete_document(document_id=document_id)

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

    # ===== Create Note =====
    def open_create_note_dialog(self):
        """Open the create note dialog."""
        self.create_note_name = ""
        self.create_note_dialog_open = True

    def close_create_note_dialog(self):
        """Close the create note dialog."""
        self.create_note_dialog_open = False
        self.create_note_name = ""

    @rx.event
    def set_create_note_name(self, name: str):
        """Set the name for the note being created.

        :param name: The note name
        :type name: str
        """
        self.create_note_name = name

    @rx.event
    async def handle_create_note(self):
        """Handle creation of a new note attached to the current project or task."""
        if not self.create_note_name.strip():
            yield rx.toast.error("Note name cannot be empty")
            return

        try:
            current_object = await self._get_current_object()
            if not current_object:
                yield rx.toast.error("No project or task selected")
                return

            self.is_creating_note = True
            yield

            note_name = self.create_note_name.strip()

            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
                document_service = DocumentService()

                if isinstance(current_object, Task):
                    created_note = document_service.create_note_for_task(
                        task_id=current_object.id,
                        name=note_name,
                    )
                else:  # Project
                    created_note = document_service.create_note_for_project(
                        project_id=current_object.id,
                        name=note_name,
                    )

                # Add the created note to the beginning of the list
                self._pagination = PaginationState(
                    documents=[_to_document_info(created_note)] + self._pagination.documents,
                    page=self._pagination.page,
                    page_size=self._pagination.page_size,
                    has_more=self._pagination.has_more,
                    is_loading=self._pagination.is_loading,
                )

            self.close_create_note_dialog()
            yield rx.toast.success("Note created successfully")

            # Navigate to the created note's page right away
            yield rx.redirect(ProjectAppRouter.get_note_detail_url(created_note.id))

        except Exception as e:
            Logger.log_exception_stack_trace(e)
            yield rx.toast.error(f"Failed to create note: {str(e)}")
        finally:
            self.is_creating_note = False

    @rx.event
    def set_rename_document_name(self, name: str):
        """Set the new name for the document being renamed.

        :param name: The new document name
        :type name: str
        """
        self.rename_document_name = name
