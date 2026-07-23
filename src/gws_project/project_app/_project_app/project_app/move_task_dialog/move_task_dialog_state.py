import reflex as rx
from gws_project.project.project_dto import ProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskDTO
from gws_project.task.task_service import TaskService
from gws_reflex_main import ReflexDialogCloseEvent, ReflexMainState


class MoveTaskDialogState(rx.State):
    """State for the move task dialog: a hierarchical, folder-style browser (Projects ->
    a project's root tasks -> subtasks -> ...) used to pick the destination project
    and/or parent task for a task being moved.

    Only tasks that allow subtasks are shown, since they are the only valid "folders"
    a task can be moved into; the moved task and its own subtree are excluded to avoid
    creating a cycle.
    """

    dialog_opened: bool = False
    is_loading: bool = False

    _task: TaskDTO | None = None
    _callback_after_close: ReflexDialogCloseEvent[Task] | None = None

    # Current browse position: current_project is None while browsing the top-level
    # project list. breadcrumb_tasks holds the chain of ancestor "folder" tasks from
    # the project's root down to the current level (empty while browsing that root).
    current_project: ProjectDTO | None = None
    breadcrumb_tasks: list[TaskDTO] = []

    # "Folder" entries at the current level
    projects: list[ProjectDTO] = []
    tasks: list[TaskDTO] = []

    @rx.var
    def task_title(self) -> str:
        """Title of the task being moved, for display in the dialog header.

        :return: The task title, or an empty string if no task is being moved
        :rtype: str
        """
        return self._task.title if self._task else ""

    @rx.var
    def can_confirm_move(self) -> bool:
        """Whether a destination project is selected, so the move can be confirmed.

        :return: True if a destination project is currently browsed
        :rtype: bool
        """
        return self.current_project is not None

    def _current_parent_task_id(self) -> str | None:
        """The ID of the task whose children are currently listed, or None while
        browsing the project's root level.

        :return: The current parent task ID, or None
        :rtype: Optional[str]
        """
        return self.breadcrumb_tasks[-1].id if self.breadcrumb_tasks else None

    async def open_move_dialog(
        self, task: TaskDTO, callback_after_close: ReflexDialogCloseEvent[Task] | None = None
    ):
        """Open the dialog, browsing to the task's current project/parent by default.

        :param task: The task to move
        :type task: TaskDTO
        :param callback_after_close: Optional callback invoked with the moved task after the move
        :type callback_after_close: Optional[ReflexDialogCloseEvent[Task]]
        """
        self._task = task
        self._callback_after_close = callback_after_close

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            project = ProjectService().get_project(task.project_id)
            # immediate parent first, root last
            ancestors = TaskService().get_task(task.id).get_ancestors()

        self.current_project = project.to_dto()
        self.breadcrumb_tasks = [ancestor.to_dto() for ancestor in reversed(ancestors)]

        await self._load_tasks()
        self.dialog_opened = True

    @rx.event
    async def navigate_to_projects_root(self):
        """Navigate back to the top-level project list."""
        self.current_project = None
        self.breadcrumb_tasks = []
        await self._load_projects()

    @rx.event
    async def navigate_to_project_root(self):
        """Navigate back to the root level of the current project."""
        self.breadcrumb_tasks = []
        await self._load_tasks()

    @rx.event
    async def navigate_to_breadcrumb_task(self, task_id: str):
        """Navigate to a task in the current breadcrumb trail, truncating anything after it.

        :param task_id: The ID of the breadcrumb task to navigate to
        :type task_id: str
        """
        index = next((i for i, t in enumerate(self.breadcrumb_tasks) if t.id == task_id), None)
        if index is None:
            return
        self.breadcrumb_tasks = self.breadcrumb_tasks[: index + 1]
        await self._load_tasks()

    @rx.event
    async def navigate_to_project(self, project: ProjectDTO):
        """Navigate into a project from the top-level project list.

        :param project: The project to browse into
        :type project: ProjectDTO
        """
        self.current_project = project
        self.breadcrumb_tasks = []
        await self._load_tasks()

    @rx.event
    async def navigate_to_task(self, task: TaskDTO):
        """Navigate into a task, listing its subtasks.

        :param task: The task to browse into
        :type task: TaskDTO
        """
        self.breadcrumb_tasks = self.breadcrumb_tasks + [task]
        await self._load_tasks()

    async def _load_projects(self):
        """Load the top-level project list."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            projects = ProjectService().get_current_user_projects()
            self.projects = [project.to_dto() for project in projects]

    async def _load_tasks(self):
        """Load the "folder" tasks at the current level: the root tasks of the current
        project, or the subtasks of the current breadcrumb task.
        """
        if not self.current_project:
            self.tasks = []
            return

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_service = TaskService()
            tasks = task_service.get_navigable_child_tasks(
                self.current_project.id,
                parent_task_id=self._current_parent_task_id(),
                exclude_task_id=self._task.id if self._task else None,
            )
            self.tasks = [task.to_dto() for task in tasks]

    @rx.event
    def close_dialog(self):
        """Close the dialog and clear its state."""
        self.dialog_opened = False
        self._clear_state()

    def _clear_state(self):
        """Reset all dialog state."""
        self._task = None
        self._callback_after_close = None
        self.current_project = None
        self.breadcrumb_tasks = []
        self.projects = []
        self.tasks = []

    @rx.event(background=True)  # type: ignore
    async def confirm_move(self):
        """Move the task to the currently browsed location: the current project, and
        the current breadcrumb task as parent, or the project's root if none.
        """
        async with self:
            self.is_loading = True
            main_state = await self.get_state(ReflexMainState)
            task_id = self._task.id if self._task else None
            project_id = self.current_project.id if self.current_project else None
            parent_task_id = self._current_parent_task_id()
            callback_after_close = self._callback_after_close

        try:
            if not task_id or not project_id:
                yield rx.toast.error("Please select a destination project.")
                return

            with await main_state.authenticate_user():
                task_service = TaskService()
                task = task_service.move_task(task_id, project_id, parent_task_id)

            yield rx.toast.success("Task moved successfully")

            if callback_after_close:
                await callback_after_close(task)
        except Exception as e:
            yield rx.toast.error(str(e))
            return
        finally:
            async with self:
                self.is_loading = False

        async with self:
            self.close_dialog()
