"""State for managing view mode across different detail pages."""

from typing import Literal

import reflex as rx

ViewMode = Literal["list", "description", "documents", "activity"]


class ViewModeState(rx.State):
    """Shared state for managing the current view mode in detail pages.

    This state is used to coordinate between different components and states
    to enable lazy loading of content based on the selected view mode.
    """

    view_mode: ViewMode = "list"

    def set_view_mode(self, value: str | list[str]):
        """Set the view mode from the segmented control.

        :param value: The view mode value ("list", "description", "documents", or "activity")
        :type value: Union[str, List[str]]
        """
        # Handle both single value and list of values (though we only expect single)
        if isinstance(value, list):
            self.view_mode = value[0] if value else "list"
        else:
            self.view_mode = value
