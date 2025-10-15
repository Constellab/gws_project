


from gws_core import LazyAbstractDbManager
from peewee import DatabaseProxy


class ProjectDbManager(LazyAbstractDbManager):
    """
    DbManager class.

    Provides backend features for managing databases.
    """

    db = DatabaseProxy()

    _instance: 'ProjectDbManager' = None

    @classmethod
    def get_instance(cls) -> 'ProjectDbManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


    def get_name(self) -> str:
        return 'db'

    def get_brick_name(self) -> str:
        return 'gws_project'

