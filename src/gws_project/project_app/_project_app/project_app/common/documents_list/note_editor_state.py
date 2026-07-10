import reflex as rx
from gws_core import RichTextDTO
from gws_project.document.document_service import DocumentService
from gws_reflex_main import ReflexMainState


class NoteEditorState(rx.State):
    """State for the note editor dialog.

    Opens a NOTE document, displays its rich-text content in the editor and
    saves the content on change.
    """

    dialog_open: bool = False
    note_id: str | None = None
    note_name: str = ""
    note_content: RichTextDTO | None = None

    async def open_note(self, document_id: str):
        """Load a note and open the editor dialog.

        :param document_id: The ID of the note document
        :type document_id: str
        """
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            document_service = DocumentService()
            note = document_service.get_note(document_id)

        self.note_id = note.id
        self.note_name = note.name
        self.note_content = note.content
        self.dialog_open = True

    @rx.event
    def close_dialog(self):
        """Close the note editor dialog."""
        self.dialog_open = False
        self.note_id = None
        self.note_name = ""
        self.note_content = None

    @rx.event
    async def handle_content_change(self, event_data: dict):
        """Handle changes from the rich text component and save the note content.

        :param event_data: Dictionary containing the RichTextDTO data
        :type event_data: dict
        """
        if not self.note_id:
            return

        content_dto = RichTextDTO.from_json(event_data)

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            document_service = DocumentService()
            document_service.update_note_content(self.note_id, content_dto)
