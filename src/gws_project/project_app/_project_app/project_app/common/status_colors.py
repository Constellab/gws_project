"""Utility class for centralized status color definitions."""


class StatusColors:
    """Centralized color mapping for BACKLOG/TODO/ONGOING/DONE statuses.

    Used across progress and status chip components to ensure consistent coloring.
    """

    BACKLOG = "indigo"
    TODO = "gray"
    ONGOING = "secondary"
    DONE = "tertiary"

    @staticmethod
    def css_var_todo(shade: int = 9) -> str:
        """Return the CSS variable for TODO status."""
        return f"var(--{StatusColors.TODO}-{shade})"

    @staticmethod
    def css_var_ongoing(shade: int = 9) -> str:
        """Return the CSS variable for ONGOING status."""
        return f"var(--{StatusColors.ONGOING}-{shade})"

    @staticmethod
    def css_var_done(shade: int = 9) -> str:
        """Return the CSS variable for DONE status."""
        return f"var(--{StatusColors.DONE}-{shade})"
