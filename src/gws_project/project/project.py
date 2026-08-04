from datetime import datetime

from gws_core import (
    NullableCharField,
    TypedCharField,
    TypedDateField,
    TypedForeignKeyField,
    TypedIntegerField,
    TypedRichTextDbField,
)

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project_dto import ProjectDTO, ProjectStatus
from gws_project.user.user import User

from ..core.model_with_user import ModelWithUser


class Project(ModelWithUser):
    """
    Project model - Manages projects linked to companies

    Status values: 'active' (default), 'completed', 'archived', 'cancelled'
    """

    title = TypedCharField(max_length=255)
    description = TypedRichTextDbField()
    start_date = TypedDateField(index=True)
    end_date = TypedDateField(index=True)
    project_manager = TypedForeignKeyField(User)
    # DEPRECATED - unused at runtime. Id of the Space folder that mirrored this
    # project before documents moved to local storage. Kept only for the
    # MigrateProjectDataFromSpace task; dropped in a later release.
    space_folder_id = NullableCharField(max_length=36, unique=True)
    progress = TypedIntegerField(default=0)

    def get_status(self) -> ProjectStatus:
        """Determine the current status of the project based on dates and progress.

        :return: The current status of the project
        :rtype: ProjectStatus
        """
        if self.progress >= 100:
            return ProjectStatus.COMPLETED
        elif self.progress > 0 or self.start_date <= datetime.now().date():
            return ProjectStatus.ACTIVE
        else:
            return ProjectStatus.DRAFT

    def to_dto(self) -> ProjectDTO:
        return ProjectDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
            description=self.description,
            start_date=self.start_date,
            end_date=self.end_date,
            start_date_text=self.start_date.strftime("%b %d, %Y"),
            end_date_text=self.end_date.strftime("%b %d, %Y"),
            project_manager=self.project_manager.to_dto(),
            progress=self.progress,
            status=self.get_status(),
        )

    class Meta:
        table_name = "gws_project_projects"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
