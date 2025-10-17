import reflex as rx
from gws_core import SpaceRootFolderUserRole
from gws_reflex_main import form_dialog_component, group_select

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
                    rx.text("Group", size="2", weight="bold"),

                    group_select(
                        groups=ProjectUserFormDialogState.groups,
                        placeholder="Select a group",
                        name="group_id",
                    ),
                ),
            ),

            width="100%",
            spacing="1"
        ),

        # Role selection field
        rx.vstack(
            rx.text("Role", size="2", weight="bold"),
            rx.select(
                SpaceRootFolderUserRole.get_as_str_list(),
                placeholder="Select a role",
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
            "Update Group Role",
            "Add Group to Project"
        ),
        description=rx.cond(
            ProjectUserFormDialogState.is_update_mode,
            f"Update the role of {ProjectUserFormDialogState.editing_project_user.user.first_name} {ProjectUserFormDialogState.editing_project_user.user.last_name}.",
            "Select a group and assign them a role in this project."
        ),
        form_content=_form_content(),
        max_width="450px"
    )
