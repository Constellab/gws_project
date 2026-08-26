"""Regression tests for the form dialogs' use of state inside background events.

`FormDialogState.submit_form` (gws_core) is an `@rx.event(background=True)` handler, so
inside it -- and inside every `_create` / `_update` it drives -- `self` is a Reflex
`StateProxy`. That proxy refuses to reach sibling state unless the state lock is held::

    Background task StateProxy is immutable outside of a context manager.
    Use `async with self` to modify state.

The app used hardcoded English strings and plain `rx.toast` until the translations
commit, which replaced them with `i18n.tr(...)` (needs `get_state(I18nState)`) and
`toast_tr` (which reaches `I18nState` the same way). That dropped `get_state` calls onto
background paths that had never made one, and every form dialog started raising on
submit.

Two complementary tests:

- :class:`TestFormDialogValidatorsUnderStateProxy` drives the real validators through a
  real `StateProxy` outside a lock -- the exact failing call, executed for real.
- :class:`TestNoUnlockedStateAccessInFormDialogs` parses the dialog states and asserts no
  unlocked `get_state` / `toast_tr` is left. It covers the toast sites the runtime test
  cannot reach (they need a DB and an authenticated user) and guards against the pattern
  being reintroduced.
"""

import ast
import asyncio
import inspect
import shutil
import sys
import unittest
from pathlib import Path

from gws_core import ReflexProcess

BRICK_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = BRICK_ROOT / "src" / "gws_project" / "project_app" / "_project_app"
DIALOGS_ROOT = APP_ROOT / "project_app"

