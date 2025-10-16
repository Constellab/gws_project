

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project_dto import ProjectDTO
from gws_project.user.user import User
from peewee import CharField, DateField, ForeignKeyField, TextField

from ..core.model_with_user import ModelWithUser


class Project(ModelWithUser):
    """
    Project model - Manages projects linked to companies

    Status values: 'active' (default), 'completed', 'archived', 'cancelled'
    """

    title = CharField(max_length=255, null=False)
    description = TextField(null=True)
    start_date = DateField(null=False, index=True)
    end_date = DateField(null=False, index=True)
    project_manager = ForeignKeyField(User, null=False)
    space_folder_id = CharField(max_length=36, unique=True, null=True)

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
            project_manager=self.project_manager.to_dto(),
            space_folder_id=self.space_folder_id
        )

    class Meta:
        table_name = 'gws_project_projects'
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
