# Portfolio Gantt

The `/gantt` page: every project the user can see, grouped by status on a shared timeline,
with its root tasks collapsible underneath. It answers three questions at a glance — what is
late, what falls due soon, and where each project stands (real progress vs elapsed time).

Implemented as a self-contained React component. It used to wrap `gantt-task-react`; that
library could not express the status grouping, the pixels-per-day axis or the frozen left
column, so it was dropped (and removed from `rxconfig.py`).

## Files

| File | Role |
|---|---|
| `gantt_chart.tsx` | The whole chart: axis, rows, bars, freezing, re-centring |
| `gantt_component.py` | The Reflex `GanttChart` wrapper + `gantt_component()` |
| `gantt_type.py` | `GanttTaskDTO` / `GanttProjectDTO` / `GanttDataDTO` / `GanttStatus` |
| `gantt_utils.py` | `build_gantt_data_from_projects()`, `resolve_status()`, `get_initials()` |
| `gantt_translations.py` | Chart labels + the locale tag |

## Usage

```python
gantt_component(
    data=GanttPageState.gantt_data,
    view_mode=GanttPageState.view_mode,          # 'Day' | 'Week' | 'Month' | 'Year'
    show_completed=GanttPageState.show_completed,
    recenter_token=GanttPageState.recenter_token,
    on_task_click=GanttPageState.handle_task_click,
)
```

`gantt_component()` fills the translated labels and the locale itself.

## Status model

Three statuses, and only three. They are **computed**, never stored — `resolve_status()` in
`gantt_utils.py`:

| Status | Condition |
|---|---|
| `termine` | `progress >= 100` |
| `retard` | `end < today` and not finished |
| `encours` | everything else, including projects that have not started |

Finished wins over late, so a project completed past its deadline reads as done. There is no
"to start" or "planned" state, and no milestones.

`GanttStatus` is deliberately *not* a mirror of `ProjectStatus` / `TaskStatus`: those record
what the user declared, this records where the item stands against today. `today` is resolved
server-side and shipped in the payload so the chart and the backend cannot disagree about it
across timezones.

## Layout

The chart is one native scroll container. The left column is `position: sticky; left: 0` and
the two-row axis is `position: sticky; top: 0`, so both freeze without any JS. The container
sets `overscroll-behavior: contain` so reaching the bottom does not hand the wheel to the page.

**The chart must be given a bounded height by its parent** — a flex child with `flex: 1` and
`min-height: 0`, as the page does. Left column is 356px; project rows are 46px, task rows 32px
(36 / 26 in compact mode).

## Time axis and zoom

The scale is `ppd` (pixels per day); origin and span come from the zoom level:

| Zoom | ppd | Origin | Span | Axis row 1 | Axis row 2 |
|---|---|---|---|---|---|
| Day | 24 | Monday of week −8 | 132 d | month + year | day number, weekends shaded |
| Week (default) | 12 | Monday of week −8 | 132 d | month + year | `S34`, current week highlighted |
| Month | 5.4 | Monday of week −8 | 132 d | month + year | week number |
| Year | 1.9 | first Monday **of January** | 372 d | year | short month, current month highlighted |

Bar geometry: `left = (start − origin in days) × ppd`, `width = max(6, (end − start + 1) × ppd)`
— both ends inclusive, 6px floor so a one-day bar stays visible when zoomed out.

The view re-centres on today at mount, on every zoom change, and whenever `recenter_token`
changes (the "Today" button bumps it): `scrollLeft = todayOffset − 0.42 × visibleWidth`.

Watch the Year origin: it must be the first Monday *of January*, not the Monday of the week
containing Jan 4th — the latter falls back into December and draws a stray sliver of the
previous year on the axis.

## Bars and colour

One meaning-carrying colour per bar (the status); the fill carries progress.

| Status | Track (remaining) | Fill (done) |
|---|---|---|
| En cours | `--accent-3` | `--accent-9` |
| En retard | `--tertiary-3` | `--tertiary-8` |
| Terminé | `--accent-9` (full, no remainder) | `--accent-9` |

These are the design tokens, not lookalikes: `--accent-9` is `#1d907d` (the brand primary the
spec names `--primary-color`) and `--tertiary-7` is `#e176b2` (its `--warn-color`). The
teal-tinted utility greys in `GREY` are literals because the sage `--gray-*` scale does not
match that tint; the spec allows them for grid and track backgrounds.

Labels never overlap a bar that is too short for them: `Nom · XX %` goes *inside* when
`width > chars × 6.4 + 26`, otherwise it is drawn to the right of the bar. Inside labels flip
to white past 55% progress. Every bar carries a native `title` tooltip.

## Grouping

Groups are ordered **En retard → En cours → Terminé**, and projects are sorted by due date
ascending inside each group — what falls due next is what needs attention. Empty groups are
not rendered, and `Terminé` disappears entirely when "show completed" is off.

Grouping and sorting are done in the chart, not the backend: they are presentation concerns
that must follow the "show completed" toggle without a round trip. The page's header counters
therefore re-derive the same rule in `GanttPageState.visible_projects` — match projects **by
id**, since projects missing a start or due date never reach the payload at all and the two
lists are not positionally aligned.

## Gotchas

- `data` arrives from Reflex as a **fresh object on every state delta**. Never clear the
  expanded set in an effect keyed on it, or the chart collapses behind the user on every
  unrelated update — only drop ids that no longer exist.
- Parse ISO dates with the local-day helper, not `new Date('2026-08-19')`: the latter parses as
  UTC midnight and shifts every bar one column west of Greenwich.
