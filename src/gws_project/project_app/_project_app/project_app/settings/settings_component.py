import reflex as rx
from gws_project.user.user_app_role import AppRole
from gws_reflex_main import (
    language_toggle_component,
    main_component,
    translate,
    user_inline_component,
)

from ..common.page_layout import page_layout
from ..common.updatable_chip_component import updatable_chip
from . import settings_translations  # noqa: F401  (side effect: registers translations)
from .settings_dto import UserRowDTO
from .settings_state import SettingsState

_WEEKDAYS = [
    (0, "settings.day.mon"),
    (1, "settings.day.tue"),
    (2, "settings.day.wed"),
    (3, "settings.day.thu"),
    (4, "settings.day.fri"),
    (5, "settings.day.sat"),
    (6, "settings.day.sun"),
]

_TIMEZONES = [
    "UTC",
    "Europe/Paris",
    "Europe/London",
    "America/New_York",
    "America/Los_Angeles",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Australia/Sydney",
]


def _role_color(role: AppRole) -> str:
    return rx.match(role, (AppRole.ADMIN, "accent"), "gray")


def _role_row(row: UserRowDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(user_inline_component(row.user), vertical_align="middle"),
        rx.table.cell(
            updatable_chip(
                value=row.role,
                all_values=[AppRole.ADMIN, AppRole.MEMBER],
                get_color=_role_color,
                on_value_change=lambda new_role: SettingsState.change_user_role(row.user.id, new_role),
            ),
            vertical_align="middle",
        ),
    )


def _language_section() -> rx.Component:
    return rx.vstack(
        rx.heading(translate("settings.language.title"), size="4"),
        language_toggle_component(size="2"),
        width="100%",
        spacing="3",
        padding="1.5rem",
        border="1px solid var(--gray-4)",
        border_radius="8px",
    )


def _roles_section() -> rx.Component:
    return rx.vstack(
        rx.heading(translate("settings.roles.title"), size="4"),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(translate("settings.roles.user_column")),
                    rx.table.column_header_cell(translate("settings.roles.role_column")),
                )
            ),
            rx.table.body(rx.foreach(SettingsState.users, _role_row)),
            width="100%",
            variant="surface",
        ),
        width="100%",
        spacing="3",
        padding="1.5rem",
        border="1px solid var(--gray-4)",
        border_radius="8px",
    )


def _working_hours_form() -> rx.Component:
    return rx.vstack(
        rx.text(translate("settings.working_hours.working_days"), size="2", weight="medium"),
        rx.hstack(
            *[
                rx.checkbox(
                    translate(label_key),
                    checked=SettingsState.working_days.contains(day),
                    on_change=lambda checked, day=day: SettingsState.toggle_working_day(day, checked),
                )
                for day, label_key in _WEEKDAYS
            ],
            wrap="wrap",
            spacing="4",
        ),
        rx.grid(
            rx.vstack(
                rx.text(translate("settings.working_hours.weekly_hours"), size="2", weight="medium"),
                rx.input(
                    type="number",
                    value=SettingsState.weekly_hours,
                    on_change=SettingsState.set_weekly_hours,
                ),
                spacing="1",
                width="100%",
            ),
            rx.vstack(
                rx.text(translate("settings.working_hours.timezone"), size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(width="100%"),
                    rx.select.content(
                        *[rx.select.item(tz, value=tz) for tz in _TIMEZONES],
                    ),
                    value=SettingsState.timezone,
                    on_change=SettingsState.set_timezone,
                ),
                spacing="1",
                width="100%",
            ),
            rx.vstack(
                rx.text(translate("settings.working_hours.day_start_time"), size="2", weight="medium"),
                rx.input(
                    type="time",
                    value=SettingsState.day_start_time,
                    on_change=SettingsState.set_day_start_time,
                ),
                spacing="1",
                width="100%",
            ),
            rx.vstack(
                rx.text(translate("settings.working_hours.day_end_time"), size="2", weight="medium"),
                rx.input(
                    type="time",
                    value=SettingsState.day_end_time,
                    on_change=SettingsState.set_day_end_time,
                ),
                spacing="1",
                width="100%",
            ),
            rx.vstack(
                rx.text(
                    translate("settings.working_hours.lunch_start_time"), size="2", weight="medium"
                ),
                rx.input(
                    type="time",
                    value=SettingsState.lunch_start_time,
                    on_change=SettingsState.set_lunch_start_time,
                ),
                spacing="1",
                width="100%",
            ),
            rx.vstack(
                rx.text(translate("settings.working_hours.lunch_end_time"), size="2", weight="medium"),
                rx.input(
                    type="time",
                    value=SettingsState.lunch_end_time,
                    on_change=SettingsState.set_lunch_end_time,
                ),
                spacing="1",
                width="100%",
            ),
            columns="2",
            spacing="4",
            width="100%",
        ),
        rx.button(translate("settings.working_hours.save"), on_click=SettingsState.save_working_hours),
        width="100%",
        spacing="4",
        align_items="start",
    )


def _working_hours_section() -> rx.Component:
    return rx.vstack(
        rx.heading(translate("settings.working_hours.title"), size="4"),
        rx.cond(
            SettingsState.is_admin,
            _working_hours_form(),
            rx.text(translate("settings.working_hours.admin_only"), size="2", color="gray"),
        ),
        width="100%",
        spacing="3",
        padding="1.5rem",
        border="1px solid var(--gray-4)",
        border_radius="8px",
    )


def settings_page() -> rx.Component:
    """Settings page: language, roles, and (admin-only) global working hours."""
    return main_component(
        page_layout(
            content=rx.vstack(
                _language_section(),
                _roles_section(),
                _working_hours_section(),
                width="100%",
                spacing="5",
            ),
            header_content=rx.heading(translate("settings.title"), size="6"),
            max_content_width="900px",
            center_content=True,
        )
    )
