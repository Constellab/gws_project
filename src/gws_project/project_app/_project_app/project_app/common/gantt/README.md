# Gantt Chart Component

A Reflex wrapper for the `gantt-task-react` library that displays projects and their root tasks in a Gantt chart view.

## Installation

The `gantt-task-react` package has been added to `rxconfig.py` in the `frontend_packages` list. Reflex will automatically install it when you run the app.

## Usage

### Basic Example

```python
import reflex as rx
from project_app.common.gantt.gantt import gantt_chart, build_gantt_data_from_projects
from gws_project.project.project_service import ProjectService

class GanttPageState(rx.State):
    gantt_data: dict = {}

    def on_mount(self):
        """Load projects with root tasks when page mounts."""
        project_service = ProjectService()
        projects_with_tasks = project_service.get_current_user_projects_with_root_tasks()

        # Convert to gantt data format
        self.gantt_data = build_gantt_data_from_projects(projects_with_tasks).model_dump()

    def handle_task_click(self, task_id: str):
        """Handle when a user clicks on a task in the Gantt chart."""
        print(f"Task clicked: {task_id}")
        # Navigate to task detail or open a dialog

def gantt_page():
    return rx.box(
        rx.heading("Project Timeline", size="8"),
        gantt_chart(
            data=GanttPageState.gantt_data,
            view_mode="Month",  # Options: 'Day', 'Week', 'Month', 'Year'
            on_task_click=GanttPageState.handle_task_click,
        ),
        padding="20px",
    )
```

### Using the Service Method

The `ProjectService.get_current_user_projects_with_root_tasks()` method returns a list of `ProjectWithRootTasksDTO` objects that contain:

- **project**: Full project details (title, dates, progress, etc.)
- **root_tasks**: List of root-level tasks (no subtasks)

### Helper Function

The `build_gantt_data_from_projects()` function converts the service data into the format expected by the Gantt chart:

```python
from project_app.common.gantt.gantt import build_gantt_data_from_projects

projects_with_tasks = project_service.get_current_user_projects_with_root_tasks()
gantt_data = build_gantt_data_from_projects(projects_with_tasks)
```

## Features

- **Multiple View Modes**: Switch between Day, Week, Month, and Year views
- **Color-Coded Status**: Tasks are colored based on their status (TODO, DOING, DONE)
- **Progress Bars**: Visual progress indicators on each task
- **Interactive Tooltips**: Hover over tasks to see detailed information
- **Project Grouping**: Tasks are automatically grouped under their parent projects
- **Click Events**: Handle task clicks to navigate or show details

## Data Structure

The Gantt chart expects data in this format:

```python
GanttDataDTO(
    tasks=[
        GanttTaskDTO(
            id="project-1",
            name="Project Name",
            start="2024-01-01",
            end="2024-03-31",
            progress=45,
            type="project",
            styles={...}
        ),
        GanttTaskDTO(
            id="task-1",
            name="Task Name",
            start="2024-01-01",
            end="2024-01-15",
            progress=100,
            type="task",
            project="project-1",
            styles={...}
        )
    ]
)
```

## Customization

### Task Colors

Task colors are automatically set based on status:
- **TODO**: Blue (`#2196f3`)
- **DOING**: Orange (`#ff9800`)
- **DONE**: Green (`#4caf50`)
- **PROJECT**: Dark Blue (`#1976d2`)

You can customize colors by modifying the `get_status_color()` function in [gantt.py](gantt.py#L90-L110).

## Component Props

- `data`: GanttDataDTO - The Gantt chart data
- `view_mode`: str - View mode: 'Day', 'Week', 'Month', or 'Year' (default: 'Month')
- `on_task_click`: EventHandler - Callback when a task is clicked (receives task ID)
