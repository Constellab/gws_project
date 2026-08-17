import reflex as rx
from gws_reflex_main import I18nState


class LanguageInitState(rx.State):
    """Sets the app's default language to English once per session.

    The shared I18nState defaults to French (gws_reflex_base's DEFAULT_LANG).
    This app wants English by default instead, without changing the shared
    default for every other app. Guarded by `initialized` so a later manual
    language switch by the user is never overridden on subsequent page loads.
    """

    initialized: bool = False

    @rx.event
    async def ensure_default_language(self):
        if self.initialized:
            return
        self.initialized = True
        i18n = await self.get_state(I18nState)
        i18n.lang = "en"
