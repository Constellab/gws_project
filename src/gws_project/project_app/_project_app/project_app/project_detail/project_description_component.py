import reflex as rx
from gws_reflex_main.gws_components import rich_text_component

from .project_detail_state import ProjectDetailState


def project_description_component() -> rx.Component:
    """Create the description view with header and content.

    :return: The description view component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Description header with edit toggle
        rx.hstack(
            rx.heading("Description", size="4", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon(
                    rx.cond(
                        ProjectDetailState.description_edit_mode,
                        "eye",
                        "pencil"
                    ),
                    size=16,
                ),
                rx.cond(
                    ProjectDetailState.description_edit_mode,
                    "View",
                    "Edit"
                ),
                variant="soft",
                size="2",
                on_click=ProjectDetailState.toggle_description_edit_mode
            ),
            width="100%",
            align="center"
        ),
        # Description content
        rich_text_component(
            value=ProjectDetailState.project.description,
            disabled=~ProjectDetailState.description_edit_mode,
            output_event=ProjectDetailState.handle_description_change,
            custom_style=rx.cond(
                ProjectDetailState.description_edit_mode,
                {"minHeight": "750px", "flex": "1", "display": "block"},
                {"padding": "0", "flex": "1", "display": "block", "minHeight": "0"}
            )
        ),
        width="100%",
        spacing="3",
        align_items="start",
        # full height but not overflow parent
        flex="1",
        min_height="0",
    )
