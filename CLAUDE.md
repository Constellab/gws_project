# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. All paths are relative to the location of this file.

## Project Overview

GWS Project is a Constellab brick (library) developed by Gencovery. It provides project, task
and planning management inside Constellab: the database models and services, plus a Reflex web
application to use them. It depends on the `gws_core` brick (see `settings.json` for the exact
version required).

Projects, tasks, documents and membership are stored **locally** (this brick's database +
a dedicated lab file store). Space is only used as the user/group directory (resolving a
group's users when adding it to a project).

## Architecture

### Directory structure
- `src/gws_project/` - Source code of the brick
  - `project/` - Projects: model, DTOs, membership (`project_user.py`), search builder,
    `project_security_service.py` (per-project authorization), `project_service.py`,
    `project_controller.py` (the brick's HTTP endpoints)
  - `task/` - Tasks: model, DTOs, search builder, service
  - `task_comment/` - Comments posted on a task
  - `task_history/` - The history events shown in a task's Activity tab
  - `template/` - Project and task templates
  - `company/` - Companies, the (optional) shared reference data a project can be linked to
  - `document/` - Files and notes attached to a project or task, plus the one-shot tasks that
    migrated them (and their images) out of Space
  - `planning/` - Planning slots: the person x day scheduling behind the Planning screen
  - `my_work/`, `home/` - Read-only, derived screens (one person's day, the team's activity)
  - `user/` - Users, their app-level role (`app_role_service.py`, ADMIN/MEMBER) and the
    Space -> lab user synchronisation
  - `core/` - Base model, database manager, brick migrations, API registry, working hours settings
  - `project_app/` - The Reflex web application (see its own `CLAUDE.md`)
- `tests/test_gws_project/` - Test files

### Authorization
Two independent role concepts, both enforced **in the services**, never in the app:
- `ProjectUserRole` (OWNER/USER) - membership of one project. Enforced through
  `ProjectSecurityService.get_and_check_role_for_project` / `..._for_task`, called by every
  service method that reads or writes a project's data.
- `AppRole` (ADMIN/MEMBER) - app-level role, independent from the above and from gws_core's
  `UserGroup`. Gates app-wide features: the working hours settings (admin only) and creating
  or modifying a company (`CompanyService.COMPANY_WRITE_ROLES`).

Rules that follow from this:
- A list/search method that is not restricted to a single, explicitly authorized project must
  be bounded to the current user's projects. Use `ProjectService.search_current_user_projects`
  and `TaskService.search_current_user_tasks` rather than building a search builder outside
  the services: they own that scoping, so a filter value coming from the frontend can never
  widen what is returned.
- Never call a `*SearchBuilder` from the Reflex app.

### Display text and language
The database and the DTOs stay language-neutral. Anything a user reads is resolved in the app
layer, in the language of the session:
- Labels and messages: the app's i18n (see the app's `CLAUDE.md`).
- Dates: the `*_text` fields of `ProjectDTO`/`TaskDTO`/`ProjectTemplateDTO` carry an ISO
  fallback; the app rewrites them through `common/date_format.py`. Do not add English
  `strftime` output to a DTO.
- The one exception is the task history: its stored `message`/`old_value`/`new_value` are
  written in English at the time of the event, on purpose, since they are persisted rows.

## Development best practices
- Follow the existing code style and conventions used in the project.
- Imports from `gws_core` must use the main module (e.g. `from gws_core import BaseModelDTO`),
  never a sub-module path.
- Write docstrings for classes and public methods, in the `:param:`/`:return:` style used
  throughout the brick.
- Run `ruff check --fix` on the files you modified.

## Development commands

### Server management
- Start server: `gws server run`
- Start server with debug logging: `gws server run --log-level=DEBUG`

### Testing
- Run all tests: `gws server test all` (add `--parallel` to spread them over workers)
- Run one test file: `gws server test [TEST_FILE_NAME]` (without `.py`), from the brick folder
- Tests live in `tests/test_gws_project/`

### Development apps
- Run the Reflex app in dev mode, from the brick root:
  `gws reflex run src/gws_project/project_app/_project_app/dev_config.json`

### Migrations
Every schema change ships with a `BrickMigration` in `core/migration_<n>.py`, declared with the
version that introduces it (see `settings.json`). Bump the brick version and add a migration in
the same change.
