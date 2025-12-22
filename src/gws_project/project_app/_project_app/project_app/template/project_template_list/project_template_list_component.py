import reflex as rx
from gws_reflex_main import main_component, user_inline_component

from ...common.page_layout import page_layout
from ..project_template_form_dialog.project_template_form_dialog_component import (
    create_template_dialog,
)
from .project_template_list_state import ProjectTemplateDTO, ProjectTemplateListState


def project_template_list_page() -> rx.Component:
    """Create the template list page component.

    This component displays a table of project templates with columns for
    name, description, status, creator, and actions.

    :return: The template list page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.vstack(
                # Error message display
                rx.cond(
                    ProjectTemplateListState.error_message != "",
                    rx.callout(
                        ProjectTemplateListState.error_message,
                        icon="triangle_alert",
                        color_scheme="red",
                        role="alert",
                        margin_bottom="1rem",
                    ),
                ),
                # Loading indicator
                rx.cond(
                    ProjectTemplateListState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="2rem"),
                    # Template table
                    rx.cond(
                        ProjectTemplateListState.project_templates.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Name"),
                                    rx.table.column_header_cell("Created By"),
                                    rx.table.column_header_cell("Created At"),
                                ),
                            ),
                            rx.table.body(rx.foreach(ProjectTemplateListState.project_templates, _row)),
                            width="100%",
                            variant="surface",
                        ),
                        # Empty state when no templates
                        rx.center(
                            rx.vstack(
                                rx.icon("layout_template", size=48, color="gray"),
                                rx.text("No templates found", size="4", color="gray", margin_top="1rem"),
                                rx.text("Create your first template to get started", size="2", color="gray"),
                                spacing="2",
                                align="center",
                            ),
                            padding="3rem",
                            width="100%",
                        ),
                    ),
                ),
                width="100%",
                spacing="4",
            ),
            header_content=rx.hstack(
                rx.heading("Project Templates", size="6"),
                create_template_dialog(),
                justify="between",
                align="center",
                width="100%",
            ),
        )
    )


def _row(template: ProjectTemplateDTO) -> rx.Component:
    """Render a single row in the template table.

    :param template: The template DTO to render
    :type template: ProjectTemplateDTO
    :return: A table row component
    :rtype: rx.Component
    """
    return rx.table.row(
        rx.table.cell(
            rx.text(
                template.name,
            ),
        ),
        rx.table.cell(user_inline_component(template.created_by)),
        rx.table.cell(rx.moment(template.created_at, format="MMM D, YYYY")),
        style={":hover": {"background_color": "var(--gray-3)"}, "cursor": "pointer"},
        on_click=lambda: ProjectTemplateListState.go_to_project_template(template.id),
    )
