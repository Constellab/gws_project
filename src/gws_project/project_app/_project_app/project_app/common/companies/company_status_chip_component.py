"""Status chip component for displaying company status with color-coded badges."""

from collections.abc import Callable
from typing import Literal

import reflex as rx
from gws_project.company.company_dto import CompanyStatus

from ..status_colors import StatusColors
from ..updatable_chip_component import updatable_chip


def _get_status_color(status: CompanyStatus):
    """Get the color scheme for a given company status.

    :param status: The company status
    :type status: CompanyStatus
    :return: The color scheme name
    :rtype: str
    """
    return rx.match(
        status,
        (CompanyStatus.PROSPECT, StatusColors.TODO),
        (CompanyStatus.PARTENAIRE, StatusColors.BACKLOG),
        (CompanyStatus.CLIENT, StatusColors.DONE),
        StatusColors.TODO,
    )


def company_status_chip(
    status: CompanyStatus,
    size: Literal["1", "2", "3"] | None = None,
    on_status_change: Callable[[str], None] | None = None,
) -> rx.Component:
    """Create a status chip component with color-coded badge and status selector.

    :param status: The company status (PARTENAIRE, PROSPECT, CLIENT)
    :type status: CompanyStatus
    :param size: The badge size (optional)
    :type size: str
    :param on_status_change: Callback function when status changes (optional)
    :type on_status_change: Callable[[str], None]
    :return: The status chip component
    :rtype: rx.Component
    """
    return updatable_chip(
        value=status,
        all_values=list(CompanyStatus),
        get_color=_get_status_color,
        size=size,
        on_value_change=on_status_change,
    )
