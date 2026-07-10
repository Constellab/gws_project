from gws_core import (
    BoolParam,
    ConfigParams,
    ConfigSpecs,
    InputSpecs,
    JSONDict,
    OutputSpec,
    OutputSpecs,
    Task,
    TaskInputs,
    TaskOutputs,
    TypingIconColor,
    TypingStyle,
    task_decorator,
)

from gws_project.document.space_migration_service import SpaceMigrationService
from gws_project.project.project import Project


@task_decorator(
    "MigrateProjectDataFromSpace",
    human_name="Migrate gws_project data from Space",
    short_description="One-off migration: copy project/task documents from Space to local storage",
    style=TypingStyle.material_icon(
        "cloud_download", background_color="#22c55e", icon_color=TypingIconColor.BLACK
    ),
)
class MigrateProjectDataFromSpace(Task):
    """One-off, idempotent migration of gws_project data out of Space.

    For each project that still has a ``space_folder_id``, this task copies the
    content of its Space folders into local storage:

    - Space ``DOCUMENT`` objects are downloaded and stored as FILE documents in
      the brick's dedicated file store.
    - Space ``CONSTELLAB_DOCUMENT`` objects are converted to local rich-text
      NOTE documents (content fetched via the Space API).
    - Task documents (identified by the Space tag ``task:<task_id>`` in the
      root task's folder) are attached to the exact task; documents in a task
      folder whose tag matches no existing task are attached to the root task
      and flagged as orphans in the report.
    - Other object types (lab notes, scenarios, resources, ...) are skipped and
      listed in the report: they are lab objects synced to Space and stay
      accessible; only the app's aggregated view of them disappears.

    The task is **idempotent**: every migrated document records its Space id
    (``space_document_id``), and already-migrated ids are skipped on re-run. It
    **never writes to Space** — the Space folders are left untouched as an
    archive. Per-document errors are reported and never abort the run.

    Config:
    - ``dry_run`` (default True): only report what would be migrated, without
      downloading or writing anything. Run once with ``dry_run=True``, review
      the report (including the total byte size against the lab's disk space),
      then re-run with ``dry_run=False``.

    Output: a JSON report with per-project counts and details (migrated files
    and notes, already-migrated, orphans, skipped objects, errors, byte size).
    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({"report": OutputSpec(JSONDict, human_name="Migration report")})

    config_specs = ConfigSpecs(
        {
            "dry_run": BoolParam(
                default_value=True,
                human_name="Dry run",
                short_description="Only report what would be migrated, without writing anything",
            ),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """Run the migration"""
        dry_run: bool = params["dry_run"]

        migration_service = SpaceMigrationService(
            dry_run=dry_run, log_error=self.log_error_message
        )

        def on_project_start(index: int, total: int, project: Project) -> None:
            self.update_progress_value(
                (index / total) * 100 if total else 100,
                f"Migrating project '{project.title}'",
            )

        report = migration_service.migrate_all_projects(on_project_start=on_project_start)

        totals = report["totals"]
        self.log_info_message(
            f"Migration {'simulated' if dry_run else 'done'}: "
            f"{totals['migrated_files']} file(s), "
            f"{totals['migrated_notes']} note(s), "
            f"{totals['already_migrated']} already migrated, "
            f"{totals['skipped']} skipped, "
            f"{totals['errors']} error(s), "
            f"{totals['total_bytes']} byte(s)."
        )

        json_report = JSONDict(report)
        json_report.name = "gws_project Space migration report"
        return {"report": json_report}
