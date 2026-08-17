from datetime import datetime

import reflex as rx
from gws_core import UserDTO
from gws_project.company.company_dto import CompanyDTO
from gws_project.company.company_service import CompanyService
from gws_project.project.project_dto import CreateProjectFromTemplateDTO, ProjectDTO, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.template.project_template_dto import ProjectTemplateDTO
from gws_project.template.project_template_service import ProjectTemplateService
from gws_project.user.user import User
from gws_reflex_main import FormDialogState, ReflexMainState

from ..common.project_app_router import ProjectAppRouter
from ..common.projects.project_page_state import ProjectPageState


class ProjectFormDialogState(FormDialogState, rx.State):
    """State management for the create project dialog functionality."""

    # Project being edited (None for create mode)
    _editing_project: ProjectDTO | None = None

    # Form field default values
    form_name: str = ""
    form_start_date: str = ""
    form_end_date: str = ""
    form_project_manager_id: str = ""
    form_company_id: str = ""

    # Template-related state
    available_templates: list[ProjectTemplateDTO] = []
    selected_template_id: str = ""
    template_roles: list[str] = []
    role_mapping: dict[str, str] = {}

    # Available users for role assignment
    available_users: list[UserDTO] = []
    project_users: list[UserDTO] = []

    # Available companies for the optional company selector
    available_companies: list[CompanyDTO] = []

    @rx.event
    async def open_create_dialog(self):
        """Open the dialog in create mode and load templates and users."""
        # Reset to create mode
        self.is_update_mode = False

        # Load templates and users
        main_state = await self.get_state(ReflexMainState)

        with await main_state.authenticate_user():
            # Load templates
            template_service = ProjectTemplateService()
            templates = template_service.get_all_templates()
            self.available_templates = [t.to_dto() for t in templates]

            # Load users from the local lab user list. Role assignment (and the
            # project manager) must be a lab user; users enter the lab through
            # the project member-add dialog.
            self.available_users = [user.to_dto() for user in User.get_real_users()]

            # Load companies for the optional company selector
            self.available_companies = [
                company.to_dto() for company in CompanyService().search_companies()
            ]

        # Open the dialog
        self.dialog_opened = True

    @rx.event
    def set_form_company_id(self, value: str):
        """Handle company selection change.

        Ignores empty-string calls: the company select has no explicit "no
        company" item, so a real user pick is never empty. An empty value only
        happens as a spurious on_change Radix Select fires when a new item is
        added to the list and selected at the same time (e.g. right after the
        quick-create dialog adds a company here via add_newly_created_company) -
        without this guard, that spurious call clears the selection we just set.

        Args:
            value: The selected company ID
        """
        if value:
            self.form_company_id = value

    @rx.event
    async def handle_template_change(self, template_id: str):
        """Handle template selection change.

        Args:
            template_id: The selected template ID (empty string for no template)
        """
        self.selected_template_id = template_id

        # Clear role mapping when template changes
        self.role_mapping = {}

        if template_id:
            # Load roles for the selected template
            main_state = await self.get_state(ReflexMainState)

            with await main_state.authenticate_user():
                template_service = ProjectTemplateService()
                self.template_roles = template_service.get_all_roles_for_template(template_id)
        else:
            self.template_roles = []

    @rx.event
    def handle_role_user_change(self, role: str, user_id: str):
        """Handle user assignment change for a specific role.

        Args:
            role: The role name
            user_id: The selected user ID for this role
        """
        if user_id:
            self.role_mapping[role] = user_id
        elif role in self.role_mapping:
            # Remove from mapping if user is deselected
            del self.role_mapping[role]

    @rx.event
    async def open_update_dialog(self, project: ProjectDTO):
        """Open the dialog in update mode with existing project data.

        Args:
            project: The project to update
        """

        # Store the project being edited
        self._editing_project = project

        # Initialize form fields with project data
        self.form_name = project.title

        # set data to format 'YYYY-MM-DD' for date input
        self.form_start_date = project.start_date.strftime("%Y-%m-%d")
        self.form_end_date = project.end_date.strftime("%Y-%m-%d")

        # Set project manager
        self.form_project_manager_id = project.project_manager.id

        # Set company
        self.form_company_id = project.company.id if project.company else ""

        # Load users for project manager selection and companies for the selector
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            project_service = ProjectService()
            self.project_users = [
                pu.user.to_dto() for pu in project_service.get_project_users(project.id)
            ]
            self.available_companies = [
                company.to_dto() for company in CompanyService().search_companies()
            ]

        # Mark as editing
        self.is_update_mode = True

        # Open the dialog
        await self.open_dialog()

    def _validate_and_parse_form_data(self, form_data: dict) -> SaveProjectDTO | None:
        """Validate and parse form data into a SaveProjectDTO.

        Args:
            form_data: Dictionary containing form fields (name, start_date, end_date, project_manager_id)

        Returns:
            SaveProjectDTO if validation succeeds, None otherwise (error toast is shown)
        """
        # Get values from form data
        name = form_data.get("name", "").strip()
        start_date_str = form_data.get("start_date", "").strip()
        end_date_str = form_data.get("end_date", "").strip()
        project_manager_id = form_data.get("project_manager_id", "").strip() or None

        # Validate required fields
        if not name:
            raise Exception("Project name is required")

        if not start_date_str:
            raise Exception("Start date is required")

        if not end_date_str:
            raise Exception("End date is required")

        # Parse dates from string to datetime
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)

        # Create and return the SaveProjectDTO
        return SaveProjectDTO(
            name=name,
            start_date=start_date,
            end_date=end_date,
            project_manager_id=project_manager_id,
            # Read directly from state (kept in sync via on_change) rather than form_data:
            # rx.select is not a native <select>, so its value isn't reliably part of the
            # submitted HTML form data.
            company_id=self.form_company_id or None,
        )

    async def _create(self, form_data: dict):
        """Create a new project using the form data.

        Args:
            form_data: Dictionary containing form fields (name, start_date, end_date)

        Yields:
            Reflex events (rx.toast, rx.redirect)
        """

        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        # Check if creating from template
        if self.selected_template_id:
            # Validate template creation
            created_project = await self._create_from_template(form_data, main_state)
        else:
            # Standard project creation
            # Validate and parse form data
            project_dto = self._validate_and_parse_form_data(form_data)
            if project_dto is None:
                return  # Validation error already shown

            # Create the project
            with await main_state.authenticate_user():
                project_service = ProjectService()
                created_project = project_service.create_project(project_dto)

        # Show success toast
        yield rx.toast.success("Project created successfully")

        # Redirect to the project detail page
        yield rx.redirect(ProjectAppRouter.get_project_detail_url(created_project.id))

    async def _create_from_template(self, form_data: dict, main_state: ReflexMainState):
        """Create a project from a template.

        Args:
            form_data: Dictionary containing form fields
            main_state: The main state instance

        Returns:
            The created project
        """
        # Get values from form data
        name = form_data.get("name", "").strip()
        start_date_str = form_data.get("start_date", "").strip()

        # Validate required fields
        if not name:
            raise Exception("Project name is required")

        if not start_date_str:
            raise Exception("Start date is required")

        # Validate that all roles have been assigned
        if len(self.role_mapping) != len(self.template_roles):
            missing_roles = [role for role in self.template_roles if role not in self.role_mapping]
            raise Exception(
                f"Please assign users to all roles. Missing: {', '.join(missing_roles)}"
            )

        # Parse start date
        start_date = datetime.fromisoformat(start_date_str)

        # Create DTO for template-based creation
        create_dto = CreateProjectFromTemplateDTO(
            name=name,
            start_date=start_date,
            project_manager_id=None,  # Using current user as project manager
            role_mapping=self.role_mapping,
            company_id=self.form_company_id or None,
        )

        # Create the project from template
        with await main_state.authenticate_user():
            project_service = ProjectService()
            created_project = project_service.create_project_from_template(
                self.selected_template_id, create_dto
            )

        return created_project

    async def _update(self, form_data: dict):
        """Update an existing project using the form data.

        Args:
            form_data: Dictionary containing form fields (name, start_date, end_date)

        Yields:
            Reflex events (rx.toast)
        """

        main_state: ReflexMainState
        project_page_state: ProjectPageState
        async with self:
            main_state = await self.get_state(ReflexMainState)
            project_page_state = await self.get_state(ProjectPageState)

        # Validate and parse form data
        project_dto = self._validate_and_parse_form_data(form_data)
        if project_dto is None:
            return  # Validation error already shown

        # Update the project
        with await main_state.authenticate_user():
            project_service = ProjectService()
            project_service.update_project(self._editing_project.id, project_dto)

        # Close dialog and clear all state after successful operation
        async with self:
            # Reload the project detail state if available
            await project_page_state.refresh_object()

        # Show success toast
        yield rx.toast.success("Project updated successfully")

    @rx.event
    async def add_newly_created_company(self, company: CompanyDTO):
        """Add a company just created via the quick-create dialog to the available
        companies list and select it, without leaving the project form.

        Args:
            company: The newly created company
        """
        self.available_companies = self.available_companies + [company]
        self.form_company_id = company.id

    async def _clear_form_state(self):
        """Clear all form state after successful operation."""
        self._editing_project = None
        self.form_name = ""
        self.form_start_date = ""
        self.form_end_date = ""
        self.form_project_manager_id = ""
        self.form_company_id = ""
        self.is_update_mode = False

        # Clear template-related state
        self.selected_template_id = ""
        self.template_roles = []
        self.role_mapping = {}
        self.available_templates = []
        self.available_users = []
        self.available_companies = []
