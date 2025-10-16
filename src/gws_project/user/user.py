

from gws_core import EnumField, Model, UserDTO, UserGroup
from gws_project.core.project_db_manager import ProjectDbManager
from peewee import BooleanField, CharField


class User(Model):

    email: str = CharField(default=False, index=True)
    first_name: str = CharField(default=False)
    last_name: str = CharField(default=False)
    group: UserGroup = EnumField(choices=UserGroup,
                                 default=UserGroup.USER)
    is_active = BooleanField(default=True)

    photo: str = CharField(null=True)

    def to_dto(self) -> UserDTO:
        return UserDTO(
            id=self.id,
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            photo=self.photo
        )

    class Meta:
        table_name = 'gws_project_user'
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