# `gws_reflex_main` and the app's own `project_app` package both live outside the normal
# import path: the gws_reflex modules are injected into PYTHONPATH by `ReflexProcess`, and
# the app folder is prefixed with `_` so it is not executed on lab startup. Both paths must
# be registered before the app states below can be imported.
REFLEX_MODULES_ROOT = (
    Path(inspect.getfile(ReflexProcess)).parent / ReflexProcess.REFLEX_MODULES_PATH
)
for _path in (REFLEX_MODULES_ROOT, APP_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

# Importing the app states runs Reflex's `rx.asset(...)` registrations, which copy
# gws_reflex_base's theme into an `assets/` folder next to the current working directory.
# Remember whether the brick already had one, so `tearDownModule` can clean up a folder
# this module created without ever touching a real one.
ASSETS_DIR = BRICK_ROOT / "assets"
_ASSETS_EXISTED_BEFORE_IMPORT = ASSETS_DIR.exists()

from project_app.company.company_form_dialog_state import (  # noqa: E402
    CompanyFormDialogState,
)
from project_app.project_detail.project_user_form_dialog_state import (  # noqa: E402
    ProjectUserFormDialogState,
)
from project_app.project_form_dialog.project_form_dialog_state import (  # noqa: E402
    ProjectFormDialogState,
)
from project_app.task_form.task_form_dialog_state import (  # noqa: E402
    TaskFormDialogState,
)
from project_app.template.project_template_form_dialog.project_template_form_dialog_state import (  # noqa: E402, E501
    ProjectTemplateFormDialogState,
)
from project_app.template.task_template_form_dialog.task_template_form_dialog_state import (  # noqa: E402, E501
    TaskTemplateFormDialogState,
)
from reflex.istate.manager.memory import StateManagerMemory  # noqa: E402
from reflex.istate.manager.token import BaseStateToken  # noqa: E402
from reflex.istate.proxy import StateProxy  # noqa: E402
from reflex.utils.exceptions import ImmutableStateError  # noqa: E402
from reflex_base.event.context import EventContext  # noqa: E402

# Functions reached from the background `submit_form`, so every state access inside them
# must hold the lock.
BACKGROUND_FUNCTIONS = {
    "_create",
    "_update",
    "_create_from_template",
    "_validate_form_data",
    "_validate_and_parse_form_data",
    "_validate_and_extract_common_fields",
    "_validate_and_parse_create_task_form_data",
    "_validate_and_parse_update_task_form_data",
    "_validate_and_parse_create_task_template_form_data",
    "_validate_and_parse_update_task_template_form_data",
}


class TestFormDialogValidatorsUnderStateProxy(unittest.TestCase):
    """Run the real validators through a real StateProxy, outside the lock.

    This is the reported failure reproduced end to end: before the fix these calls raised
    ImmutableStateError, which `submit_form` turned into an error toast instead of saving.
    """

    def _run_under_state_proxy(self, state_cls, coro_name: str, *args):
        """Call `state_cls.<coro_name>(*args)` on a StateProxy held outside any lock.

        :param state_cls: The Reflex state class owning the method
        :type state_cls: type
        :param coro_name: Name of the async method to call
        :type coro_name: str
        :param args: Arguments forwarded to the method
        :return: Whatever the method returned, or the exception it raised
        """

        async def run():
            # Memory, never StateManager.create(): that one honours the Reflex config
            # and picks the on-disk manager, which pickles the state tree into a
            # .states/ folder in the brick root.
            state_manager = StateManagerMemory()
            token = f"test-token-{state_cls.__name__}"
            event_context = EventContext(
                token=token,
                state_manager=state_manager,
                enqueue_impl=lambda *args, **kwargs: None,
            )
            with event_context:
                root_state = await state_manager.get_state(
                    BaseStateToken(ident=token, cls=state_cls)
                )
                instance = await root_state.get_state(state_cls)
                # No `async with proxy` here on purpose: this mirrors `submit_form`
                # calling into `_create` / `_update` with the lock released.
                proxy = StateProxy(instance)
                try:
                    return await getattr(proxy, coro_name)(*args)
                except Exception as err:  # returned, then inspected by the caller
                    return err

        return asyncio.run(run())

    def _assert_not_immutable_state_error(self, result, label: str) -> None:
        """Fail if the call tripped Reflex's background-proxy immutability guard.

        Any other exception is fine here: the validators legitimately raise on invalid
        input, and that is not what this test is about.

        :param result: Return value or exception from the validator
        :param label: Human readable name of the call, for the failure message
        :type label: str
        """
        if isinstance(result, ImmutableStateError):
            self.fail(
                f"{label} reached sibling state without holding the lock: {result} "
                "Wrap the `get_state` call in `async with self:`."
            )
        # The proxy surfaces the same problem through other exception types when a
        # container is mutated, so guard on the message too.
        if isinstance(result, Exception) and "immutable outside of a context" in str(result):
            self.fail(f"{label} tripped the background StateProxy guard: {result}")

    def test_task_form_validator_reaches_i18n(self):
        """The reported failure: updating a task from the projects tab."""
        result = self._run_under_state_proxy(
            TaskFormDialogState,
            "_validate_and_extract_common_fields",
            {"title": "A task", "start_date": "", "due_date": "", "assign_to_id": ""},
        )
        self._assert_not_immutable_state_error(result, "TaskFormDialogState validator")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["title"], "A task")

    def test_task_form_validator_reaches_i18n_for_its_error_message(self):
        """The empty-title branch builds its message through i18n, so it needs the lock too."""
        result = self._run_under_state_proxy(
            TaskFormDialogState,
            "_validate_and_extract_common_fields",
            {"title": "", "start_date": "", "due_date": "", "assign_to_id": ""},
        )
        self._assert_not_immutable_state_error(
            result, "TaskFormDialogState validator (empty title)"
        )
        # It must still reject the empty title, with a resolved (non-empty) message.
        self.assertIsInstance(result, Exception)
        self.assertTrue(str(result))

    def test_every_form_dialog_validator_holds_the_lock(self):
        """Same check across all six dialogs the translations commit rewrote."""
        # Empty form data on purpose: it drives each validator down its i18n error
        # branch, which is the branch that needs the lock in every dialog.
        cases = [
            (TaskFormDialogState, "_validate_and_extract_common_fields"),
            (ProjectFormDialogState, "_validate_and_parse_form_data"),
            (CompanyFormDialogState, "_validate_and_parse_form_data"),
            (TaskTemplateFormDialogState, "_validate_and_extract_common_fields"),
            (ProjectTemplateFormDialogState, "_validate_and_parse_form_data"),
            (ProjectUserFormDialogState, "_validate_form_data"),
        ]

        for state_cls, method_name in cases:
            with self.subTest(state=state_cls.__name__):
                result = self._run_under_state_proxy(state_cls, method_name, {})
                self._assert_not_immutable_state_error(
                    result, f"{state_cls.__name__}.{method_name}"
                )


