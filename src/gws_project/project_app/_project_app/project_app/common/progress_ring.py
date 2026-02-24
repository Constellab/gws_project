import reflex as rx


def progress_ring(progress: rx.Var[int], size: int = 44) -> rx.Component:
    """Create a circular progress ring component inspired by example.jsx ProgressRing.

    :param progress: The progress value (0-100)
    :type progress: rx.Var[int]
    :param size: The size of the ring in pixels
    :type size: int
    :return: The progress ring component
    :rtype: rx.Component
    """
    r = (size - 6) / 2
    circ = 2 * 3.14159265 * r
    half = size / 2

    return rx.box(
        rx.el.svg(
            # Background circle
            rx.el.circle(
                cx=str(half),
                cy=str(half),
                r=str(r),
                fill="none",
                stroke="var(--gray-4)",
                stroke_width="4",
            ),
            # Progress circle
            rx.el.circle(
                cx=str(half),
                cy=str(half),
                r=str(r),
                fill="none",
                stroke=rx.cond(
                    progress == 100,
                    "var(--accent-9)",
                    rx.cond(
                        progress > 0,
                        "var(--secondary-9)",
                        "var(--gray-4)",
                    ),
                ),
                stroke_width="4",
                stroke_dasharray=str(circ),
                stroke_dashoffset=(circ - (progress / 100) * circ).to(str),
                stroke_linecap="round",
                style={
                    "transition": "stroke-dashoffset 0.8s cubic-bezier(.4,0,.2,1)",
                },
            ),
            width=str(size),
            height=str(size),
            style={"transform": "rotate(-90deg)"},
        ),
        rx.text(
            rx.cond(progress > 0, progress.to(str) + "%", "0%"),
            weight="bold",
            color=rx.cond(progress > 0, "var(--gray-12)", "var(--gray-8)"),
            style={
                "position": "absolute",
                "inset": "0",
                "display": "flex",
                "align-items": "center",
                "justify-content": "center",
                "font-size": "10px",
            },
        ),
        position="relative",
        width=f"{size}px",
        height=f"{size}px",
    )
