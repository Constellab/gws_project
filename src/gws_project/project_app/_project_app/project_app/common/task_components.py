
import reflex as rx
from gws_project.task.task_dto import TaskDTO


def task_icon_component(task: TaskDTO, **kwargs) -> rx.Component:
    """Create an icon component indicating if the task allows subtasks.

    :param task: The task data transfer object
    :type task: TaskDTO
    :return: The task icon component
    :rtype: rx.Component
    """
    return rx.cond(
        task.allow_subtasks,
        rx.icon("folder", **kwargs),
        rx.icon("file", **kwargs)
    )
