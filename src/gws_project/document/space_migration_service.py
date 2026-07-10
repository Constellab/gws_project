import os
from collections.abc import Callable

from gws_core import (
    SearchOperator,
    Settings,
    SpaceHierarchyObjectDTO,
    SpaceHierarchyObjectSearchParams,
    SpaceService,
    Tag,
)

from gws_project.document.document_service import DocumentService
from gws_project.document.project_document import ProjectDocument
from gws_project.project.project import Project
from gws_project.task.task import Task

# key of the Space tag that linked a document to a task (legacy Space storage)
SPACE_TASK_TAG_KEY = "task"

# Space object types the migration knows how to convert locally
FILE_OBJECT_TYPE = "DOCUMENT"
NOTE_OBJECT_TYPE = "CONSTELLAB_DOCUMENT"

_PAGE_SIZE = 50


class SpaceMigrationService:
    """One-off, idempotent migration of gws_project data out of Space.

    For each project that still has a ``space_folder_id``, copies the content
    of its Space folders into local storage:
    - Space ``DOCUMENT`` objects are downloaded and stored as FILE documents.
    - Space ``CONSTELLAB_DOCUMENT`` objects are converted to local NOTE
      documents (content fetched via the Space API).
    - Task documents (Space tag ``task:<task_id>`` in the root task's folder)
      are attached to the exact task; documents whose tag matches no existing
      task are attached to the root task and flagged as orphans.
    - Other object types are skipped and listed in the report.

    Idempotent (migrated Space ids are recorded on ``space_document_id`` and
    skipped on re-run), error-resilient (per-document errors are reported and
    never abort the run) and non-destructive (Space is never written to).

    :param space_service: The SpaceService to use (mockable in tests)
    :type space_service: Optional[SpaceService]
    :param dry_run: If True, only report what would be migrated without writing
    :type dry_run: bool
    :param log_error: Optional callback called with each per-document error message
    :type log_error: Optional[Callable[[str], None]]
    """

    _space_service: SpaceService
    _document_service: DocumentService
    _dry_run: bool
    _log_error: Callable[[str], None] | None

    def __init__(
        self,
        space_service: SpaceService | None = None,
        dry_run: bool = True,
        log_error: Callable[[str], None] | None = None,
    ):
        self._space_service = (
            space_service if space_service is not None else SpaceService("gws-project")
        )
        self._document_service = DocumentService()
        self._dry_run = dry_run
        self._log_error = log_error

    def migrate_all_projects(
        self, on_project_start: Callable[[int, int, Project], None] | None = None
    ) -> dict:
        """Migrate every project that has a Space folder and return the report.

        :param on_project_start: Optional callback (index, total, project) for progress
        :type on_project_start: Optional[Callable[[int, int, Project], None]]
        :return: The migration report
        :rtype: dict
        """
        projects: list[Project] = list(
            Project.select().where(Project.space_folder_id.is_null(False))
        )

        report: dict = {"dry_run": self._dry_run, "projects": []}

        for index, project in enumerate(projects):
            if on_project_start:
                on_project_start(index, len(projects), project)
            report["projects"].append(self.migrate_project(project))

        report["totals"] = self._compute_totals(report["projects"])
        return report

    def migrate_project(self, project: Project) -> dict:
        """Migrate every Space folder of a project (root tasks first, then the
        project folder) and return the per-project report entry.

        :param project: The project to migrate
        :type project: Project
        :return: The report entry of the project
        :rtype: dict
        """
        entry: dict = {
            "project_id": project.id,
            "project_title": project.title,
            "space_folder_id": project.space_folder_id,
            "migrated_files": [],
            "migrated_notes": [],
            "already_migrated": 0,
            "orphans": [],
            "skipped": [],
            "errors": [],
            "total_bytes": 0,
        }

        # 1. Task documents: each root task with a Space folder holds the
        # documents of its whole subtree, tagged with the exact task id.
        root_tasks = [
            task
            for task in Task.get_root_tasks_of_project(project.id)
            if task.space_folder_id
        ]
        for root_task in root_tasks:
            subtree = [root_task] + root_task.get_all_descendants()
            handled_ids: set[str] = set()

            for task in subtree:
                objects = self._list_folder_objects(
                    root_task.space_folder_id, tag=Tag(key=SPACE_TASK_TAG_KEY, value=task.id)
                )
                for space_object in objects:
                    self._migrate_object(project, task, space_object, entry)
                    handled_ids.add(space_object.id)

            # 2. Orphans: documents of the task folder whose tag matched no
            # existing task (deleted task, manual upload via the Space UI, ...)
            # are attached to the root task.
            for space_object in self._list_folder_objects(root_task.space_folder_id):
                if space_object.id in handled_ids:
                    continue
                if space_object.objectType in (
                    FILE_OBJECT_TYPE,
                    NOTE_OBJECT_TYPE,
                ) and not ProjectDocument.space_document_already_migrated(space_object.id):
                    entry["orphans"].append({"id": space_object.id, "name": space_object.name})
                self._migrate_object(project, root_task, space_object, entry)

        # 3. Project documents: direct non-folder children of the project
        # folder (task folders are separate folder ids, their content is not
        # returned here).
        for space_object in self._list_folder_objects(project.space_folder_id):
            self._migrate_object(project, None, space_object, entry)

        return entry

    def _migrate_object(
        self,
        project: Project,
        task: Task | None,
        space_object: SpaceHierarchyObjectDTO,
        entry: dict,
    ) -> None:
        """Migrate one Space object (idempotent, error-resilient).

        :param project: The project the object belongs to
        :type project: Project
        :param task: The task the object belongs to (None for project-level)
        :type task: Optional[Task]
        :param space_object: The Space object to migrate
        :type space_object: SpaceHierarchyObjectDTO
        :param entry: The report entry of the project (mutated in place)
        :type entry: dict
        """
        try:
            if space_object.objectType not in (FILE_OBJECT_TYPE, NOTE_OBJECT_TYPE):
                entry["skipped"].append(
                    {
                        "id": space_object.id,
                        "name": space_object.name,
                        "type": space_object.objectType,
                    }
                )
                return

            if ProjectDocument.space_document_already_migrated(space_object.id):
                entry["already_migrated"] += 1
                return

            if space_object.objectType == FILE_OBJECT_TYPE:
                self._migrate_file(project, task, space_object)
                entry["migrated_files"].append(space_object.name)
                entry["total_bytes"] += space_object.documentSize or 0
            else:
                self._migrate_note(project, task, space_object)
                entry["migrated_notes"].append(space_object.name)
        except Exception as err:
            if self._log_error:
                self._log_error(
                    f"Error migrating '{space_object.name}' ({space_object.id}): {err}"
                )
            entry["errors"].append(
                {"id": space_object.id, "name": space_object.name, "error": str(err)}
            )

    def _migrate_file(
        self, project: Project, task: Task | None, space_object: SpaceHierarchyObjectDTO
    ) -> None:
        """Download a Space document and store it as a local FILE document.

        :param project: The project the file belongs to
        :type project: Project
        :param task: The task the file belongs to (None for project-level)
        :type task: Optional[Task]
        :param space_object: The Space document
        :type space_object: SpaceHierarchyObjectDTO
        """
        if self._dry_run:
            return

        file_bytes = self._space_service.download_document_bytes(
            document_id=space_object.id, filename=space_object.name
        )

        temp_dir = Settings.make_temp_dir()
        temp_path = os.path.join(temp_dir, space_object.name)
        with open(temp_path, "wb") as file_handle:
            file_handle.write(file_bytes)

        self._document_service.create_migrated_file_document(
            project=project,
            task=task,
            file_path=temp_path,
            name=space_object.name,
            space_document_id=space_object.id,
        )

    def _migrate_note(
        self, project: Project, task: Task | None, space_object: SpaceHierarchyObjectDTO
    ) -> None:
        """Fetch a Space Constellab document content and store it as a local NOTE.

        :param project: The project the note belongs to
        :type project: Project
        :param task: The task the note belongs to (None for project-level)
        :type task: Optional[Task]
        :param space_object: The Space Constellab document
        :type space_object: SpaceHierarchyObjectDTO
        """
        if self._dry_run:
            return

        content = self._space_service.get_constellab_document_content(space_object.id)

        self._document_service.create_migrated_note(
            project=project,
            task=task,
            name=space_object.name,
            content=content,
            space_document_id=space_object.id,
        )

    def _list_folder_objects(
        self, folder_id: str, tag: Tag | None = None
    ) -> list[SpaceHierarchyObjectDTO]:
        """List all non-folder objects of a Space folder (paged through fully).

        :param folder_id: The Space folder id
        :type folder_id: str
        :param tag: Optional tag filter
        :type tag: Optional[Tag]
        :return: All non-folder objects of the folder
        :rtype: List[SpaceHierarchyObjectDTO]
        """
        objects: list[SpaceHierarchyObjectDTO] = []
        page = 0
        while True:
            search_params = SpaceHierarchyObjectSearchParams()
            search_params.add_object_type_filter(SearchOperator.NEQ, "FOLDER")
            if tag is not None:
                search_params.add_tag_filter(SearchOperator.EQ, tag)

            page_dto = self._space_service.search_project_children_objects_paginated(
                folder_id=folder_id,
                search_params=search_params,
                page=page,
                size=_PAGE_SIZE,
            )
            objects.extend(page_dto.objects)

            if len(page_dto.objects) < _PAGE_SIZE:
                return objects
            page += 1

    def _compute_totals(self, project_entries: list[dict]) -> dict:
        """Aggregate the per-project entries into global totals.

        :param project_entries: The per-project report entries
        :type project_entries: List[dict]
        :return: The totals of the report
        :rtype: dict
        """
        return {
            "projects": len(project_entries),
            "migrated_files": sum(len(entry["migrated_files"]) for entry in project_entries),
            "migrated_notes": sum(len(entry["migrated_notes"]) for entry in project_entries),
            "already_migrated": sum(entry["already_migrated"] for entry in project_entries),
            "orphans": sum(len(entry["orphans"]) for entry in project_entries),
            "skipped": sum(len(entry["skipped"]) for entry in project_entries),
            "errors": sum(len(entry["errors"]) for entry in project_entries),
            "total_bytes": sum(entry["total_bytes"] for entry in project_entries),
        }
