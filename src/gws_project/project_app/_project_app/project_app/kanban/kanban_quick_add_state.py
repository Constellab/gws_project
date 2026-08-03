import reflex as rx
from gws_project.project.project_dto import ProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import CreateTaskDTO, TaskDTO, TaskStatus
from gws_project.task.task_service import TaskService
from gws_reflex_main import ReflexMainState

from .kanban_state import KanbanState


class KanbanQuickAddState(rx.State):
    """State for the inline "quick add task" row shown at the bottom of each Kanban
    column (GitHub Projects style: no dialog).

    The destination project/folder is picked with the same hierarchical, folder-style
    browser (Projects -> a project's root tasks -> subtasks -> ...) used by the "Move
    Task" dialog, reusing `TaskService.get_navigable_child_tasks`. Only one column's
    quick-add row can be active at a time, so a single top-level state is enough.
    """

    # Which column's quick-add row is currently expanded ("" means none)
    active_column_id: str = ""
    title: str = ""
    is_creating: bool = False

    # Whether the destination browser panel is expanded
    browse_open: bool = False

    # Current browse position: current_project is None while browsing the top-level
    # project list. breadcrumb_tasks holds the chain of ancestor "folder" tasks from
    # the project's root down to the current level (empty while browsing that root).
    # The current position also doubles as the currently chosen destination.
    current_project: ProjectDTO | None = None
    breadcrumb_tasks: list[TaskDTO] = []

    # "Folder" entries at the current level
    projects: list[ProjectDTO] = []
    tasks: list[TaskDTO] = []

    @rx.var
    def current_project_title(self) -> str:
        """Label of the currently browsed destination, or "" if none chosen yet.

        Reflects the deepest level currently browsed: the last breadcrumb task's title
        if browsing inside a folder task, otherwise the project's own title.

        :return: The destination label, or ""
        :rtype: str
        """
        if not self.current_project:
            return ""
        if self.breadcrumb_tasks:
            return self.breadcrumb_tasks[-1].title
        return self.current_project.title

    @rx.var
    def can_submit(self) -> bool:
        """Whether a title is filled in and a destination project has been chosen.

        :return: True if the quick-add task can be created
        :rtype: bool
        """
        return bool(self.title.strip()) and self.current_project is not None

    def _current_parent_task_id(self) -> str | None:
        """The ID of the task whose children are currently listed, or None while
        browsing the project's root level.

        :return: The current parent task ID, or None
        :rtype: Optional[str]
        """
        return self.breadcrumb_tasks[-1].id if self.breadcrumb_tasks else None

    @rx.event
    async def open_quick_add(self, column_id: str):
        """Expand the quick-add row for a given column.

        :param column_id: The status column id ("BACKLOG", "TODO", "DOING", "DONE")
        :type column_id: str
        """
        self.active_column_id = column_id
        self.title = ""
        self.browse_open = False
        self.current_project = None
        self.breadcrumb_tasks = []
        await self._load_projects()

    @rx.event
    def cancel_quick_add(self):
        """Collapse the quick-add row and clear its state."""
        self.active_column_id = ""
        self.title = ""
        self.browse_open = False
        self.current_project = None
        self.breadcrumb_tasks = []
        self.projects = []
        self.tasks = []

    @rx.event
    def set_title(self, value: str):
        """Update the task title being typed.

        :param value: The new title
        :type value: str
        """
        self.title = value

    @rx.event
    def toggle_browse(self):
        """Open or close the destination browser panel."""
        self.browse_open = not self.browse_open

    @rx.event
    def select_here(self):
        """Confirm the currently browsed level as the destination and close the panel."""
        self.browse_open = False

    @rx.event
    async def navigate(self, kind: str, target_id: str):
        """Navigate the destination browser.

        :param kind: One of "projects_root", "project_root", "project", "task",
            "breadcrumb_task"
        :type kind: str
        :param target_id: The project/task ID to navigate to (unused for
            "projects_root"/"project_root")
        :type target_id: str
        """
        if kind == "projects_root":
            self.current_project = None
            self.breadcrumb_tasks = []
            await self._load_projects()
        elif kind == "project_root":
            self.breadcrumb_tasks = []
            await self._load_tasks()
        elif kind == "project":
            project = next((p for p in self.projects if p.id == target_id), None)
            if not project:
                return
            self.current_project = project
            self.breadcrumb_tasks = []
            await self._load_tasks()
        elif kind == "task":
            task = next((t for t in self.tasks if t.id == target_id), None)
            if not task:
                return
            self.breadcrumb_tasks = self.breadcrumb_tasks + [task]
            await self._load_tasks()
        elif kind == "breadcrumb_task":
            index = next((i for i, t in enumerate(self.breadcrumb_tasks) if t.id == target_id), None)
            if index is None:
                return
            self.breadcrumb_tasks = self.breadcrumb_tasks[: index + 1]
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
                self.current_project.id, parent_task_id=self._current_parent_task_id()
            )
            self.tasks = [task.to_dto() for task in tasks]

    @rx.event(background=True)  # type: ignore
    async def submit(self):
        """Create the task in the currently chosen project/folder, with the status of
        the column the quick-add row was opened from.
        """
        async with self:
            title = self.title.strip()
            column_id = self.active_column_id
            project_id = self.current_project.id if self.current_project else None
            parent_task_id = self._current_parent_task_id()
            main_state = await self.get_state(ReflexMainState)

        if not title or not project_id:
            yield rx.toast.error("Please enter a title and choose a project.")
            return

        async with self:
            self.is_creating = True

        try:
            status = TaskStatus[column_id]
            # start_date/end_date are typed as optional but have no default, so pydantic
            # requires them to be passed explicitly; None defers to the project's own
            # dates (see TaskService._build_task_from_dto).
            task_dto = CreateTaskDTO(
                title=title,
                start_date=None,
                end_date=None,
                status=status,
                allow_subtasks=False,
            )

            with await main_state.authenticate_user():
                task_service = TaskService()
                if parent_task_id:
                    task = task_service.create_sub_task(parent_task_id, task_dto)
                else:
                    task = task_service.create_root_task(project_id, task_dto)

            async with self:
                kanban_state = await self.get_state(KanbanState)
                await kanban_state.add_task(task)
                self.cancel_quick_add()
        except Exception as e:
            yield rx.toast.error(str(e))
        finally:
            async with self:
                self.is_creating = False
