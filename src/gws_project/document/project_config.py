from gws_core import Model, NullableCharField
from gws_core.impl.file.local_file_store import LocalFileStore

from gws_project.core.project_db_manager import ProjectDbManager


class ProjectConfig(Model):
    """Single-row configuration table for the gws_project brick.

    Holds the id of the brick's dedicated ``LocalFileStore`` (project documents).
    ``LocalFileStore`` has no name column, so the chosen store's id is remembered
    here and reused across restarts. The row is created lazily by
    :meth:`get_instance`.
    """

    file_store_id = NullableCharField(max_length=36)

    @classmethod
    def get_instance(cls) -> "ProjectConfig":
        """Return the single config row, creating it if missing.

        :return: The single ProjectConfig row
        :rtype: ProjectConfig
        """
        config = cls.select().first()
        if config is not None:
            return config

        config = cls()
        config.save()
        return config

    def get_or_create_file_store(self) -> LocalFileStore:
        """Return the brick's dedicated LocalFileStore, creating it once.

        The store id is remembered on this config row so the same store is reused
        across restarts (and never collides with gws_core's default store).

        :return: The dedicated LocalFileStore of the brick
        :rtype: LocalFileStore
        """
        if self.file_store_id:
            store = LocalFileStore.get_by_id(self.file_store_id)
            if store is not None:
                return store

        store = LocalFileStore()
        store.save()
        self.file_store_id = store.id
        self.save()
        return store

    class Meta:
        table_name = "gws_project_config"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
