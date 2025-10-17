
from gws_core import Event, EventListener, event_listener
from gws_project.user.user_service import UserService


@event_listener
class GwsCoreDbListener(EventListener):
    """
    Listen to gws_core event to sync user database.

    Args:
        EventListener (_type_): _description_
    """

    def handle(self, event: Event) -> None:
        if event.type == 'system' and event.action == 'started':
            UserService.sync_gws_core_users()
        if event.type == 'user':
            print(f"User event received: {event.action} for user {event.data}")
            UserService.sync_gws_core_user(event.data)
