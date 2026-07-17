# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

This is a Reflex web application for project and task management, part of the GWS Project brick. The app provides a multi-page interface with project lists, project details, task details, and a kanban board view.

## Running the Application

Run the Reflex app in development mode from the brick root directory:
```bash
gws reflex run src/gws_project/project_app/_project_app/dev_config.json
```

The app requires `GWS_REFLEX_API_URL` environment variable to be set (configured automatically by gws_reflex_base.ReflexInit).

## Architecture

### Page Structure

The app has 4 main pages defined in `project_app/project_app.py`:

1. **Project List** (`/`) - Landing page showing all projects
2. **Project Detail** (`/project/[project_id_param]`) - Project overview with tasks and documents
3. **Task Detail** (`/task/[task_id_param]`) - Individual task with subtasks
4. **Kanban Board** (`/kanban`) - Global task kanban across all projects

Each page follows the pattern:
- Component file: `[module]_component.py` - UI components
- State file: `[module]_state.py` - State management and event handlers

### State Management

All states inherit from `gws_reflex_main.ReflexMainState` which provides:
- `check_authentication()` - Verify user is logged in
- `authenticate_user()` - Context manager for authenticated operations
- `get_state(StateClass)` - Access another state

**Key States:**

- `ProjectPageState` (in `common/`) - Shared caching layer for Project/Task objects extracted from URL parameters. Used by multiple pages to avoid redundant DB queries.
- `ProjectListState` - Manages project list loading and creation
- `ProjectDetailState` - Handles project view modes (list/kanban/documents)
- `TaskListState` - Loads and manages tasks for a project or parent task
- `TaskDetailState` - Shows single task details
- `KanbanState` - Global kanban with filtering (project, user, date, search)

**Reactive Variables Pattern:**
```python
@rx.var
async def computed_value(self) -> SomeType:
    """Computed property that auto-updates when dependencies change"""
    other_state = await self.get_state(OtherState)
    return await other_state.some_method()
```

**Event Handler Pattern:**
```python
async def on_load(self):
    """Called by page's on_load hook"""
    if not await self.check_authentication():
        return

    with await self.authenticate_user():
        service = ProjectService()
        self.items = service.get_items()
```

### Component Patterns

**Layout Components:**
- `page_layout(content)` - Main wrapper with left sidebar navigation
- `detail_page_layout(main_content, sidebar_content)` - Two-column layout with breadcrumb

**Reusable Components:**
- `status_chip(status, on_status_change, allow_subtask)` - Task status chip
- `priority_chip(priority, on_priority_change, allow_subtask)` - Task priority chip
- `task_table_component(tasks, empty_message)` - Task list table
- Components from `gws_reflex_main`: `user_inline_component()`, `user_profile_picture()`, `user_select()`, `group_select()`

**Dialog Pattern:**
```python
def _form_content() -> rx.Component:
    """Form fields"""
    return rx.vstack(...)

def _dialog() -> rx.Component:
    """Base dialog without trigger"""
    return form_dialog_component(
        title="Dialog Title",
        form_content=_form_content(),
        state=FormDialogState,
        on_submit_method="submit"
    )

def my_dialog() -> rx.Component:
    """Dialog with trigger button"""
    return rx.dialog.root(
        rx.dialog.trigger(rx.button("Open")),
        _dialog(),
    )
```

Dialog states inherit from `gws_reflex_main.FormDialogState` and implement:
- Form field variables (e.g., `form_title: str`)
- `open_create_dialog()` or `open_update_dialog()` methods
- `_create()` or `_update()` submission handlers

**Callback Pattern for Dialog Updates:**
```python
# In parent state
async def open_create_dialog(self):
    form_state = await self.get_state(FormDialogState)
    await form_state.open_create_dialog(
        callback_after_close=self._on_dialog_close
    )

async def _on_dialog_close(self, created_item):
    self.items.append(created_item)
```

### URL Parameter Caching

The `ProjectPageState` (in `common/project_page_state.py`) implements smart caching:
- Detects `project_id_param` or `task_id_param` from URL
- Caches loaded objects to avoid redundant DB queries
- Used by: ProjectDetail, TaskDetail, TaskList, Breadcrumb, Documents

Access pattern:
```python
project_page_state = await self.get_state(ProjectPageState)
current_project = await project_page_state.project()
```

### Service Integration

All database operations go through service classes:
- `ProjectService` - Project CRUD operations
- `TaskService` - Task CRUD operations
- `UserService` - User operations
- `DocumentService` - Document/note operations (local storage: brick DB + dedicated lab file store)
- `SpaceService` - User/group directory only (list groups, resolve group users; from gws_core)

Services are called within authenticated context:
```python
with await self.authenticate_user():
    service = ProjectService()
    result = service.method()
```

### DTOs (Data Transfer Objects)

Backend models are converted to DTOs for frontend use:
- `project.to_dto()` → `ProjectDTO`
- `task.to_dto()` → `TaskDTO`
- Keeps frontend decoupled from backend models

## Development Best Practices

### Import Pattern
- From `gws_reflex_main`: `from gws_reflex_main import ReflexMainState, FormDialogState, main_component, ...`
- From `gws_core`: Use main module imports (e.g., `from gws_core import BaseModelDTO`)
- From other app modules: Relative imports (e.g., `from .task_list.task_list_state import TaskListState`)

### State Best Practices
- Always authenticate: Use `check_authentication()` or `authenticate_user()` context
- Single responsibility: Each state manages one page or dialog
- Reactive composition: Use `@rx.var` for computed properties that depend on other states
- Avoid redundant queries: Use `ProjectPageState` caching when accessing current project/task

### Component Best Practices
- Pure functions: Components are pure functions returning `rx.Component`
- Reusable: Extract common patterns to `common/` directory
- Conditional rendering: Use `rx.cond()` for show/hide logic
- List rendering: Use `rx.foreach()` for dynamic lists

### Naming Conventions
- State classes: `[Module]State` (e.g., `ProjectListState`)
- Component functions: `[name]_component()` (e.g., `task_table_component()`)
- Dialog components: `[name]_dialog()` (e.g., `create_project_dialog()`)
- Internal helpers: Prefix with `_` (e.g., `_form_content()`, `_on_dialog_close()`)

## Common Development Tasks

### Adding a New Page
1. Create directory: `project_app/[page_name]/`
2. Create state file: `[page_name]_state.py` with `[PageName]State(ReflexMainState)`
3. Create component file: `[page_name]_component.py` with `[page_name]_page() -> rx.Component`
4. Register in `project_app.py`: Add `@rx.page()` decorator and route

### Adding a Dialog
1. Create state in relevant module: `[dialog]_dialog_state.py` inheriting `FormDialogState`
2. Implement form fields, `open_[create/update]_dialog()`, and `_[create/update]()` methods
3. Create component: `[dialog]_dialog_component.py` with `_form_content()`, `_dialog()`, and wrapper
4. Add dialog callback in parent state to refresh data

### Adding a Reusable Component
1. Create in `common/`: `[name]_component.py`
2. Function signature: `def [name]_component(param1: Type, ...) -> rx.Component`
3. Import and use in other components

## Configuration Files

- `rxconfig.py` - Reflex configuration (app name, API URL, frontend packages)
- `dev_config.json` - Development configuration (app directory, user email)
