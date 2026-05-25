from gws_core import (
    AuthenticateUser,
    Event,
    EventListener,
    Logger,
    ResourceSearchBuilder,
    ScenarioCreationType,
    ScenarioProxy,
    Tag,
    event_listener,
)

from .project_app.generate_project_app import GenerateProjectApp
from .project_app.project_app_constants import (
    PROJECT_APP_TAG_KEY,
    PROJECT_APP_TAG_VALUE,
)


@event_listener
class GwsProjectListener(EventListener):
    """Listener that creates the Constellab Project app on lab startup.

    If no project app exists yet (no resource carrying the project tag), a
    scenario running :class:`GenerateProjectApp` is queued to generate one.
    """

    def handle(self, event: Event) -> None:
        if event.type == "system" and event.action == "started":
            self._create_project_app_if_none_exists()

    def _create_project_app_if_none_exists(self) -> None:
        """Generate the project app scenario if no project app exists yet."""
        try:
            if self._project_app_exists():
                return

            with AuthenticateUser.system_user():
                # build a scenario running GenerateProjectApp
                scenario = ScenarioProxy(
                    title="Generate Constellab Project app",
                    creation_type=ScenarioCreationType.AUTO,
                )
                protocol = scenario.get_protocol()
                generate_task = protocol.add_task(GenerateProjectApp)
                protocol.add_output(
                    "reflex_app_output", generate_task >> "reflex_app"
                )

                scenario.add_to_queue()
        except Exception as err:
            Logger.error(
                f"Error while creating the Constellab Project app. Error: {err}"
            )

    def _project_app_exists(self) -> bool:
        """Return True if a project app resource already exists in the lab."""
        search_builder = ResourceSearchBuilder()
        search_builder.add_tag_filter(
            Tag(PROJECT_APP_TAG_KEY, PROJECT_APP_TAG_VALUE)
        )
        return search_builder.search_first() is not None
