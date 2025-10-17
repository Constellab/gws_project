import reflex as rx
from gws_project.task.task_service import TaskService
from gws_reflex_main import ReflexMainState


class SubtaskListState(ReflexMainState):
    """State for managing the subtask list within a task detail page.

    This state handles deleting subtasks and reloading the parent task.
    """

    @rx.event(background=True)
    async def delete_subtask(self, subtask_id: str):
        """Delete a subtask and reload the parent task.

        :param subtask_id: The ID of the subtask to delete
        :type subtask_id: str
        """
        from ..task_detail_state import TaskDetailState

        main_state: ReflexMainState
        task_detail_state: TaskDetailState
        async with self:
            main_state = await self.get_state(ReflexMainState)
            task_detail_state = await self.get_state(TaskDetailState)

        try:
            # Delete the subtask
            with await main_state.authenticate_user():
                task_service = TaskService()
                task_service.delete_task(subtask_id)

            # Show success toast
            yield rx.toast.success("Subtask deleted successfully")

            # Reload the task to refresh the subtasks list
            async with self:
                if task_detail_state.task:
                    await task_detail_state.load_task(task_detail_state.task.id)

        except Exception as e:
            yield rx.toast.error(f"Error deleting subtask: {str(e)}")
