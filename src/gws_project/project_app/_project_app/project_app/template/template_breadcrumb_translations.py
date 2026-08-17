"""Translations for the template breadcrumb root label. Registered once at import time.

See gws_reflex_main's I18nState/translate/register_translations for the
underlying (session-local) i18n mechanism.
"""

from gws_reflex_main import register_translations

register_translations(
    {
        "en": {
            "template_breadcrumb.templates": "Templates",
        },
        "fr": {
            "template_breadcrumb.templates": "Modèles",
        },
    }
)
