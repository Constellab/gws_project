import reflex as rx


def progress_bar(progress: int, width: str = "100%") -> rx.Component:
    """Create a progress bar component with percentage display.

    :param progress: The progress value (0-100)
    :type progress: int
    :return: The progress bar component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.box(
            rx.box(
                width=f"{progress}%",
                height="100%",
                background="var(--accent-9)",
                border_radius="4px",
                transition="width 0.3s ease",
            ),
            width=width,
            height="12px",
            background="var(--gray-3)",
            border_radius="4px",
            position="relative",
            overflow="hidden",
        ),
        rx.text(
            f"{progress}%",
            size="2",
            color="gray",
            width="40px",
            text_align="right",
        ),
        spacing="2",
        align="center",
    )
