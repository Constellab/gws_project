
import reflex as rx
from gws_project.task.task_dto import TaskDTO
from gws_project.template.task_template_dto import TaskTemplateDTO


def task_icon_component(task: TaskDTO, **kwargs) -> rx.Component:
    """Create an icon component indicating if the task allows subtasks.

    :param task: The task data transfer object
    :type task: TaskDTO
    :return: The task icon component
    :rtype: rx.Component
    """
    return rx.text(rx.cond(task.allow_subtasks, "📁", "📋"), **kwargs),


def task_template_icon_component(task_template: TaskTemplateDTO, **kwargs) -> rx.Component:
    """Create an icon component indicating if the task template allows subtasks.

    :param task_template: The task template data transfer object
    :type task_template: TaskTemplateDTO
    :return: The task template icon component
    :rtype: rx.Component
    """
    return rx.cond(
        task_template.allow_subtasks,
        rx.icon("folder", **kwargs),
        rx.icon("file", **kwargs)
    )
