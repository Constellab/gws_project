import os
from typing import List, Optional

import reflex as rx
from anyio import sleep
from gws_core.core.classes.search_builder import SearchParams
from gws_core.space.space_dto import (DocumentUploadOverrideMode,
                                      SpaceHierarchyObjectDTO)
from gws_core.space.space_service import SpaceService
from gws_reflex_main import ReflexMainState

from ..common.project_page_state import ProjectPageState


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

    @rx.var
    def documents(self) -> List[SpaceHierarchyObjectDTO]:
        """Return the current list of documents.

        :return: List of SpaceHierarchyObjectDTOs
        :rtype: List[SpaceHierarchyObjectDTO]
        """
        return self._documents

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

        self._is_loading = True

        try:
            with await self.authenticate_user():
                space_service = SpaceService()
                search_params = SearchParams()

                # Get paginated documents
                page_result = space_service.get_project_children_objects_paginated(
                    folder_id=current_project.space_folder_id,
                    search_params=search_params,
                    page=self._page,
                    size=self._page_size
                )

                self._documents = page_result.objects
                self._has_more = len(page_result.objects) >= self._page_size
        except Exception as e:
            # Log error and show toast
            yield rx.toast.error(f"Error loading documents: {str(e)}")
            self._documents = []
            self._has_more = False
        finally:
            self._is_loading = False

    async def load_more_documents(self):
        """Load the next page of documents."""
        if not self._has_more or self._is_loading:
            return

        project_page_state = await self.get_state(ProjectPageState)
        current_project = await project_page_state.project()

        if not current_project or not current_project.space_folder_id:
            return

        self._is_loading = True
        self._page += 1

        try:
            with await self.authenticate_user():
                space_service = SpaceService()
                search_params = SearchParams()

                # Get next page of documents
                page_result = space_service.get_project_children_objects_paginated(
                    folder_id=current_project.space_folder_id,
                    search_params=search_params,
                    page=self._page,
                    size=self._page_size
                )

                # Append new documents to existing list
                self._documents.extend(page_result.objects)
                self._has_more = len(page_result.objects) >= self._page_size

                yield rx.toast.success(f"Loaded {len(page_result.objects)} more documents")
        except Exception as e:
            # Revert page increment on error
            self._page -= 1
            yield rx.toast.error(f"Error loading more documents: {str(e)}")
        finally:
            self._is_loading = False

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
        print(progress)

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
