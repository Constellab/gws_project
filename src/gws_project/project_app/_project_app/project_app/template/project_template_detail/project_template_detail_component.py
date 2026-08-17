import reflex as rx
from gws_reflex_main import (
    main_component,
    right_sidebar_close_button,
    translate,
    user_inline_component,
)
from gws_reflex_main.gws_components import rich_text_component

from ...common.breadcrumb.breadcrumb_component import breadcrumb_component
from ...common.detail_page_layout import detail_page_layout
from ...common.page_layout import page_layout
from ..project_template_form_dialog.project_template_form_dialog_component import (
    project_template_update_dialog,
)
from ..project_template_form_dialog.project_template_form_dialog_state import (
    ProjectTemplateFormDialogState,
)
from ..task_template_form_dialog.task_template_form_dialog_component import (
    task_template_form_dialog,
)
from ..task_template_list.task_template_list_component import task_template_list_component
from ..task_template_list.task_template_list_state import TaskTemplateListState
from ..template_breadcrumb_state import TemplateBreadcrumbState
from . import (
    project_template_detail_translations,  # noqa: F401  (side effect: registers translations)
)
from .project_template_detail_state import TemplateDetailState


def template_action_menu() -> rx.Component:
    """Create the template action menu with update and delete options.

    :return: The action menu component
    :rtype: rx.Component
    """
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(rx.icon("ellipsis-vertical", size=18), variant="ghost", color_scheme="gray")
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("pencil", size=16),
                translate("project_template_detail.update_menu_item"),
                on_click=lambda: ProjectTemplateFormDialogState.open_update_dialog(
                    TemplateDetailState.project_template
                ),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash-2", size=16),
                translate("project_template_detail.delete_menu_item"),
                color_scheme="red",
                on_click=TemplateDetailState.open_delete_template_dialog,
            ),
        ),
    )


def delete_confirmation_dialog() -> rx.Component:
    """Delete confirmation dialog for templates.

    :return: The delete confirmation dialog component
    :rtype: rx.Component
    """
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(translate("project_template_detail.delete_dialog_title")),
            rx.alert_dialog.description(
                translate("project_template_detail.delete_dialog_description")
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        translate("project_template_detail.cancel"),
                        variant="soft",
                        color_scheme="gray",
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        translate("project_template_detail.delete"),
                        color_scheme="red",
                        on_click=TemplateDetailState.delete_template,
                    ),
                ),
                spacing="3",
                justify="end",
            ),
        ),
        open=TemplateDetailState.delete_dialog_opened,
        on_open_change=TemplateDetailState.set_delete_dialog_opened,
    )


def _tab_count_badge(count: rx.Var[int]) -> rx.Component:
    """Create a small count badge for a tab title.

    :param count: The count value to display
    :type count: rx.Var[int]
    :return: The styled count badge component
    :rtype: rx.Component
    """
    return rx.badge(
        count,
        variant="soft",
        size="1",
        radius="full",
    )


def _tab_action_button() -> rx.Component:
    """Create the action button that changes based on the active tab.

    - Task Templates tab: "Create Task Template" button
    - Description tab: "Edit"/"View" toggle button

    :return: The conditional action button component
    :rtype: rx.Component
    """
    return rx.match(
        TemplateDetailState.view_mode,
        (
            "task_templates",
            rx.button(
                rx.icon("plus", size=16),
                translate("project_template_detail.create_task_template_button"),
                variant="solid",
                size="2",
                on_click=TaskTemplateListState.open_create_task_template_dialog,
            ),
        ),
        (
            "description",
            rx.button(
                rx.icon(
                    rx.cond(
                        TemplateDetailState.description_edit_mode,
                        "eye",
                        "pencil",
                    ),
                    size=16,
                ),
                rx.cond(
                    TemplateDetailState.description_edit_mode,
                    translate("project_template_detail.view"),
                    translate("project_template_detail.edit"),
                ),
                variant="solid",
                size="2",
                on_click=TemplateDetailState.toggle_description_edit_mode,
            ),
        ),
        rx.fragment(),
    )


def template_description_component() -> rx.Component:
    """Component for displaying and editing the template description.

    :return: The description component
    :rtype: rx.Component
    """
    return rx.box(
        rich_text_component(
            value=TemplateDetailState.project_template.description,
            disabled=~TemplateDetailState.description_edit_mode,
            output_event=TemplateDetailState.handle_description_change,
            custom_style=rx.cond(
                TemplateDetailState.description_edit_mode,
                {"flex": "1", "display": "flex"},
                {"padding": "0", "flex": "1", "display": "flex"},
            ),
        ),
        key=TemplateDetailState.project_template.id,
        width="100%",
        flex="1",
        min_height="0",
        display="flex",
        flex_direction="column",
        background="var(--card-background)",
        border_radius="8px",
        padding="1rem",
    )