class TestNoUnlockedStateAccessInFormDialogs(unittest.TestCase):
    """Static guard over the dialog states.

    The runtime test above cannot reach the `toast_tr` calls (they sit after a DB write
    behind an authenticated user), so those are covered here instead, together with any
    future `get_state` added to a background path.
    """

    def _dialog_state_files(self) -> list[Path]:
        """Every `*_form_dialog_state.py` under the app.

        :return: The dialog state module paths
        :rtype: list[Path]
        """
        files = sorted(DIALOGS_ROOT.rglob("*_form_dialog_state.py"))
        self.assertTrue(files, f"no form dialog states found under {DIALOGS_ROOT}")
        return files

    def _unlocked_state_access(self, func: ast.AST) -> list[str]:
        """Collect state accesses in `func` that are not inside `async with self:`.

        :param func: The function node to inspect
        :type func: ast.AST
        :return: One description per offending call site
        :rtype: list[str]
        """
        offenders: list[str] = []

        def is_self_lock(node: ast.AST) -> bool:
            return isinstance(node, ast.AsyncWith) and any(
                isinstance(item.context_expr, ast.Name) and item.context_expr.id == "self"
                for item in node.items
            )

        def describe(call: ast.Call) -> str | None:
            target = call.func
            if not isinstance(target, ast.Attribute):
                return None
            # self.get_state(...)
            if (
                target.attr == "get_state"
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                return "self.get_state(...)"
            # toast_tr.success(self, ...) and friends
            if isinstance(target.value, ast.Name) and target.value.id == "toast_tr":
                return f"toast_tr.{target.attr}(self, ...)"
            return None

        def visit(node: ast.AST, locked: bool) -> None:
            for child in ast.iter_child_nodes(node):
                child_locked = locked or is_self_lock(child)
                if isinstance(child, ast.Call) and not locked:
                    label = describe(child)
                    if label:
                        offenders.append(f"line {child.lineno}: {label}")
                visit(child, child_locked)

        visit(func, locked=False)
        return offenders

    def test_background_paths_hold_the_lock(self):
        """No `get_state` / `toast_tr` outside `async with self:` on a background path."""
        problems: list[str] = []

        for path in self._dialog_state_files():
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if not isinstance(node, ast.AsyncFunctionDef):
                    continue
                if node.name not in BACKGROUND_FUNCTIONS:
                    continue
                for offender in self._unlocked_state_access(node):
                    problems.append(
                        f"{path.relative_to(BRICK_ROOT)}::{node.name} -> {offender}"
                    )

        self.assertEqual(
            problems,
            [],
            "These run inside the background `submit_form`, so they must be wrapped in "
            "`async with self:`:\n  " + "\n  ".join(problems),
        )

    def test_the_guard_actually_detects_the_old_pattern(self):
        """Guard the guard: the pre-fix code must be reported as a problem.

        Without this, a bug in the AST walk would make the test above pass silently.
        """
        old_code = (
            "class S:\n"
            "    async def _update(self, form_data):\n"
            "        i18n = await self.get_state(I18nState)\n"
            "        yield await toast_tr.success(self, 'k')\n"
        )
        func = self._first_async_function(old_code, "_update")
        offenders = self._unlocked_state_access(func)
        self.assertEqual(len(offenders), 2, f"expected both calls flagged, got {offenders}")

        fixed_code = (
            "class S:\n"
            "    async def _update(self, form_data):\n"
            "        async with self:\n"
            "            i18n = await self.get_state(I18nState)\n"
            "        async with self:\n"
            "            toast = await toast_tr.success(self, 'k')\n"
            "        yield toast\n"
        )
        func = self._first_async_function(fixed_code, "_update")
        self.assertEqual(self._unlocked_state_access(func), [])

    def _first_async_function(self, code: str, name: str) -> ast.AsyncFunctionDef:
        """Parse `code` and return the async function called `name`.

        :param code: The source to parse
        :type code: str
        :param name: The function name to find
        :type name: str
        :return: The matching function node
        :rtype: ast.AsyncFunctionDef
        """
        tree = ast.parse(code)
        return next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef) and node.name == name
        )


def tearDownModule():
    """Drop the `assets/` folder the app imports created, so a run leaves no stray files."""
    if not _ASSETS_EXISTED_BEFORE_IMPORT and ASSETS_DIR.exists():
        shutil.rmtree(ASSETS_DIR, ignore_errors=True)
