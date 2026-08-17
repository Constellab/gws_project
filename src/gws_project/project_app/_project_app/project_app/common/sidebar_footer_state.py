import reflex as rx
from gws_core import UserDTO
from gws_project.user.app_role_service import AppRoleService
from gws_reflex_main import ReflexMainState


class SidebarFooterState(rx.State):
    """Lightweight state exposing the current user for the sidebar footer.

    Standalone state (not inherited), fetched via get_state, following the
    same pattern as BreadcrumbState: computed @rx.var properties that reach
    ReflexMainState via get_state, so it works reactively on every page
    without needing an on_load anywhere.
    """

    @rx.var
    async def current_user_dto(self) -> UserDTO | None:
        main_state = await self.get_state(ReflexMainState)
        user = await main_state.get_current_user()
        return user.to_dto() if user else None

    @rx.var
    async def current_user_role_label_key(self) -> str:
        """Translation key for the current user's role label (see translate())."""
        main_state = await self.get_state(ReflexMainState)
        user = await main_state.get_current_user()
        if user is None:
            return ""
        return "sidebar.role_admin" if AppRoleService.is_admin(user.id) else "sidebar.role_member"
