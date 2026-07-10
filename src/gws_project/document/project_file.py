import os

from gws_core import Model
from gws_core.impl.file.local_file_store import LocalFileStore
from peewee import BigIntegerField, CharField

from gws_project.core.project_db_manager import ProjectDbManager


class ProjectFile(Model):
    """A single stored file in the brick's dedicated LocalFileStore.

    The brick's central file registry: every stored file (uploaded project or
    task documents) is one ``ProjectFile`` row holding the store id plus the
    path RELATIVE to that store. Domain rows that need a file
    (``ProjectDocument`` of type FILE) reference a ``ProjectFile`` instead of
    re-implementing storage, so there is one file pattern for the whole brick.
    """

    file_store = CharField(max_length=36, null=False)
    path = CharField(max_length=1024, null=False)  # relative to the store root
    name = CharField(max_length=255, null=False)
    size = BigIntegerField(null=False, default=0)  # size in bytes

    def get_store(self) -> LocalFileStore | None:
        """The LocalFileStore this file lives in (None if it no longer exists).

        :return: The LocalFileStore or None
        :rtype: LocalFileStore | None
        """
        return LocalFileStore.get_by_id(self.file_store)

    def get_absolute_path(self) -> str | None:
        """Absolute path of the file on disk, or None if the store is gone.

        :return: The absolute path or None
        :rtype: str | None
        """
        store = self.get_store()
        if store is None:
            return None
        return os.path.join(store.path, self.path)

    def delete_file_from_store(self) -> None:
        """Delete the file node from the store (no-op if store or file is gone)."""
        store = self.get_store()
        if store is None:
            return
        store.delete_node_path(os.path.join(store.path, self.path))

    class Meta:
        table_name = "gws_project_file"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
