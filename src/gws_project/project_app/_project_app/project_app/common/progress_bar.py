import reflex as rx

from .status_colors import StatusColors


def progress_bar(progress: int, width: str = "100%", height: str = "12px") -> rx.Component:
    """Create a progress bar component with percentage display.

    :param progress: The progress value (0-100)
    :type progress: int
    :param width: The width of the progress bar
    :type width: str
    :param height: The height of the progress bar
    :type height: str
    :return: The progress bar component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.box(
            rx.box(
                width=f"{progress}%",
                height="100%",
                background=rx.cond(
                    progress == 100,
                    # Make it lighter as this is like a "Disabled" state
                    StatusColors.css_var_done(shade=2),
                    rx.cond(
                        progress > 0,
                        StatusColors.css_var_ongoing(),
                        StatusColors.css_var_todo(),
                    ),
                ),
                border_radius="4px",
                transition="width 0.3s ease",
            ),
            width=width,
            height=height,
            background="var(--gray-3)",
            border_radius="4px",
            position="relative",
            overflow="hidden",
        ),
        spacing="2",
        align="center",
        width="100%",
    )
