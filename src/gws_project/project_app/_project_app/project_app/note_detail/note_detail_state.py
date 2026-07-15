import reflex as rx
from gws_core import RichTextDTO
from gws_project.document.document_dto import ProjectNoteDTO
from gws_project.document.document_service import DocumentService
from gws_project.project.project_service import ProjectService
from gws_project.task.task_service import TaskService
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..common.breadcrumb.breadcrumb_state import BreadcrumbItem
from ..common.project_app_router import ProjectAppRouter


class NoteDetailState(rx.State):
    """State for managing the note detail page.

    This state loads a NOTE document from the ``note_id_param`` URL parameter,
    displays its rich-text content in the editor and saves the content on
    change. It replaces the former note editor dialog.
    """

    _note: ProjectNoteDTO | None = None
    # Title of the parent (task or project) used in the breadcrumb, resolved on load.
    _parent_label: str = ""

    # ===== Rename Note Dialog =====
    rename_dialog_open: bool = False
    rename_note_name: str = ""
    is_renaming: bool = False

    async def on_load(self):
        """Load the note from the ``note_id_param`` URL parameter.

        Called by the page's ``on_load`` hook. Authenticates the user and
        fetches the note (with its rich-text content) and its parent's title
        (for the breadcrumb) through the services.
        """
        main_state = await self.get_state(ReflexMainState)
        if not await main_state.check_authentication():
            return

        note_id = getattr(self, "note_id_param", None)
        if not note_id:
            self._note = None
            self._parent_label = ""
            return

        with await main_state.authenticate_user():
            document_service = DocumentService()
            note = document_service.get_note(note_id)

            # Resolve the parent title for the breadcrumb.
            if note.task_id:
                self._parent_label = TaskService().get_task(note.task_id).title
            else:
                self._parent_label = ProjectService().get_project(note.project_id).title

        self._note = note

    @rx.var
    async def note(self) -> ProjectNoteDTO | None:
        """Return the currently loaded note DTO.

        :return: The note DTO or None if not loaded
        :rtype: Optional[ProjectNoteDTO]
        """
        return self._note

    @rx.var
    async def note_content(self) -> RichTextDTO | None:
        """Return the rich-text content of the loaded note.

        :return: The note content or None
        :rtype: Optional[RichTextDTO]
        """
        if not self._note:
            return None
        return self._note.content

    @rx.var
    async def breadcrumbs(self) -> list[BreadcrumbItem]:
        """Build the breadcrumb trail for the note page.

        The shared BreadcrumbState only understands project/task URL params, so
        the note page builds its own trail: Projects > project > [task] > note.

        :return: List of breadcrumb items
        :rtype: List[BreadcrumbItem]
        """
        if not self._note:
            return []

        items = [BreadcrumbItem(label="Projects", url=ProjectAppRouter.get_project_list_url())]

        if self._note.task_id:
            items.append(
                BreadcrumbItem(
                    label=self._parent_label,
                    url=ProjectAppRouter.get_task_detail_url(self._note.task_id),
                )
            )
        else:
            items.append(
                BreadcrumbItem(
                    label=self._parent_label,
                    url=ProjectAppRouter.get_project_detail_url(self._note.project_id),
                )
            )

        items.append(
            BreadcrumbItem(
                label=self._note.name,
                url=ProjectAppRouter.get_note_detail_url(self._note.id),
            )
        )
        return items

    @rx.event
    async def handle_content_change(self, event_data: dict):
        """Handle changes from the rich text component and save the note content.

        :param event_data: Dictionary containing the RichTextDTO data
        :type event_data: dict
        """
        if not self._note:
            return

        content_dto = RichTextDTO.from_json(event_data)

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            document_service = DocumentService()
            document_service.update_note_content(self._note.id, content_dto)

    # ===== Rename =====
    @rx.event
    def open_rename_dialog(self):
        """Open the rename dialog, prefilled with the current note name."""
        if not self._note:
            return
        self.rename_note_name = self._note.name
        self.rename_dialog_open = True

    @rx.event
    def close_rename_dialog(self):
        """Close the rename dialog."""
        self.rename_dialog_open = False
        self.rename_note_name = ""

    @rx.event
    def set_rename_note_name(self, name: str):
        """Set the new name for the note being renamed.

        :param name: The new note name
        :type name: str
        """
        self.rename_note_name = name

    @rx.event
    async def handle_rename_note(self):
        """Update the note name and refresh the page state."""
        if not self._note:
            return

        if not self.rename_note_name.strip():
            yield rx.toast.error("Note name cannot be empty")
            return

        new_name = self.rename_note_name.strip()

        try:
            self.is_renaming = True
            yield

            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
                document_service = DocumentService()
                self._note = document_service.update_note_name(self._note.id, new_name)

            self.close_rename_dialog()
            yield rx.toast.success("Note renamed successfully")
        except Exception as e:
            yield rx.toast.error(f"Failed to rename note: {str(e)}")
        finally:
            self.is_renaming = False

    # ===== Delete =====
    @rx.event
    async def open_delete_dialog(self):
        """Open the delete confirmation dialog for the note."""
        if not self._note:
            return

        confirm_dialog_state = await self.get_state(ConfirmDialogState)
        confirm_dialog_state.open_dialog(
            title="Delete Note",
            content=f"Are you sure you want to permanently delete '{self._note.name}'? "
            "This action cannot be undone.",
            action=self._delete_note_action,
        )

    async def _delete_note_action(self):
        """Delete the note, then navigate back to the parent project or task."""
        if not self._note:
            yield
            return

        note_id = self._note.id
        task_id = self._note.task_id
        project_id = self._note.project_id

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            document_service = DocumentService()
            document_service.delete_document(note_id)

        yield rx.toast.success("Note deleted successfully")

        # Navigate back to the parent (task or project) page.
        if task_id:
            yield rx.redirect(ProjectAppRouter.get_task_detail_url(task_id))
        else:
            yield rx.redirect(ProjectAppRouter.get_project_detail_url(project_id))