def header() -> rx.Component:
    """Create the header component for the template detail page.

    :return: The header component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.heading(TemplateDetailState.project_template.name, size="6"),
        rx.spacer(),
        template_action_menu(),
        width="100%",
        align="center",
        spacing="2",
    )


def main_content_area() -> rx.Component:
    """Create the main content area with tabs for switching between views.

    The tab bar includes the view triggers on the left and a contextual
    action button on the right.

    :return: The main content area component
    :rtype: rx.Component
    """
    return rx.tabs.root(
        # Tab bar row: triggers on the left, action button on the right
        rx.hstack(
            rx.tabs.list(
                rx.tabs.trigger(
                    rx.hstack(
                        rx.text(translate("project_template_detail.tab_task_templates")),
                        _tab_count_badge(TaskTemplateListState.task_template_count),
                        align="center",
                        spacing="2",
                    ),
                    value="task_templates",
                ),
                rx.tabs.trigger(
                    rx.text(translate("project_template_detail.tab_description")),
                    value="description",
                ),
            ),
            rx.spacer(),
            _tab_action_button(),
            width="100%",
            align="center",
        ),
        # Tab content panels
        rx.tabs.content(
            task_template_list_component(),
            value="task_templates",
            padding_top="1rem",
        ),
        rx.tabs.content(
            template_description_component(),
            value="description",
            padding_top="1rem",
            flex="1",
            min_height="0",
            display="flex",
            flex_direction="column",
        ),
        value=TemplateDetailState.view_mode,
        on_change=TemplateDetailState.set_view_mode,
        width="100%",
        flex="1",
        min_height="0",
        display="flex",
        flex_direction="column",
    )


def _sidebar_section_label(label: str) -> rx.Component:
    """Create a small uppercase gray label for a sidebar section.

    :param label: The label text
    :type label: str
    :return: The styled label component
    :rtype: rx.Component
    """
    return rx.text(
        label,
        size="1",
        color="gray",
        weight="bold",
        style={
            "text-transform": "uppercase",
            "letter-spacing": "0.06em",
        },
    )


def _sidebar_metadata_row(label: str, value: rx.Component) -> rx.Component:
    """Create a metadata row with a label on the left and value on the right.

    :param label: The label text
    :type label: str
    :param value: The value component
    :type value: rx.Component
    :return: The metadata row component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.text(label, size="2", color="gray"),
        rx.spacer(),
        value,
        width="100%",
        align="center",
    )


def details_sidebar() -> rx.Component:
    """Create the details sidebar (right side) with template metadata.

    :return: The details sidebar component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Heading with close button
        rx.hstack(
            _sidebar_section_label(translate("project_template_detail.sidebar_title")),
            rx.spacer(),
            right_sidebar_close_button(),
            width="100%",
            align="center",
        ),
        # Roles section
        rx.cond(
            TemplateDetailState.template_roles.length() > 0,
            rx.vstack(
                _sidebar_section_label(translate("project_template_detail.roles")),
                rx.vstack(
                    rx.foreach(
                        TemplateDetailState.template_roles,
                        lambda role: rx.badge(role, size="2", variant="soft"),
                    ),
                    spacing="2",
                    align_items="start",
                    width="100%",
                ),
                spacing="2",
                align_items="start",
                width="100%",
            ),
        ),
        # Divider + metadata section
        rx.vstack(
            rx.divider(margin_bottom="0.5rem"),
            _sidebar_metadata_row(
                translate("project_template_detail.created_by"),
                user_inline_component(TemplateDetailState.project_template.created_by, size="small"),
            ),
            _sidebar_metadata_row(
                translate("project_template_detail.created_at"),
                rx.text(TemplateDetailState.created_at_text, size="1", weight="medium"),
            ),
            _sidebar_metadata_row(
                translate("project_template_detail.last_modified_by"),
                user_inline_component(
                    TemplateDetailState.project_template.last_modified_by, size="small"
                ),
            ),
            _sidebar_metadata_row(
                translate("project_template_detail.last_modified_at"),
                rx.text(TemplateDetailState.last_modified_at_text, size="1", weight="medium"),
            ),
            spacing="1",
            width="100%",
            padding_top="0.5rem",
        ),
        width="100%",
        spacing="5",
        align_items="start",
    )


def project_template_detail_page() -> rx.Component:
    """Create the template detail page component.

    This page displays template details with tabs for task templates and description,
    info sidebar, and action menu.

    :return: The template detail page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.cond(
                TemplateDetailState.project_template,
                detail_page_layout(
                    main_content=main_content_area(),
                    header_content=header(),
                ),
            ),
            header_content=breadcrumb_component(TemplateBreadcrumbState.breadcrumbs),
            right_sidebar_content=details_sidebar(),
            on_mount=TemplateDetailState.init,
        ),
        # Dialogs
        project_template_update_dialog(),
        delete_confirmation_dialog(),
        task_template_form_dialog(),
    )
