import os
from typing import List, Optional

import reflex as rx
from gws_core import (BaseModelDTO, DocumentUploadOverrideMode, SearchOperator,
                      SearchParams, SpaceFrontService, SpaceHierarchyObjectDTO,
                      SpaceHierarchyObjectType, SpaceService)
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..common.project_page_state import ProjectPageState


class ProjectDocumentInfo(BaseModelDTO):
    """DTO for project document information."""
    id: str
    name: str
    url: str
    type: SpaceHierarchyObjectType


class ProjectDocumentsState(ReflexMainState):
    """State for managing the project documents list.

    This state handles fetching and displaying documents for a specific project's folder
    with pagination support.
    """

    _project_id: Optional[str] = None
    _documents: List[SpaceHierarchyObjectDTO] = []
    _page: int = 0
    _page_size: int = 20
    _has_more: bool = True
    _is_loading: bool = False

    is_uploading: bool = False
    _is_uploading_big_file: bool = False
    progress: int = 0

    # ===== Rename Document Dialog =====
    rename_dialog_open: bool = False
    rename_document_id: Optional[str] = None
    rename_document_name: str = ""
    is_renaming: bool = False

    @rx.var
    def documents(self) -> List[ProjectDocumentInfo]:
        """Return the current list of documents.

        :return: List of ProjectDocumentInfo
        :rtype: List[ProjectDocumentInfo]
        """
        space_front_service = SpaceFrontService()
        return [
            ProjectDocumentInfo(
                id=doc.id,
                name=doc.name,
                url=space_front_service.get_hierarchy_object_url(
                    object_id=doc.id,
                    object_type=doc.objectType
                ),
                type=doc.objectType
            )
            for doc in self._documents
        ]

    @rx.var
    def is_loading(self) -> bool:
        """Return whether documents are currently being loaded.

        :return: True if loading, False otherwise
        :rtype: bool
        """
        return self._is_loading

    @rx.var
    def has_more(self) -> bool:
        """Return whether there are more documents to load.

        :return: True if more documents available, False otherwise
        :rtype: bool
        """
        return self._has_more

    async def _fetch_documents_page(self, folder_id: str, page: int, append: bool = False):
        """Fetch a page of documents from the space service.

        :param folder_id: The folder ID to fetch documents from
        :type folder_id: str
        :param page: The page number to fetch
        :type page: int
        :param append: Whether to append to existing documents or replace them
        :type append: bool
        :return: Number of documents loaded
        :rtype: int
        """
        self._is_loading = True

        try:
            with await self.authenticate_user():
                space_service = SpaceService()
                search_params = SearchParams()
                search_params.add_filter_criteria("objectType", SearchOperator.NEQ, "FOLDER")

                # Get paginated documents
                page_result = space_service.get_project_children_objects_paginated(
                    folder_id=folder_id,
                    search_params=search_params,
                    page=page,
                    size=self._page_size
                )

                if append:
                    self._documents.extend(page_result.objects)
                else:
                    self._documents = page_result.objects

                self._has_more = len(page_result.objects) >= self._page_size

                return len(page_result.objects)

        finally:
            self._is_loading = False

    async def load_documents(self):
        """Load the first page of documents for the current project."""
        project_page_state = await self.get_state(ProjectPageState)
        current_project = await project_page_state.project()

        if not current_project:
            self._documents = []
            self._has_more = False
            return

        # Reset if this is a new project
        if self._project_id != current_project.id:
            self._project_id = current_project.id
            self._page = 0
            self._documents = []

        # Don't load if we already have documents or no folder_id
        if not current_project.space_folder_id:
            self._documents = []
            self._has_more = False
            return

        if self._documents and self._page == 0:
            return

        try:
            await self._fetch_documents_page(
                folder_id=current_project.space_folder_id,
                page=self._page,
                append=False
            )
        except Exception as e:
            self._documents = []
            self._has_more = False
            raise e

    async def load_more_documents(self):
        """Load the next page of documents."""
        if not self._has_more or self._is_loading:
            return

        project_page_state = await self.get_state(ProjectPageState)
        current_project = await project_page_state.project()

        if not current_project or not current_project.space_folder_id:
            return

        await self._fetch_documents_page(
            folder_id=current_project.space_folder_id,
            page=self._page + 1,
            append=True
        )

        self._page += 1

    async def reset_documents(self):
        """Reset documents list when project changes."""
        self._project_id = None
        self._documents = []
        self._page = 0
        self._has_more = True
        await self.load_documents()

    @rx.event
    async def handle_upload(self, files: List[rx.UploadFile]):
        """Handle file upload to the project folder.

        :param files: List of uploaded files from Reflex
        :type files: List[rx.UploadFile]
        """

        project_page_state = await self.get_state(ProjectPageState)
        current_project = await project_page_state.project()

        if not current_project or not current_project.space_folder_id:
            yield rx.toast.error("Project folder not found")
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
                    space_service = SpaceService()

                    # Upload the document with RENAME mode to avoid conflicts
                    uploaded_doc = space_service.upload_document(
                        parent_folder_id=current_project.space_folder_id,
                        file_path=temp_file_path,
                        override_mode=DocumentUploadOverrideMode.RENAME,
                        filename=file.name
                    )

                    # Add the uploaded document to the beginning of the list

                    self._documents.insert(0, uploaded_doc)
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

        self.is_uploading = False

        # Show success message
        if uploaded_count > 0:
            if uploaded_count == 1:
                yield rx.toast.success(f"Successfully uploaded {uploaded_count} file")
            else:
                yield rx.toast.success(f"Successfully uploaded {uploaded_count} files")

        if failed_count > 0:
            yield rx.toast.warning(f"{failed_count} file(s) failed to upload")

    @rx.event
    def handle_upload_progress(self, progress: dict):

        # For small file the progress is set to 1 directly, it will be set to false by upload method
        # for big file, the progress is set to 1 once the upload method is complete

        if progress["progress"] == 1:
            # for small file we let the upload method handle the is_uploading flag to False
            if not self._is_uploading_big_file:
                self.is_uploading = True
            # reset the big uploading flag
            self._is_uploading_big_file = False
        else:
            self._is_uploading_big_file = True
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

        try:
            with await self.authenticate_user():
                space_service = SpaceService()
                space_service.rename_document(
                    document_id=document_id,
                    name=document_name
                )

            # Update the document name in the local list
            async with self:
                for doc in self._documents:
                    if doc.id == document_id:
                        doc.name = document_name
                        break

                self.close_rename_dialog()
            yield rx.toast.success("Document renamed successfully")

        except Exception as e:
            yield rx.toast.error(f"Failed to rename document: {str(e)}")
        finally:
            async with self:
                self.is_renaming = False

    # ===== Download Document =====
    @rx.event()
    async def handle_download_document(self, document_id: str, document_name: str):
        """Handle document download using SpaceService.

        :param document_id: The ID of the document to download
        :type document_id: str
        :param document_name: The name of the document
        :type document_name: str
        """
        try:
            with await self.authenticate_user():
                space_service = SpaceService()
                # Download document bytes directly
                file_data = space_service.download_document_bytes(
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
            with await self.authenticate_user():
                space_service = SpaceService()
                space_service.delete_document(document_id)

            # Remove the document from the local list
            self._documents = [doc for doc in self._documents if doc.id != document_id]

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
