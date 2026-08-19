import os

import reflex as rx


def _init_reflex(config: rx.Config) -> None:
    """Initialize Reflex environment after config is created to avoid circular imports."""
    # Import inside the function to avoid circular import
    from gws_reflex_base import ReflexInit, get_theme

    # Call init but ignore the return value since we already got api_url
    ReflexInit.init()

    # Configure the GWS theme via RadixThemesPlugin (replaces the deprecated
    # App(theme=...), removed in reflex 1.0). Done here because get_theme is only
    # importable once ReflexInit.init() has set up the gws_reflex_base path.
    config.plugins.append(
        rx.plugins.RadixThemesPlugin(theme=get_theme()),
    )


# Get api_url from environment variable first (before calling _init_reflex)
# This avoids circular imports since the config object needs to exist first
api_url = os.environ.get("GWS_REFLEX_API_URL")
if api_url is None:
    raise ValueError("GWS_REFLEX_API_URL environment variable is not set")
# [END_AUTO_CODE]

config = rx.Config(
    app_name="project_app",
    plugins=[rx.plugins.SitemapPlugin()],
    # [START_AUTO_CODE]
    api_url=api_url,
    # [END_AUTO_CODE]
    frontend_packages=[
        "@dnd-kit/core",
        "@dnd-kit/sortable",
        "@dnd-kit/utilities",
    ],
)

# Now that config exists, call initialization
# This must happen after config is defined to avoid circular imports
_init_reflex(config)
