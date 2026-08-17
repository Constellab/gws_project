import reflex as rx
from gws_project.project.project_dto import ProjectUserRole
from gws_reflex_main import form_dialog_component, group_select, translate

from . import (
    project_user_form_dialog_translations,  # noqa: F401  (side effect: registers translations)
)
from .project_user_form_dialog_state import ProjectUserFormDialogState


def _form_content() -> rx.Component:
    """Form content for selecting group and role.

    Returns:
        rx.Component: The form content
    """
    return rx.vstack(
        # Group selection field
        rx.vstack(
            rx.cond(
                ProjectUserFormDialogState.is_create_mode,
                rx.fragment(
                    rx.text(translate("project_user_form.group_label"), size="2", weight="bold"),

                    group_select(
                        groups=ProjectUserFormDialogState.groups,
                        placeholder=translate("project_user_form.select_group_placeholder"),
                        name="group_id",
                    ),
                ),
            ),

            width="100%",
            spacing="1"
        ),

        # Role selection field
        rx.vstack(
            rx.text(translate("project_user_form.role_label"), size="2", weight="bold"),
            rx.select(
                [role.value for role in ProjectUserRole],
                placeholder=translate("project_user_form.select_role_placeholder"),
                name="role",
                default_value=ProjectUserFormDialogState.selected_role,
                width="100%",
            ),
            width="100%",
            spacing="1"
        ),

        width="100%",
        spacing="3"
    )


def project_user_form_dialog() -> rx.Component:
    """Dialog component for adding or updating project groups.

    This dialog allows:
    - Adding new groups to the project (create mode)
    - Updating existing group roles (update mode)

    The dialog is controlled by ProjectUserFormDialogState and can be opened via:
    - ProjectUserFormDialogState.open_create_dialog() for adding new groups
    - ProjectUserFormDialogState.open_update_dialog(project_user) for updating roles

    Returns:
        rx.Component: The project user form dialog component
    """
    return form_dialog_component(
        state=ProjectUserFormDialogState,
        title=rx.cond(
            ProjectUserFormDialogState.is_update_mode,
            translate("project_user_form.update_title"),
            translate("project_user_form.add_title")
        ),
        description=rx.cond(
            ProjectUserFormDialogState.is_update_mode,
            translate(
                "project_user_form.update_description",
                {
                    "first_name": ProjectUserFormDialogState.editing_project_user.user.first_name,
                    "last_name": ProjectUserFormDialogState.editing_project_user.user.last_name,
                },
            ),
            translate("project_user_form.add_description")
        ),
        form_content=_form_content(),
        max_width="450px"
    )
