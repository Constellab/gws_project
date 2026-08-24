# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application overview

A Reflex web application for project, task and planning management, part of the GWS Project
brick. It is bilingual (English/French) and every screen is bounded to the projects the
signed-in user is a member of.

## Running the application

From the brick root directory:
```bash
gws reflex run src/gws_project/project_app/_project_app/dev_config.json
```

The app requires the `GWS_REFLEX_API_URL` environment variable (set automatically by
`gws_reflex_base.ReflexInit`, see `rxconfig.py`).

## Architecture

### Pages

Routes are declared in `project_app/project_app.py`. Each page's `on_load` starts with
`_LANGUAGE_FIRST` (`LanguageInitState.ensure_default_language`) so the first server-side render
already uses the app's language:

| Route | Module | Screen |
| --- | --- | --- |
| `/` | `home/` | Home: the ways into the app, then the team's recent activity |
| `/projects` | `project_list/` | The user's projects, with filters and stat cards |
| `/project/[project_id_param]` | `project_detail/` | One project: tasks, documents, members |
| `/project/task/[task_id_param]` | `task_detail/` | One task: subtasks, description, documents, activity |
| `/project/note/[note_id_param]` | `note_detail/` | One note in a full-page rich-text editor |
| `/kanban` | `kanban/` | Task board across projects |
| `/planning` | `planning/` | Person x day weekly scheduling grid |
| `/gantt` | `gantt/` | Portfolio timeline |
| `/my-work` | `my_work/` | The signed-in user's day and remaining tasks |
| `/companies`, `/company/[company_id_param]` | `company/` | Companies and their projects |
| `/templates`, `/template/project/[...]`, `/template/task/[...]` | `template/` | Project and task templates |
| `/admin` | `admin/` | Language, app roles, and (admin-only) working hours |

Each module holds `[name]_component.py` (UI), `[name]_state.py` (state and event handlers) and
`[name]_translations.py` (its texts).

### States

Every state is a plain `rx.State`; none of them inherits `ReflexMainState`. They *compose* the
shared states instead:

```python
main_state = await self.get_state(ReflexMainState)   # authentication
i18n = await self.get_state(I18nState)               # active language
```

`ReflexMainState` provides `check_authentication()`, `get_and_check_current_user()` and the
`authenticate_user()` context manager. Every service call goes inside that context:

```python
with await main_state.authenticate_user():
    tasks = TaskService().search_current_user_tasks(project_id=self.selected_project_id or None)
```

Shared states:
- `ProjectPageState` (`common/projects/`) - loads and caches the Project/Task of the current
  URL. It also owns `access_error` (a `ProjectAccessError` value): a project id in the URL is
  user input, so a deleted project or one the user is not a member of is a normal state, and
  the detail pages render `project_access_error_component()` instead of their content.
- `CompanyPageState`, `TemplatePageState` - the same caching for companies and templates.
- `ViewModeState`, `BreadcrumbState`, `LanguageInitState`, `DocumentsListState` - cross-page
  concerns.

### Services and authorization

The app never queries the database and never builds a `*SearchBuilder`: authorization lives in
the brick's services, so a filter value coming from the frontend must go through them.

- Listing projects: `ProjectService.search_current_user_projects(...)`
- Listing tasks across projects: `TaskService.search_current_user_tasks(...)`
- Everything else: the matching `*Service` method, which checks the role itself.

### Internationalisation

`gws_reflex_base`'s lightweight i18n (see its `i18n` component package). Two access paths:

```python
# in a component: reactive, re-renders on language change
rx.text(translate("project_list.title"))

# in an event handler: a plain string, in the session's language
i18n = await self.get_state(I18nState)
confirm_dialog_state.open_dialog(title=i18n.tr("task_actions.delete.title"), ...)

# a translated toast, the shortcut for the case above
yield await toast_tr.success(self, "task_form.toast.task_created")
yield await toast_tr.error(self, "documents_list.toast.rename_failed", {"error": str(err)})
```

