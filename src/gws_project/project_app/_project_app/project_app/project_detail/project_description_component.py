import reflex as rx
from gws_reflex_main.gws_components import rich_text_component

from .project_detail_state import ProjectDetailState


def project_description_content() -> rx.Component:
    """Create the description content without header.

    The header (title and action button) is managed at the tab level
    in the project detail page.

    :return: The description content component
    :rtype: rx.Component
    """
    return rx.vstack(
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
