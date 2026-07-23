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

from gws_project.document.note_image_migration_service import NoteImageMigrationService


@task_decorator(
    "MigrateNoteImagesFromSpace",
    human_name="Repair images of Space-migrated project notes",
    short_description="One-off fix: download the embedded images of notes migrated from Space",
    style=TypingStyle.material_icon(
        "image", background_color="#22c55e", icon_color=TypingIconColor.BLACK
    ),
)
class MigrateNoteImagesFromSpace(Task):
    """One-off, idempotent repair of the images embedded in notes migrated out
    of Space.

    The main Space removal migration (``MigrateProjectDataFromSpace``) was run
    before project notes supported images. It converted each Space Constellab
    document into a local rich-text NOTE, copying the content verbatim — so the
    figure references (their filenames) were kept, but the image **bytes** were
    never downloaded into the note's local directory. As a result the images of
    those migrated notes are broken.

    For every NOTE that was migrated from Space (i.e. has a
    ``space_document_id``), this task:

    - reads the note's rich-text content and finds its ``FIGURE`` blocks,
    - for each figure whose image file is missing on disk, downloads the bytes
      from Space and writes them under the note's dedicated directory,
      **keeping the same filename** so the content is left untouched.

    The task is **idempotent**: a figure whose file already exists locally is
    skipped, so re-running only fetches what is still missing (and a note whose
    images are all present is a no-op). It **never writes to Space** and
    **never mutates the note content**. Per-figure and per-note errors are
    reported and never abort the run.

    Config:
    - ``dry_run`` (default True): only report which figures would be
      downloaded, without fetching or writing anything. Run once with
      ``dry_run=True``, review the report, then re-run with ``dry_run=False``.

    Output: a JSON report with per-note counts and details (figures repaired,
    already present, errors, failed notes).
    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({"report": OutputSpec(JSONDict, human_name="Repair report")})

    config_specs = ConfigSpecs(
        {
            "dry_run": BoolParam(
                default_value=True,
                human_name="Dry run",
                short_description="Only report what would be repaired, without writing anything",
            ),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """Run the note image repair migration"""
        dry_run: bool = params["dry_run"]

        migration_service = NoteImageMigrationService(
            dry_run=dry_run, message_dispatcher=self.get_message_dispatcher()
        )

        report = migration_service.migrate_all_notes()

        totals = report["totals"]
        self.log_info_message(
            f"Note image repair {'simulated' if dry_run else 'done'}: "
            f"{totals['notes']} note(s), "
            f"{totals['figures_repaired']} figure(s) "
            f"{'to repair' if dry_run else 'repaired'}, "
            f"{totals['figures_already_present']} already present, "
            f"{totals['errors']} error(s), "
            f"{totals['failed_notes']} failed note(s)."
        )

        json_report = JSONDict(report)
        json_report.name = "gws_project migrated-note image repair report"
        return {"report": json_report}
