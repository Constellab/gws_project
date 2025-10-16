# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. All path are relative to location of this file.

## Project Overview

GWS Project is a Constellab brick (library) developed by Gencovery that provides AI-driven tools for data analysis and visualization in the life sciences. It depends on the `gws_core` brick (version 0.17.0) and includes a reflex application and database models to manage projects in Constellab.

## Architecture

### Directory Structure
- `src/gws_project/` - Source code of the brick
  - `user/` - User management module
    - `user.py` - User database model
    - `user_service.py` - User business logic and operations
  - `project/` - Project management module
    - `project.py` - Project database model
    - `project_dto.py` - Project data transfer objects
    - `project_user.py` - Project-user relationship model
    - `project_service.py` - Project business logic and operations
    - `project_security_service.py` - Project security and permissions
  - `task/` - Task management module
    - `task.py` - Task database model
    - `task_dto.py` - Task data transfer objects
    - `task_service.py` - Task business logic and operations
    - `task_search_builder.py` - Task search functionality
  - `project_app/` - Reflex web application to manage projects
    - `generate_project_app.py` - Script to generate/configure the Reflex app
    - `_project_app/` - Reflex application root directory
      - `dev_config.json` - Development configuration file (use to run the app in dev mode)
      - `rxconfig.py` - Reflex configuration
      - `project_app/` - Main application package
        - `project_app.py` - Main app entry point with rx.App() definition
      - `assets/` - Static assets (CSS, favicon, etc.)
  - `core/` - Core utilities and helpers
    - `model_with_user.py` - Base model with user tracking
    - `project_db_manager.py` - Database manager for project models
    - `gws_core_event_listener.py` - Event listeners for gws_core events
- `tests/test_gws_project/` - Test files


### Dependencies
- `gws_core` (v0.17.0) - Core Constellab functionality including BaseModelDTO, credentials, external API services
- `reflex` (v0.8.14.post1) - Web framework for the RAG application

## Development best Practices
- Follow the existing code style and conventions used in the project.
- Import from `gws_core` must use the main module imports (e.g., `from gws_core import BaseModelDTO`) rather than sub-imports (avoid `from gws_core.model.base import BaseModelDTO`)

## Development Commands

### Server Management
- Start server: `gws server run`
- Start server with debug logging: `gws server run --log-level=DEBUG`

### Testing
- Run all tests: `gws server test all`
- Run specific test: `gws server test [TEST_FILE_NAME]` (without `.py` extension, to run from the project directory)
- Tests are located in `tests/test_gws_core/` directory

### Development Apps
- Run Streamlit app in dev mode: `gws streamlit run [CONFIG_FILE_PATH]`
- Run Reflex app in dev mode: `gws reflex run [CONFIG_FILE_PATH]`