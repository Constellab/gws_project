import reflex as rx
from gws_reflex_main import translate, user_inline_component
from gws_reflex_main.gws_components import rich_text_component

from . import task_activity_translations  # noqa: F401  (side effect: registers translations)
from .task_activity_state import TaskActivityState


def _activity_event_row(item: rx.Var) -> rx.Component:
    """Create a single, compact timeline row for a history event.

    Automatic events (recalculated from subtasks) use a more muted icon color to keep
    the timeline discreet and let direct user actions stand out.

    :param item: The activity item (kind == "event")
    :type item: rx.Var
    :return: The row component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.box(
            rx.icon(item.icon, size=13),
            background=rx.cond(item.is_automatic, "var(--gray-3)", "var(--accent-3)"),
            color=rx.cond(item.is_automatic, "var(--gray-9)", "var(--accent-9)"),
            border_radius="50%",
            padding="6px",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.hstack(
            user_inline_component(item.actor, size="small"),
            rx.text(item.message, size="2", color="gray"),
            spacing="1",
            align="center",
            wrap="wrap",
        ),
        rx.spacer(),
        rx.text(item.created_at_text, size="1", color="gray", white_space="nowrap"),
        width="100%",
        align="center",
        spacing="3",
        padding_y="0.4rem",
        key=item.id,
    )


def _comment_edit_button(item: rx.Var) -> rx.Component:
    """Create the edit button shown on a comment the current user may edit.

    :param item: The activity item (kind == "comment")
    :type item: rx.Var
    :return: The button component, or nothing if the current user can't edit this comment
    :rtype: rx.Component
    """
    return rx.cond(
        item.can_edit,
        rx.icon_button(
            rx.icon("pencil", size=14),
            variant="ghost",
            size="1",
            color_scheme="gray",
            on_click=TaskActivityState.start_edit_comment(item.comment_id, item.content),
        ),
    )


def _comment_edit_form() -> rx.Component:
    """Create the inline edit form shown on a comment currently being edited.

    :return: The edit form component
    :rtype: rx.Component
    """
    return rx.vstack(
        rich_text_component(
            value=TaskActivityState.edit_comment_content,
            disabled=False,
            output_event=TaskActivityState.handle_edit_comment_change,
            custom_style={"minHeight": "60px", "flex": "0", "backgroundColor": "var(--card-background)"},
        ),
        rx.hstack(
            rx.button(
                translate("task_activity.cancel"),
                variant="soft",
                color_scheme="gray",
                size="2",
                on_click=TaskActivityState.cancel_edit_comment,
            ),
            rx.button(
                translate("task_activity.save"), size="2", on_click=TaskActivityState.save_edit_comment
            ),
            spacing="2",
            justify="end",
            width="100%",
        ),
        width="100%",
        spacing="2",
    )


def _comment_card(item: rx.Var) -> rx.Component:
    """Create a comment row: the same icon bubble as a history event, then author,
    timestamp, edited marker and body.

    Borderless like the event rows: a comment is one more entry of the timeline, and the
    icon is what tells the two apart.

    :param item: The activity item (kind == "comment")
    :type item: rx.Var
    :return: The row component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.box(
            rx.icon("message-square", size=13),
            background="var(--accent-3)",
            color="var(--accent-9)",
            border_radius="50%",
            padding="6px",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.hstack(
                user_inline_component(item.actor, size="small"),
                rx.cond(
                    item.is_edited,
                    rx.text(
                        translate("task_activity.edited"),
                        size="1",
                        color="gray",
                        font_style="italic",
                    ),
                ),
                rx.spacer(),
                rx.text(item.created_at_text, size="1", color="gray", white_space="nowrap"),
                _comment_edit_button(item),
                width="100%",
                align="center",
                spacing="2",
            ),
            rx.cond(
                TaskActivityState.editing_comment_id == item.comment_id,
                _comment_edit_form(),
                # Read mode renders the comment as markdown rather than mounting the
                # editor: `disabled` still leaves the editor's inline toolbars reacting to
                # the pointer, so hovering a comment looked like an invitation to type in
                # it. Editing now only ever starts from the pencil button.
                rx.markdown(item.content_markdown, width="100%"),
            ),
            width="100%",
            spacing="1",
            align_items="start",
            min_width="0",
        ),
        width="100%",
        align="start",
        spacing="3",
        padding_y="0.4rem",
        key=item.id,
    )


def _activity_item(item: rx.Var) -> rx.Component:
    """Render one timeline row, dispatching on the item's kind.

    :param item: The activity item
    :type item: rx.Var
    :return: The row or card component
    :rtype: rx.Component
    """
    return rx.match(
        item.kind,
        ("comment", _comment_card(item)),
        _activity_event_row(item),
    )


def _comment_composer() -> rx.Component:
    """Create the composer used to post a new comment on the task.

    :return: The composer component
    :rtype: rx.Component
    """
    return rx.vstack(
        rich_text_component(
            value=TaskActivityState.new_comment_content,
            disabled=False,
            output_event=TaskActivityState.handle_new_comment_change,
            custom_style={"minHeight": "80px", "flex": "0", "backgroundColor": "var(--card-background)"},
        ),
        rx.hstack(
            rx.spacer(),
            rx.button(
                rx.cond(TaskActivityState.is_posting_comment, rx.spinner(size="2")),
                translate("task_activity.comment_button"),
                size="2",
                on_click=TaskActivityState.submit_comment,
                disabled=TaskActivityState.is_posting_comment,
            ),
            width="100%",
        ),
        width="100%",
        spacing="2",
        margin_top="1rem",
    )


def task_activity_content() -> rx.Component:
    """Create the Activity tab content: the history timeline interleaved with comments,
    and a composer to post a new one.

    :return: The activity content component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.cond(
            TaskActivityState.activity_items.length() > 0,
            rx.vstack(
                rx.foreach(TaskActivityState.activity_items, _activity_item),
                width="100%",
                spacing="1",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("history", size=48, color="gray"),
                    rx.text(
                        translate("task_activity.no_activity"),
                        size="4",
                        color="gray",
                        margin_top="1rem",
                    ),
                    spacing="2",
                    align="center",
                ),
                padding="3rem",
                width="100%",
            ),
        ),
        _comment_composer(),
        width="100%",
        spacing="3",
        on_mount=TaskActivityState.fetch_activity_on_mount,
    )
