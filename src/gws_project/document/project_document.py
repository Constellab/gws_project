from gws_core import (
    NullableCharField,
    NullableForeignKeyField,
    NullableRichTextDbField,
    TypedCharField,
    TypedEnumField,
    TypedForeignKeyField,
)
from peewee import ModelSelect

from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.document.document_dto import (
    ProjectDocumentDTO,
    ProjectDocumentType,
    ProjectNoteDTO,
)
from gws_project.document.project_file import ProjectFile
from gws_project.project.project import Project
from gws_project.task.task import Task

PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE = "project_document"
"""Rich text object type owning the images of a document's content.

The images of a NOTE document are stored by ``RichTextFileService`` in a directory
dedicated to the document (``.../project_document/{document_id}``), so they are deleted
with the document (see ``DocumentService._delete_document_and_file``).
"""


class ProjectDocument(ModelWithUser):
    """A document attached to a project or a task.

    Single table for both uploaded files and rich-text notes so the mixed
    documents list is one paginated, date-ordered query:
    - ``type = FILE``: the bytes live in a ``ProjectFile`` (the brick's central
      file registry backed by the dedicated ``LocalFileStore``); this row only
      references it.
    - ``type = NOTE``: the rich-text content lives in ``content`` (kept in DB,
      transactional with edits, consistent with project/task descriptions). The
      images of that content live on disk, see
      ``PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE``.

    ``task`` points to the EXACT task the document belongs to (including
    subtasks), replacing the Space tag ``task:<id>``; ``task`` is null for
    project-level documents.

    ``space_document_id`` records the id of the Space object this row was
    migrated from (provenance + idempotency of the migration task).
    """

    project = TypedForeignKeyField(Project, on_delete="CASCADE", backref="+")
    task = NullableForeignKeyField(Task, on_delete="CASCADE", backref="+")
    type = TypedEnumField(choices=ProjectDocumentType, max_length=10)
    name = TypedCharField(max_length=255)
    file = NullableForeignKeyField(ProjectFile, backref="+")
    content = NullableRichTextDbField()
    space_document_id = NullableCharField(max_length=36, unique=True)

    @classmethod
    def get_project_documents_query(cls, project_id: str) -> ModelSelect:
        """Query the documents attached directly to a project (task is null),
        newest modified first.

        :param project_id: The ID of the project
        :type project_id: str
        :return: The peewee query
        :rtype: ModelSelect
        """
        return (
            cls.select()
            .where((cls.project == project_id) & (cls.task.is_null()))
            .order_by(cls.last_modified_at.desc())
        )

    @classmethod
    def get_task_documents_query(cls, task_id: str) -> ModelSelect:
        """Query the documents attached to a task, newest modified first.

        :param task_id: The ID of the task
        :type task_id: str
        :return: The peewee query
        :rtype: ModelSelect
        """
        return cls.select().where(cls.task == task_id).order_by(cls.last_modified_at.desc())

    @classmethod
    def count_project_documents(cls, project_id: str) -> int:
        """Count the documents attached directly to a project (task is null).

        :param project_id: The ID of the project
        :type project_id: str
        :return: Number of documents
        :rtype: int
        """
        return cls.select().where((cls.project == project_id) & (cls.task.is_null())).count()

    @classmethod
    def count_task_documents(cls, task_id: str) -> int:
        """Count the documents attached to a task.

        :param task_id: The ID of the task
        :type task_id: str
        :return: Number of documents
        :rtype: int
        """
        return cls.select().where(cls.task == task_id).count()

    @classmethod
    def get_documents_of_project_and_subtree(cls, project_id: str) -> list["ProjectDocument"]:
        """Get ALL documents of a project, including the ones attached to its tasks.

        Used to clean up file nodes before a project deletion.

        :param project_id: The ID of the project
        :type project_id: str
        :return: List of documents
        :rtype: List[ProjectDocument]
        """
        return list(cls.select().where(cls.project == project_id))

    @classmethod
    def space_document_already_migrated(cls, space_document_id: str) -> bool:
        """Check whether a Space document was already migrated locally.

        :param space_document_id: The id of the Space document
        :type space_document_id: str
        :return: True if a local document already references this Space id
        :rtype: bool
        """
        return cls.select().where(cls.space_document_id == space_document_id).exists()

    def to_dto(self) -> ProjectDocumentDTO:
        """Convert to a ProjectDocumentDTO for display in the frontend.

        :return: The DTO
        :rtype: ProjectDocumentDTO
        """
        return ProjectDocumentDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            name=self.name,
            type=self.type,
            project_id=self.project.id,
            task_id=self.task.id if self.task else None,
            size=self.file.size if self.file else None,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
        )

    def to_note_dto(self) -> ProjectNoteDTO:
        """Convert to a ProjectNoteDTO including the rich-text content.

        :return: The note DTO
        :rtype: ProjectNoteDTO
        """
        return ProjectNoteDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            name=self.name,
            type=self.type,
            project_id=self.project.id,
            task_id=self.task.id if self.task else None,
            size=None,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            content=self.content,
        )

    class Meta:
        table_name = "gws_project_documents"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
