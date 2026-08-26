import os

from gws_core import FileHelper, Settings
from gws_core.impl.file.local_file_store import LocalFileStore

from gws_project.document.project_config import ProjectConfig
from gws_project.document.project_file import ProjectFile


class ProjectFileService:
    """Storage of every file of the brick, in its dedicated ``LocalFileStore``.

    The single entry point to put bytes on disk: whatever owns the file
    (a ``ProjectDocument`` of type FILE, a ``Company`` logo) only keeps a
    reference to the returned :class:`ProjectFile` row, so there is one file
    pattern - and one store - for the whole brick.

    File operations are NOT transactional: a caller running inside a DB
    transaction must delete the file from the store only once the transaction
    is committed (a rollback cannot bring the bytes back).
    """

    @classmethod
    def get_store(cls) -> LocalFileStore:
        """Return the brick's dedicated LocalFileStore (find-or-create).

        :return: The dedicated LocalFileStore
        :rtype: LocalFileStore
        """
        return ProjectConfig.get_instance().get_or_create_file_store()

    @classmethod
    def create_from_path(cls, file_path: str, name: str | None = None) -> ProjectFile:
        """Move a file into the store and register it as a ProjectFile.

        The source file is MOVED, not copied. If the ProjectFile row cannot be
        saved, the moved node is removed from the store so no orphan file is left.

        :param file_path: The path of the source file (MOVED into the store)
        :type file_path: str
        :param name: The name to store the file under (defaults to the source file name)
        :type name: str | None
        :return: The created ProjectFile row
        :rtype: ProjectFile
        """
        file_name = name or os.path.basename(file_path)

        store = cls.get_store()
        # the store moves the file and de-duplicates the destination name
        node = store.add_node_from_path(file_path, file_name)

        try:
            project_file = ProjectFile(
                file_store=store.id,
                path=os.path.relpath(node.path, store.path),
                name=file_name,
                size=os.path.getsize(node.path),
            )
            project_file.save()
            return project_file
        except Exception:
            # remove the moved node so a DB failure doesn't leave an orphan file
            store.delete_node_path(node.path)
            raise

    @classmethod
    def create_from_bytes(cls, data: bytes, name: str) -> ProjectFile:
        """Write bytes to the store and register them as a ProjectFile.

        Used for content the app receives in memory (an uploaded logo) rather
        than as a file on disk. The bytes go through a temp file so the store
        does the naming and de-duplication exactly as for an uploaded document.

        :param data: The raw bytes to store
        :type data: bytes
        :param name: The name to store the file under
        :type name: str
        :return: The created ProjectFile row
        :rtype: ProjectFile
        """
        temp_dir = Settings.make_temp_dir()
        temp_path = os.path.join(temp_dir, name)

        try:
            with open(temp_path, "wb") as file_handle:
                file_handle.write(data)

            return cls.create_from_path(temp_path, name)
        finally:
            FileHelper.delete_dir(temp_dir)
