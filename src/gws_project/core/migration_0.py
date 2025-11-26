from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project import Project
from gws_project.task.task import Task


@brick_migration(
    "0.1.2", short_description="Adding progress to task and project", db_manager=ProjectDbManager.get_instance()
)
class Migration012(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        # Add progress column to Task table
        sql_migrator.add_column_if_not_exists(Task, Task.progress)
        # Add progress column to Project table
        sql_migrator.add_column_if_not_exists(Project, Project.progress)
        sql_migrator.migrate()

        # Refresh all tasks to set progress based on status
        all_tasks: list[Task] = list(Task.select())
        for task in all_tasks:
            if task.allow_subtasks:
                task.update_from_subtasks()
            else:
                task.set_status(task.status)
            task.save(skip_hook=True)

        # Refresh all projects to set progress based on root tasks
        all_projects: list[Project] = list(Project.select())
        for project in all_projects:
            root_tasks = Task.get_root_tasks_of_project(project.id)
            if not root_tasks:
                project.progress = 0
            else:
                total_progress = sum(task.progress for task in root_tasks)
                project.progress = total_progress // len(root_tasks)
            project.save(skip_hook=True)
