import reflex as rx
from gws_core import SpaceGroupDTO, SpaceGroupType, SpaceService
from gws_project.project.project_dto import ProjectUserDTO, ProjectUserRole
from gws_project.project.project_service import ProjectService
from gws_reflex_main import FormDialogState, I18nState, ReflexMainState, toast_tr

from ..common.projects.project_page_state import ProjectPageState
from .project_detail_state import ProjectDetailState


class ProjectUserFormDialogState(FormDialogState, rx.State):
    """State management for the project user form dialog functionality.

    This state handles adding new users to a project and updating existing user roles.
    """

    # Editing project user (None for create mode)
    editing_project_user: ProjectUserDTO | None = None

    # Form field default values
    selected_role: str = ProjectUserRole.USER.value
    groups: list[SpaceGroupDTO]

    @rx.event
    async def open_create_dialog(self):
        """Open the dialog in create mode for adding a new group.

        Resets all form fields to default values.
        """
        # Clear editing state
        self.editing_project_user = None

        # Reset form fields
        self.selected_role = "USER"

        # Mark as creating (not editing)
        self.is_update_mode = False

        await self._load_groups()

        # Open the dialog
        await self.open_dialog()

    @rx.event
    async def open_update_dialog(self, project_user: ProjectUserDTO):
        """Open the dialog in update mode with existing project user data.

        Args:
            project_user: The project user to update
        """
        # Store the project user being edited
        self.editing_project_user = project_user

        # Initialize form fields with project user data
        self.selected_role = project_user.role.value

        # Mark as editing
        self.is_update_mode = True

        await self._load_groups()

        # Open the dialog
        await self.open_dialog()

    async def _validate_form_data(self, form_data: dict) -> tuple[str, ProjectUserRole]:
        """Validate form data.

        Args:
            form_data: Dictionary containing form fields (group_id, role)

        Returns:
            True if validation succeeds, False otherwise (error toast is shown)
        """
        # submit_form is a background event, so `self` is a StateProxy here and
        # sibling state can only be reached while the state lock is held.
        async with self:
            i18n = await self.get_state(I18nState)

        # Get values from form data
        group_id = form_data.get("group_id", "").strip()
        role = form_data.get("role", "").strip()

        # Validate required fields
        if not group_id and self.is_create_mode:
            raise Exception(i18n.tr("project_user_form.error.group_required"))

        if not role:
            raise Exception(i18n.tr("project_user_form.error.role_required"))

        # Validate role value
        try:
            enum_role = ProjectUserRole[role]
        except KeyError as err:
            raise Exception(
                i18n.tr("project_user_form.error.invalid_role", {"role": role})
            ) from err

        return group_id, enum_role

    async def _create(self, form_data: dict):
        """Add a new group to the project.

        Args:
            form_data: Dictionary containing form fields (group_id, role)

        Yields:
            Reflex events (rx.toast)
        """
        # Validate form data
        group_id, role = await self._validate_form_data(form_data)

        # Get project_id from ProjectDetailState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        project_id = await self._get_project_id()

        # A SINGLE_USER "group" is not an actual team in Space, so it can't be
        # resolved via get_group_users. Add the underlying user directly instead.
        selected_group = next((group for group in self.groups if group.id == group_id), None)

        with await main_state.authenticate_user():
            project_service = ProjectService()
            if selected_group is not None and selected_group.type == SpaceGroupType.SINGLE_USER:
                project_service.add_user_to_project(project_id, selected_group.user.id, role)
            else:
                project_service.add_group_to_project(project_id, group_id, role)

        # Reload project detail to refresh the user list
        await self._reload_project_detail()

        # Show success message
        # toast_tr resolves I18nState via get_state, so it needs the lock held.
        async with self:
            toast = await toast_tr.success(self, "project_user_form.toast.added")
        yield toast

    async def _update(self, form_data: dict):
        """Update an existing project group's role.

        Args:
            form_data: Dictionary containing form fields (group_id, role)

        Yields:
            Reflex events (rx.toast)
        """
        # Validate form data
        _, role = await self._validate_form_data(form_data)

        # Get project_id from ProjectDetailState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        project_id = await self._get_project_id()

        # Update group role
        with await main_state.authenticate_user():
            project_service = ProjectService()
            project_service.update_user_role(project_id, self.editing_project_user.user.id, role)

        # Reload project detail to refresh the user list
        await self._reload_project_detail()

        # Show success message
        # toast_tr resolves I18nState via get_state, so it needs the lock held.
        async with self:
            toast = await toast_tr.success(self, "project_user_form.toast.role_updated")
        yield toast

    async def _clear_form_state(self):
        """Clear all form state after successful operation."""
        self.editing_project_user = None
        self.selected_role = "USER"
        self.is_update_mode = False

    async def _load_groups(self):
        """Return the list of groups available in the current lab space.

        This computed property fetches groups from the space service each time it's accessed.
        """
        main_state: ReflexMainState = await self.get_state(ReflexMainState)

        with await main_state.authenticate_user():
            # we use the SpaceService with token mode because this app is used within the space so the user might not be in the lab
            space_service = SpaceService("gws-project")
            self.groups = space_service.get_current_lab_all_groups()

    async def _get_project_id(self) -> str:
        """Get the current project ID from ProjectDetailState.

        Returns:
            The current project ID
        """
        async with self:
            project_detail_state = await self.get_state(ProjectPageState)
            url_params = await project_detail_state.get_url_params()
            return url_params.id

    async def _reload_project_detail(self):
        """Reload the project detail state to refresh data."""
        async with self:
            project_detail_state: ProjectDetailState = await self.get_state(ProjectDetailState)
            await project_detail_state.reload_users()
