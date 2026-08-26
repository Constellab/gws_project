import base64
import os

from gws_core import FileHelper, Model, TypedBigIntegerField, TypedCharField
from gws_core.impl.file.local_file_store import LocalFileStore

from gws_project.core.project_db_manager import ProjectDbManager


class ProjectFile(Model):
    """A single stored file in the brick's dedicated LocalFileStore.

    The brick's central file registry: every stored file (uploaded project or
    task documents) is one ``ProjectFile`` row holding the store id plus the
    path RELATIVE to that store. Domain rows that need a file
    (``ProjectDocument`` of type FILE) reference a ``ProjectFile`` instead of
    re-implementing storage, so there is one file pattern for the whole brick.
    """

    file_store = TypedCharField(max_length=36)
    path = TypedCharField(max_length=1024)  # relative to the store root
    name = TypedCharField(max_length=255)
    size = TypedBigIntegerField(default=0)  # size in bytes

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

    def read_bytes(self) -> bytes | None:
        """Read the whole content of the file, or None if it is no longer on disk.

        :return: The file content, or None if the store or the file is gone
        :rtype: bytes | None
        """
        absolute_path = self.get_absolute_path()
        if absolute_path is None or not os.path.exists(absolute_path):
            return None

        with open(absolute_path, "rb") as file_handle:
            return file_handle.read()

    def to_data_url(self) -> str | None:
        """Return the file content as a base64 ``data:`` URL.

        The store is not served over HTTP, so an image stored here is embedded
        in the page rather than linked (see ``CompanyService.get_logo_data_url``).

        :return: The data URL, or None if the file is no longer on disk
        :rtype: str | None
        """
        content = self.read_bytes()
        if content is None:
            return None

        mime_type = FileHelper.get_mime(self.get_absolute_path()) or "application/octet-stream"
        return f"data:{mime_type};base64,{base64.b64encode(content).decode()}"

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
