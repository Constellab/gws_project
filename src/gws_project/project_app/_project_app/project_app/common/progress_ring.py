from typing import Literal

import reflex as rx

from .status_colors import StatusColors


def progress_ring(
    progress: rx.Var[int],
    size: Literal["normal", "big"] = "normal",
) -> rx.Component:
    """Create a circular progress ring component.

    :param progress: The progress value (0-100)
    :type progress: rx.Var[int]
    :param size: Predefined size - "normal" (44px) for tables/lists, "big" (80px) for detail views
    :type size: Literal["normal", "big"]
    :return: The progress ring component
    :rtype: rx.Component
    """
    pixel_size = 80 if size == "big" else 44
    font_size = "14px" if size == "big" else "10px"

    r = (pixel_size - 6) / 2
    circ = 2 * 3.14159265 * r
    half = pixel_size / 2

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
                    StatusColors.css_var_done(),
                    rx.cond(
                        progress > 0,
                        StatusColors.css_var_ongoing(),
                        StatusColors.css_var_todo(shade=4),
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
            width=str(pixel_size),
            height=str(pixel_size),
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
                "font-size": font_size,
            },
        ),
        position="relative",
        width=f"{pixel_size}px",
        height=f"{pixel_size}px",
    )
