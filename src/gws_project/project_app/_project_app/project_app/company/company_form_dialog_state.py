import reflex as rx
from gws_project.company.company_dto import CompanyDTO, CompanyStatus, SaveCompanyDTO
from gws_project.company.company_service import CompanyService
from gws_reflex_main import FormDialogState, I18nState, ReflexMainState, toast_tr

from ..common.companies.company_page_state import CompanyPageState


class CompanyFormDialogState(FormDialogState, rx.State):
    """State management for the create/update company dialog.

    Also supports a "quick create" mode, used from the project form dialog's
    "+" button next to the company selector: only the name field is shown, and
    on success the newly created company is pushed straight into
    ProjectFormDialogState instead of redirecting to the company detail page.
    """

    # Company being edited (None for create mode)
    _editing_company: CompanyDTO | None = None

    # True when opened from the project form's quick-create "+" button: only the
    # name field is shown, and the dialog never navigates away on success.
    is_quick_create: bool = False

    # Form field default values
    form_name: str = ""
    form_address: str = ""
    form_siren: str = ""
    form_phone: str = ""
    form_status: str = CompanyStatus.PROSPECT.value

    # Logo preview shown in the dialog (a base64 data URL: the file store is not
    # served over HTTP), and the id of the stored file to attach on create
    form_logo_url: str = ""
    form_logo_file_id: str = ""
    is_uploading_logo: bool = False

    @rx.event
    async def open_create_dialog(self):
        """Open the dialog in create mode."""
        self.is_update_mode = False
        self.is_quick_create = False
        self.dialog_opened = True

    @rx.event
    async def open_quick_create_dialog(self):
        """Open the dialog in create mode, for the project form's quick-create button.

        Only the name field is shown - the user can add the other details later
        from the company detail page.
        """
        self.is_update_mode = False
        self.is_quick_create = True
        self.dialog_opened = True

    @rx.event
    def set_form_status(self, value: str):
        """Handle status selection change.

        Args:
            value: The selected CompanyStatus value
        """
        self.form_status = value

    @rx.event
    async def open_update_dialog(self, company: CompanyDTO):
        """Open the dialog in update mode with existing company data.

        Args:
            company: The company to update
        """
        self._editing_company = company
        self.is_quick_create = False

        self.form_name = company.name
        self.form_address = company.address or ""
        self.form_siren = company.siren or ""
        self.form_phone = company.phone or ""
        self.form_status = company.status.value

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            self.form_logo_url = CompanyService().get_logo_data_url(company.id) or ""

        self.is_update_mode = True
        await self.open_dialog()

    async def _validate_and_parse_form_data(self, form_data: dict) -> SaveCompanyDTO:
        """Validate and parse form data into a SaveCompanyDTO.

        Args:
            form_data: Dictionary containing form fields (name, address, siren, phone, status)

        Returns:
            The parsed SaveCompanyDTO (only `name` is required)
        """
        # submit_form is a background event, so `self` is a StateProxy here and
        # sibling state can only be reached while the state lock is held.
        async with self:
            i18n = await self.get_state(I18nState)

        name = form_data.get("name", "").strip()
        if not name:
            raise Exception(i18n.tr("company_form_dialog.error.name_required"))

        address = form_data.get("address", "").strip() or None
        siren = form_data.get("siren", "").strip() or None
        phone = form_data.get("phone", "").strip() or None

        return SaveCompanyDTO(
            name=name,
            address=address,
            siren=siren,
            phone=phone,
            # Read directly from state (kept in sync via on_change) rather than form_data:
            # rx.select is not a native <select>, so its value isn't reliably part of the
            # submitted HTML form data.
            status=CompanyStatus(self.form_status),
            logo_file_id=self.form_logo_file_id or None,
        )

    async def _create(self, form_data: dict):
        """Create a new company using the form data.

        Yields:
            Reflex events (rx.toast, rx.redirect)
        """
        company_dto = await self._validate_and_parse_form_data(form_data)

        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        with await main_state.authenticate_user():
            company_service = CompanyService()
            created_company = company_service.create_company(company_dto)

        if self.is_quick_create:
            # Push the newly created company into the project form dialog instead
            # of navigating away, so the user never leaves the "create project" flow.
            from ..project_form_dialog.project_form_dialog_state import ProjectFormDialogState

            async with self:
                project_form_state = await self.get_state(ProjectFormDialogState)
                await project_form_state.add_newly_created_company(created_company.to_dto())

            # toast_tr resolves I18nState via get_state, so it needs the lock held.
            async with self:
                toast = await toast_tr.success(self, "company_form_dialog.toast.created")
            yield toast
        else:
            from ..common.company_app_router import CompanyAppRouter

            # toast_tr resolves I18nState via get_state, so it needs the lock held.
            async with self:
                toast = await toast_tr.success(self, "company_form_dialog.toast.created")
            yield toast
            yield rx.redirect(CompanyAppRouter.get_company_detail_url(created_company.id))

    async def _update(self, form_data: dict):
        """Update an existing company using the form data.

        Yields:
            Reflex events (rx.toast)
        """
        company_dto = await self._validate_and_parse_form_data(form_data)

        main_state: ReflexMainState
        company_page_state: CompanyPageState
        async with self:
            main_state = await self.get_state(ReflexMainState)
            company_page_state = await self.get_state(CompanyPageState)

        with await main_state.authenticate_user():
            company_service = CompanyService()
            company_service.update_company(self._editing_company.id, company_dto)

        async with self:
            await company_page_state.refresh_object()

        # toast_tr resolves I18nState via get_state, so it needs the lock held.
        async with self:
            toast = await toast_tr.success(self, "company_form_dialog.toast.updated")
        yield toast

    @rx.event
    async def handle_logo_upload(self, files: list[rx.UploadFile]):
        """Handle the logo image upload.

        In update mode, the logo is persisted to the existing company right away.
        In create mode, the company doesn't exist yet: the image is only stored in
        the brick's file store and attached to the company when the form is submitted.

        Args:
            files: The uploaded files (only the first one is used)
        """
        self.is_uploading_logo = True
        try:
            for file in files:
                if not file.name:
                    continue

                data = await file.read()
                extension = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else "png"

                main_state = await self.get_state(ReflexMainState)
                company_service = CompanyService()

                if self.is_update_mode and self._editing_company:
                    with await main_state.authenticate_user():
                        updated_company = company_service.upload_logo(
                            self._editing_company.id, data, extension
                        )
                    logo_file = updated_company.logo_file

                    company_page_state = await self.get_state(CompanyPageState)
                    await company_page_state.refresh_object()
                else:
                    with await main_state.authenticate_user():
                        logo_file = company_service.stage_logo(data, extension)

                self.form_logo_file_id = logo_file.id
                # The store is not served over HTTP: the preview embeds the image
                self.form_logo_url = logo_file.to_data_url() or ""

                break
        finally:
            self.is_uploading_logo = False

    async def _clear_form_state(self):
        """Clear all form state after successful operation."""
        self._editing_company = None
        self.is_quick_create = False
        self.form_name = ""
        self.form_address = ""
        self.form_siren = ""
        self.form_phone = ""
        self.form_status = CompanyStatus.PROSPECT.value
        self.form_logo_url = ""
        self.form_logo_file_id = ""