Rules:
- No user-visible string literal in a state or a component: register it in the module's
  `[name]_translations.py`, in **both** `en` and `fr`.
- Texts shared by several screens go in a common translations module (see
  `common/tasks/task_actions_translations.py`).
- The component module imports its translations for the side effect:
  `from . import x_translations  # noqa: F401  (side effect: registers translations)`.
- `{{placeholder}}` markers are filled from the `data` dict.
- The language toggle lives on the Admin page (`language_toggle_component`).

### Dates

`common/date_format.py` is the only place that turns a date into text a user reads: it renders
day, month and weekday names in the active language (the tables cover `en`/`fr`).

```python
lang = (await self.get_state(I18nState)).lang
self.tasks = [localize_task_dto(task.to_dto(), lang) for task in tasks]  # *_text fields
format_date(value, lang)          # "Aug 21, 2026" / "21 août 2026"
format_datetime(value, lang)      # + " 14:32"  (also format_timestamp)
format_weekday_date(day, lang)    # "Thursday 21 August" / "jeudi 21 août"
```

History lines follow the same principle one step further: the backend hands over
`event_type` plus language-neutral values, and `common/tasks/task_history_message.py`
builds the sentence (`HistorySubject.TIMELINE` on a task's Activity tab,
`HistorySubject.FEED` on Home, which names the task on its own line).

A model's `to_dto()` fills `*_text` with an ISO fallback because it knows nothing about the
session: every state that sends a Project/Task/ProjectTemplate DTO to the frontend passes it
through the matching `localize_*_dto`. Never call `strftime` with an English format for
display; `"%Y-%m-%d"` for an `<input type="date">` value is fine.

Formatting happens server-side and reaches the frontend as a plain string (client-side parsing
of the serialized datetimes proved unreliable). A state therefore formats with the language of
the session at load time, which is enough: the language toggle lives on the Admin page, so any
other page is reloaded after a change.

### Components

- Layouts: `page_layout(content, ...)` (left sidebar + optional right sidebar),
  `detail_page_layout(main_content, header_content)`.
- Reusable: `common/tasks/` (status and priority chips, card, actions menu),
  `common/projects/`, `common/kanban/`, `common/gantt/`, `common/planning_grid/`,
  `common/documents_list/`, `progress_ring`, `updatable_chip`. From `gws_reflex_main`:
  `user_inline_component`, `user_profile_picture`, `user_select`, `group_select`.
- Navigation URLs come from `ProjectAppRouter` / `CompanyAppRouter`, never a literal path.
- Dialogs: a state inheriting `FormDialogState` with `open_create_dialog()`/
  `open_update_dialog()` and `_create()`/`_update()`; the component exposes
  `[name]_dialog()`. `submit_form` runs as a background event, and its validation helpers are
  `async` so they can resolve their error messages through `I18nState`.
- Confirmations use `ConfirmDialogState.open_dialog(title=..., content=..., action=...)` with
  translated strings.

## Conventions

- State classes `[Module]State`, components `[name]_component()`, dialogs `[name]_dialog()`,
  page entry points `[name]_page()`, internal helpers prefixed with `_`.
- Imports: `from gws_reflex_main import ...`, `from gws_core import ...` (main module only),
  relative imports inside the app.
- Components are pure functions returning `rx.Component`; use `rx.cond` / `rx.foreach` for
  conditionals and lists.
- Prefer `@rx.var async def` for anything derived from another state (it stays reactive).
- Run `ruff check --fix` on the files you modified.

## Adding a page

1. Create `project_app/[page_name]/` with `[page_name]_state.py`, `[page_name]_component.py`
   and `[page_name]_translations.py`.
2. Register the route in `project_app.py` with `on_load=[_LANGUAGE_FIRST, State.on_load]`.
3. Add its URL to `ProjectAppRouter` and, if it belongs in the navigation, to
   `common/page_layout.py`.

## Configuration files

- `rxconfig.py` - Reflex configuration (app name, API URL, theme, frontend packages)
- `dev_config.json` - Development configuration (app directory, dev user email, access mode)
