import reflex as rx
from gws_project.company.company_dto import CompanyStatus
from gws_reflex_main import form_dialog_component

from .company_form_dialog_state import CompanyFormDialogState


def _status_select() -> rx.Component:
    """Status select field, bound directly to state (not to native form data)."""
    return rx.vstack(
        rx.text("Status", size="2", weight="bold"),
        rx.select.root(
            rx.select.trigger(width="100%"),
            rx.select.content(
                *[rx.select.item(status.value, value=status.value) for status in CompanyStatus],
            ),
            value=CompanyFormDialogState.form_status,
            on_change=CompanyFormDialogState.set_form_status,
        ),
        width="100%",
        spacing="1",
    )


def _logo_section() -> rx.Component:
    """Logo upload/preview section.

    Available both when creating and updating a company: in create mode the
    image is staged under a pending id and attached to the company on submit
    (see CompanyFormDialogState._pending_id); in update mode it's persisted
    immediately."""
    return rx.vstack(
        rx.text("Logo", size="2", weight="bold"),
        rx.cond(
            CompanyFormDialogState.form_logo_url != "",
            rx.image(
                src=CompanyFormDialogState.form_logo_url,
                max_height="80px",
                border_radius="0.5rem",
            ),
        ),
        rx.upload.root(
            rx.button(
                rx.spinner(loading=CompanyFormDialogState.is_uploading_logo),
                rx.icon("upload", size=16),
                "Upload logo",
                type="button",
                variant="soft",
                size="2",
            ),
            id="company_logo_upload",
            accept={"image/*": [".png", ".jpg", ".jpeg", ".gif", ".webp"]},
            multiple=False,
            on_drop=CompanyFormDialogState.handle_logo_upload(
                rx.upload_files("company_logo_upload")
            ),
        ),
        width="100%",
        spacing="2",
    )


def _form_content() -> rx.Component:
    """Form content for entering company details."""
    return rx.vstack(
        rx.vstack(
            rx.text("Company Name*", size="2", weight="bold"),
            rx.input(
                placeholder="Enter company name",
                name="name",
                required=True,
                width="100%",
                default_value=CompanyFormDialogState.form_name,
            ),
            width="100%",
            spacing="1",
        ),
        # Quick-create (from the project form's "+" button) only asks for the name -
        # the user can fill in the rest later from the company detail page.
        rx.cond(
            ~CompanyFormDialogState.is_quick_create,
            rx.fragment(
                rx.vstack(
                    rx.text("Address", size="2", weight="bold"),
                    rx.input(
                        placeholder="Enter company address",
                        name="address",
                        width="100%",
                        default_value=CompanyFormDialogState.form_address,
                    ),
                    width="100%",
                    spacing="1",
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text("Registration (SIREN)", size="2", weight="bold"),
                        rx.input(
                            placeholder="9 digit SIREN",
                            name="siren",
                            max_length=9,
                            width="100%",
                            default_value=CompanyFormDialogState.form_siren,
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Phone", size="2", weight="bold"),
                        rx.input(
                            placeholder="Enter phone number",
                            name="phone",
                            width="100%",
                            default_value=CompanyFormDialogState.form_phone,
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    width="100%",
                    spacing="3",
                ),
                _status_select(),
                _logo_section(),
            ),
        ),
        width="100%",
        spacing="3",
    )


def _dialog() -> rx.Component:
    """The base company dialog component without a trigger.

    Reused with different triggers: the company list "New Company" button, the
    quick-create "+" button in the project form, and the company detail page's
    "Update" action.

    :return: The dialog component
    :rtype: rx.Component
    """
    return form_dialog_component(
        state=CompanyFormDialogState,
        title=rx.cond(CompanyFormDialogState.is_update_mode, "Update Company", "New Company"),
        description=rx.cond(
            CompanyFormDialogState.is_update_mode,
            "Update the company details below.",
            "Fill in the details below to create a new company.",
        ),
        form_content=_form_content(),
        max_width="500px",
    )


def create_company_dialog() -> rx.Component:
    """Dialog component for creating a new company with a trigger button.

    :return: The create company dialog component with trigger button
    :rtype: rx.Component
    """
    return rx.fragment(
        rx.button(
            rx.icon("plus", size=18),
            "New Company",
            size="3",
            on_click=CompanyFormDialogState.open_create_dialog,
        ),
        _dialog(),
    )


def quick_create_company_trigger_button() -> rx.Component:
    """Small "+" icon button that opens the quick-create company dialog.

    A plain `type="button"`, safe to embed inside another form (e.g. the project
    form, right next to its company selector): it never submits anything itself.
    Must be paired with `quick_create_company_dialog()` rendered elsewhere on the
    same page (see that function's docstring for why it can't be nested here).

    :return: The trigger button component
    :rtype: rx.Component
    """
    return rx.icon_button(
        rx.icon("plus", size=16),
        type="button",
        variant="soft",
        size="2",
        on_click=CompanyFormDialogState.open_quick_create_dialog,
    )


def quick_create_company_dialog() -> rx.Component:
    """The quick-create company dialog itself (no trigger button).

    Used from the project form to let the user create a company inline via
    `quick_create_company_trigger_button()`. This dialog's content must be
    rendered as a page-level sibling of the project form's dialog, NOT nested
    inside the project form's own `_form_content()`: this dialog contains its
    own `<form>`, and React bubbles a form's `submit` event through the React
    component tree even across a Dialog's portal - nesting it inside the
    project's `<form>` would make submitting this dialog also (incorrectly)
    submit the project form.

    :return: The quick-create company dialog component
    :rtype: rx.Component
    """
    return _dialog()


def company_update_dialog() -> rx.Component:
    """Dialog component for updating an existing company (no trigger button).

    The dialog is controlled by CompanyFormDialogState.dialog_opened.

    :return: The update company dialog component
    :rtype: rx.Component
    """
    return _dialog()
