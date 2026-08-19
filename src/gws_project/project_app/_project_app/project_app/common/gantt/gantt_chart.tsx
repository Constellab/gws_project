import React, { useState, useMemo, useRef, useEffect, useCallback } from 'react';

/* ------------------------------------------------------------------ types */

type Status = 'encours' | 'retard' | 'termine';
type Zoom = 'Day' | 'Week' | 'Month' | 'Year';

interface GanttTask {
  name: string;
  start: string;
  end: string;
  progress: number;
  status: Status;
}

interface GanttProject extends GanttTask {
  id: string;
  owner: string;
  owner_name: string;
  late_days: number;
  tasks: GanttTask[];
}

interface GanttData {
  projects: GanttProject[];
  today: string;
}

interface GanttChartProps {
  data: GanttData;
  viewMode?: Zoom;
  showCompleted?: boolean;
  compact?: boolean;
  /** Bumped by the "Today" button; any change re-centres the timeline. */
  recenterToken?: number;
  locale?: string;
  onTaskClick?: (projectId: string) => void;
  labels?: Record<string, string>;
}

/* -------------------------------------------------------------- constants */

const LEFT_WIDTH = 356;
const META_WIDTH = 92;
const HEADER_HEIGHT = 56;
const GROUP_HEIGHT = 30;

const ROW_HEIGHT = { project: 46, task: 32 };
const ROW_HEIGHT_COMPACT = { project: 36, task: 26 };

const BAR_HEIGHT = { project: 20, task: 12 };
const BAR_RADIUS = { project: 6, task: 4 };

/** Pixels per day, window origin and span for each zoom level. */
const ZOOM: Record<Zoom, { ppd: number; days: number; weeksBefore: number; fromJanuary: boolean }> = {
  Day: { ppd: 24, days: 132, weeksBefore: 8, fromJanuary: false },
  Week: { ppd: 12, days: 132, weeksBefore: 8, fromJanuary: false },
  Month: { ppd: 5.4, days: 132, weeksBefore: 8, fromJanuary: false },
  Year: { ppd: 1.9, days: 372, weeksBefore: 0, fromJanuary: true },
};

/** The spec's status palette, expressed against this app's Radix scales. --accent-9 is
 *  #1d907d (the brand primary the spec names) and --tertiary-7 is #e176b2 (its warn tone),
 *  so these are the real design tokens rather than lookalike hex values. */
const PALETTE: Record<Status, { track: string; fill: string; dot: string }> = {
  encours: { track: 'var(--accent-3)', fill: 'var(--accent-9)', dot: 'var(--accent-9)' },
  retard: { track: 'var(--tertiary-3)', fill: 'var(--tertiary-8)', dot: 'var(--tertiary-8)' },
  termine: { track: 'var(--accent-9)', fill: 'var(--accent-9)', dot: 'var(--accent-9)' },
};

/* Teal-tinted utility greys, explicitly allowed by the spec for grid and track backgrounds.
   They sit between --accent-1 (#f7fdfc) and the sage --gray-* scale, which is why they are
   literals rather than tokens. */
const GREY = {
  groupBg: '#fbfdfd',
  taskBg: '#fdfefe',
  rowHover: '#f6faf9',
  grid: '#eef3f2',
  border: '#e4ecea',
  borderStrong: '#dfe9e7',
  weekend: '#fafcfb',
  muted: '#b9c4c2',
  avatarBg: '#eef3f2',
};

const GROUP_ORDER: Status[] = ['retard', 'encours', 'termine'];
const DAY_MS = 86400000;
const LABEL_CHAR_PX = 6.4;
const LABEL_PADDING_PX = 26;
/** Progress past which an in-bar label is drawn white rather than dark. */
const LABEL_INVERT_AT = 55;
const RECENTRE_RATIO = 0.42;

const DEFAULT_LABELS: Record<string, string> = {
  columnProject: 'Projet / tâche',
  columnMeta: 'Période · avancement',
  groupLate: 'En retard',
  groupOngoing: 'En cours',
  groupDone: 'Terminé',
  projectOne: 'projet',
  projectMany: 'projets',
  taskOne: 'tâche',
  taskMany: 'tâches',
  lateBy: 'En retard de {n} j',
  done: 'réalisé',
  empty: 'Aucun projet ne correspond aux filtres.',
};

/* ---------------------------------------------------------------- helpers */

/** Parse an ISO `YYYY-MM-DD` as a local calendar day. `new Date('2026-08-19')` parses as UTC
 *  midnight and shifts a day west of Greenwich, which would move every bar by one column. */
function parseDay(iso: string): Date {
  const [y, m, d] = (iso || '').split('-').map(Number);
  return new Date(y || 1970, (m || 1) - 1, d || 1);
}

function dayIndex(day: Date, origin: Date): number {
  return Math.round((day.getTime() - origin.getTime()) / DAY_MS);
}

function addDays(day: Date, count: number): Date {
  const next = new Date(day);
  next.setDate(next.getDate() + count);
  return next;
}

/** Monday of the week containing `day`. */
function startOfWeek(day: Date): Date {
  const monday = new Date(day);
  const weekday = (monday.getDay() + 6) % 7;
  monday.setDate(monday.getDate() - weekday);
  monday.setHours(0, 0, 0, 0);
  return monday;
}

/** ISO week number, for the `S34` axis labels. */
function isoWeek(day: Date): number {
  const target = new Date(day.getFullYear(), day.getMonth(), day.getDate());
  target.setDate(target.getDate() + 3 - ((target.getDay() + 6) % 7));
  const firstThursday = new Date(target.getFullYear(), 0, 4);
  firstThursday.setDate(firstThursday.getDate() + 3 - ((firstThursday.getDay() + 6) % 7));
  return 1 + Math.round((target.getTime() - firstThursday.getTime()) / (7 * DAY_MS));
}

function formatDay(day: Date, locale: string): string {
  return day.toLocaleDateString(locale, { day: 'numeric', month: 'short' });
}

function plural(count: number, one: string, many: string): string {
  return count + ' ' + (count > 1 ? many : one);
}

/* ------------------------------------------------------------------ atoms */

function StatusDot({ status, size }: { status: Status; size: number }) {
  return (
    <span style={{
      width: size, height: size, borderRadius: '50%', flexShrink: 0,
      backgroundColor: PALETTE[status].dot,
    }} />
  );
}

/** One bar plus its label, positioned against the timeline origin. */
function Bar({
  item, kind, origin, ppd, locale, labels, ownerName,
}: {
  item: GanttTask; kind: 'project' | 'task'; origin: Date; ppd: number;
  locale: string; labels: Record<string, string>; ownerName?: string;
}) {
  const start = parseDay(item.start);
  const end = parseDay(item.end);
  const left = dayIndex(start, origin) * ppd;
  // +1 because both ends are inclusive; the 6px floor keeps a one-day bar visible zoomed out.
  const width = Math.max(6, (dayIndex(end, origin) - dayIndex(start, origin) + 1) * ppd);

  const palette = PALETTE[item.status];
  const height = BAR_HEIGHT[kind];
  const radius = BAR_RADIUS[kind];

  const text = kind === 'project' ? item.name + ' · ' + item.progress + ' %' : item.name;
  // Only put the label inside when the bar is genuinely wide enough for it.
  const fitsInside = width > text.length * LABEL_CHAR_PX + LABEL_PADDING_PX;
  const tooltip = [
    item.name,
    ownerName || null,
    formatDay(start, locale) + ' → ' + formatDay(end, locale),
    item.progress + ' % ' + labels.done,
  ].filter(Boolean).join(' · ');

  return (
    <>
      <div
        title={tooltip}
        style={{
          position: 'absolute', left, width, height, top: 'calc(50% - ' + (height / 2) + 'px)',
          background: palette.track, borderRadius: radius, overflow: 'hidden',
        }}
      >
        {item.status !== 'termine' && (
          <div style={{
            position: 'absolute', left: 0, top: 0, bottom: 0,
            width: Math.min(100, Math.max(0, item.progress)) + '%',
            background: palette.fill, borderRadius: 'inherit',
          }} />
        )}
        {fitsInside && (
          <span style={{
            position: 'absolute', left: 10, top: 0, bottom: 0, right: 8,
            display: 'flex', alignItems: 'center',
            fontSize: '11.5px', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden',
            color: item.progress > LABEL_INVERT_AT || item.status === 'termine'
              ? '#fff' : 'var(--color-foreground, #021f21)',
          }}>{text}</span>
        )}
      </div>
      {!fitsInside && (
        <span style={{
          position: 'absolute', left: left + width + 8, top: 0, bottom: 0,
          display: 'flex', alignItems: 'center',
          fontSize: '11.5px', fontWeight: 600, whiteSpace: 'nowrap',
          color: 'var(--gray-11)', pointerEvents: 'none',
        }}>{text}</span>
      )}
    </>
  );
}

/* ------------------------------------------------------------------- main */

export function GanttChart({
  data,
  viewMode = 'Week',
  showCompleted = false,
  compact = false,
  recenterToken = 0,
  locale = 'fr-FR',
  onTaskClick,
  labels: labelOverrides,
}: GanttChartProps) {
  const labels = { ...DEFAULT_LABELS, ...(labelOverrides || {}) };
  const scrollRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [hovered, setHovered] = useState<string | null>(null);

  const rowHeight = compact ? ROW_HEIGHT_COMPACT : ROW_HEIGHT;
  const zoom = ZOOM[viewMode] || ZOOM.Week;
  const today = useMemo(() => (data && data.today ? parseDay(data.today) : new Date()), [data]);

  // Timeline window. Day/Week/Month start 8 weeks back so recent history stays reachable;
  // Year snaps to the first Monday of January so columns line up with the months.
  const origin = useMemo(() => {
    if (zoom.fromJanuary) {
      // The first Monday *of January*. Taking the Monday of the week containing Jan 4th
      // would fall back into December and draw a stray sliver of the previous year on the
      // axis (a 3-day "2025" cell before "2026").
      const january = new Date(today.getFullYear(), 0, 1);
      const toMonday = (8 - january.getDay()) % 7;
      return new Date(today.getFullYear(), 0, 1 + toMonday);
    }
    return addDays(startOfWeek(today), -7 * zoom.weeksBefore);
  }, [today, zoom.fromJanuary, zoom.weeksBefore]);

  const ppd = zoom.ppd;
  const trackWidth = zoom.days * ppd;
  const todayOffset = dayIndex(today, origin) * ppd;

  /* ----------------------------------------------------------- grouping */

  const groups = useMemo(() => {
    const projects = ((data && data.projects) || []).filter(
      project => showCompleted || project.status !== 'termine',
    );
    return GROUP_ORDER
      .map(status => ({
        status,
        projects: projects
          .filter(project => project.status === status)
          // Soonest deadline first: what falls due next is what needs attention.
          .sort((a, b) => a.end.localeCompare(b.end)),
      }))
      .filter(group => group.projects.length > 0);
  }, [data, showCompleted]);

  const isEmpty = groups.length === 0;

  /* -------------------------------------------------------- axis columns */

  const axis = useMemo(() => {
    const top: { label: string; left: number; width: number }[] = [];
    const bottom: { label: string; left: number; width: number; highlight: boolean; dim: boolean }[] = [];
    const separators: number[] = [];

    if (viewMode === 'Year') {
      // Row 2 steps by month, row 1 carries the year.
      let cursor = 0;
      while (cursor < zoom.days) {
        const day = addDays(origin, cursor);
        const monthEnd = new Date(day.getFullYear(), day.getMonth() + 1, 1);
        const span = Math.min(Math.round((monthEnd.getTime() - day.getTime()) / DAY_MS), zoom.days - cursor);
        bottom.push({
          label: day.toLocaleDateString(locale, { month: 'short' }),
          left: cursor * ppd, width: span * ppd,
          highlight: day.getFullYear() === today.getFullYear() && day.getMonth() === today.getMonth(),
          dim: false,
        });
        if (cursor > 0) separators.push(cursor * ppd);
        cursor += span;
      }
      let yearCursor = 0;
      while (yearCursor < zoom.days) {
        const day = addDays(origin, yearCursor);
        const yearEnd = new Date(day.getFullYear() + 1, 0, 1);
        const span = Math.min(Math.round((yearEnd.getTime() - day.getTime()) / DAY_MS), zoom.days - yearCursor);
        top.push({ label: String(day.getFullYear()), left: yearCursor * ppd, width: span * ppd });
        yearCursor += span;
      }
      return { top, bottom, separators };
    }

    // Row 1: months.
    let cursor = 0;
    while (cursor < zoom.days) {
      const day = addDays(origin, cursor);
      const monthEnd = new Date(day.getFullYear(), day.getMonth() + 1, 1);
      const span = Math.min(Math.round((monthEnd.getTime() - day.getTime()) / DAY_MS), zoom.days - cursor);
      top.push({
        label: day.toLocaleDateString(locale, { month: 'long', year: 'numeric' }),
        left: cursor * ppd, width: span * ppd,
      });
      if (cursor > 0) separators.push(cursor * ppd);
      cursor += span;
    }

    if (viewMode === 'Day') {
      for (let i = 0; i < zoom.days; i++) {
        const day = addDays(origin, i);
        const weekday = day.getDay();
        bottom.push({
          label: String(day.getDate()), left: i * ppd, width: ppd,
          highlight: dayIndex(day, origin) === dayIndex(today, origin),
          dim: weekday === 0 || weekday === 6,
        });
      }
    } else {
      // Week and Month both step by week; only the label differs.
      const currentWeek = isoWeek(today);
      for (let i = 0; i < zoom.days; i += 7) {
        const day = addDays(origin, i);
        const week = isoWeek(day);
        bottom.push({
          label: viewMode === 'Week' ? 'S' + week : String(week),
          left: i * ppd, width: 7 * ppd,
          highlight: week === currentWeek && day.getFullYear() === today.getFullYear(),
          dim: false,
        });
      }
    }
    return { top, bottom, separators };
  }, [viewMode, origin, ppd, zoom.days, locale, today]);

  /* --------------------------------------------------------- re-centring */

  const recentre = useCallback(() => {
    const element = scrollRef.current;
    if (!element) return;
    // Put today a little left of centre: the near future matters more than the past.
    element.scrollLeft = Math.max(0, todayOffset - RECENTRE_RATIO * element.clientWidth);
  }, [todayOffset]);

  // On mount, on zoom change, and whenever the "Today" button bumps the token.
  useEffect(() => { recentre(); }, [recentre, viewMode, recenterToken]);

  /* --------------------------------------------------------- interaction */

  const toggle = (id: string) => {
    setExpanded(previous => {
      const next = new Set(previous);
      if (next.has(id)) { next.delete(id); } else { next.add(id); }
      return next;
    });
  };

  // `data` arrives as a fresh object on every Reflex state delta, so only drop ids that no
  // longer exist rather than clearing the set and collapsing the chart behind the user.
  useEffect(() => {
    const ids = new Set(((data && data.projects) || []).map(project => project.id));
    setExpanded(previous => {
      const kept = new Set([...previous].filter(id => ids.has(id)));
      return kept.size === previous.size ? previous : kept;
    });
  }, [data]);

  /* -------------------------------------------------------------- render */

  const groupLabel: Record<Status, string> = {
    retard: labels.groupLate, encours: labels.groupOngoing, termine: labels.groupDone,
  };

  const trackBackground = viewMode === 'Year'
    ? undefined
    : 'repeating-linear-gradient(to right, ' + GREY.grid + ' 0 1px, transparent 1px ' + (7 * ppd) + 'px)';

  const leftCell: React.CSSProperties = {
    position: 'sticky', left: 0, zIndex: 2, width: LEFT_WIDTH, minWidth: LEFT_WIDTH,
    boxSizing: 'border-box', borderRight: '1px solid ' + GREY.border,
  };

  return (
    <div style={{ flex: 1, minHeight: 0, width: '100%', display: 'flex', flexDirection: 'column' }}>
      <div
        ref={scrollRef}
        style={{
          flex: isEmpty ? '0 0 auto' : 1, minHeight: 0, width: '100%', overflow: 'auto',
          // Keep the wheel inside the chart instead of handing it to the page at the limits.
          overscrollBehavior: 'contain',
        }}
      >
      <div style={{ position: 'relative', width: LEFT_WIDTH + trackWidth, minWidth: '100%' }}>

        {/* ---------------------------------------------------- axis header */}
        <div style={{
          position: 'sticky', top: 0, zIndex: 3, display: 'flex',
          height: HEADER_HEIGHT, background: '#fff',
          borderBottom: '1px solid ' + GREY.borderStrong,
        }}>
          <div style={{
            ...leftCell, zIndex: 4, background: '#fff', display: 'flex',
            alignItems: 'flex-end', padding: '0 12px 8px', gap: 8,
          }}>
            <span style={{
              flex: 1, fontSize: '11px', fontWeight: 600, textTransform: 'uppercase',
              letterSpacing: '0.04em', color: 'var(--gray-11)',
            }}>{labels.columnProject}</span>
            <span style={{
              fontSize: '11px', fontWeight: 600, textTransform: 'uppercase',
              letterSpacing: '0.04em', color: 'var(--gray-11)', textAlign: 'right',
            }}>{labels.columnMeta}</span>
          </div>

          <div style={{ position: 'relative', width: trackWidth, flexShrink: 0 }}>
            {axis.top.map(cell => (
              <div key={'t-' + cell.left} style={{
                position: 'absolute', left: cell.left, width: cell.width, top: 0, height: 28,
                display: 'flex', alignItems: 'center', padding: '0 8px', boxSizing: 'border-box',
                fontSize: '12px', fontWeight: 700, color: 'var(--color-foreground, #021f21)',
                borderLeft: '1px solid ' + GREY.border, whiteSpace: 'nowrap', overflow: 'hidden',
                textTransform: 'capitalize',
              }}>{cell.label}</div>
            ))}
            {axis.bottom.map(cell => (
              <div key={'b-' + cell.left} style={{
                position: 'absolute', left: cell.left, width: cell.width, top: 28, height: 28,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxSizing: 'border-box', fontSize: '11px',
                fontWeight: cell.highlight ? 700 : 500,
                color: cell.highlight ? 'var(--accent-11)' : 'var(--gray-11)',
                background: cell.highlight ? 'var(--accent-3)' : cell.dim ? GREY.weekend : 'transparent',
                borderLeft: '1px solid ' + GREY.grid,
                borderRadius: cell.highlight ? 4 : 0,
                whiteSpace: 'nowrap', overflow: 'hidden', textTransform: 'capitalize',
              }}>{cell.label}</div>
            ))}
          </div>
        </div>

        {/* --------------------------------------------------------- rows */}
        {groups.map(group => (
          <React.Fragment key={group.status}>
            <div style={{
              display: 'flex', height: GROUP_HEIGHT, background: GREY.groupBg,
              borderBottom: '1px solid ' + GREY.border,
            }}>
              <div style={{
                ...leftCell, background: GREY.groupBg, display: 'flex', alignItems: 'center',
                gap: 8, padding: '0 12px',
              }}>
                <span style={{
                  width: 7, height: 7, background: PALETTE[group.status].dot, flexShrink: 0,
                }} />
                <span style={{
                  fontSize: '10.5px', fontWeight: 700, textTransform: 'uppercase',
                  letterSpacing: '0.06em', color: 'var(--gray-12)',
                }}>
                  {groupLabel[group.status]} · {plural(group.projects.length, labels.projectOne, labels.projectMany)}
                </span>
              </div>
              <div style={{ width: trackWidth, flexShrink: 0 }} />
            </div>

            {group.projects.map(project => {
              const isOpen = expanded.has(project.id);
              const hasTasks = project.tasks.length > 0;
              const isHovered = hovered === project.id;
              const isLate = project.status === 'retard';
              const subtitle = isLate
                ? labels.lateBy.replace('{n}', String(project.late_days))
                : groupLabel[project.status];

              return (
                <React.Fragment key={project.id}>
                  <div
                    onMouseEnter={() => setHovered(project.id)}
                    onMouseLeave={() => setHovered(current => (current === project.id ? null : current))}
                    style={{
                      display: 'flex', height: rowHeight.project,
                      borderBottom: '1px solid ' + GREY.grid,
                      background: isHovered ? GREY.rowHover : '#fff',
                      transition: 'background 0.15s ease',
                    }}
                  >
                    <div style={{
                      ...leftCell, background: isHovered ? GREY.rowHover : '#fff',
                      display: 'flex', alignItems: 'center', gap: 8, padding: '0 12px',
                      transition: 'background 0.15s ease',
                    }}>
                      {hasTasks ? (
                        <button
                          onClick={() => toggle(project.id)}
                          aria-expanded={isOpen}
                          style={{
                            width: 18, height: 18, flexShrink: 0, border: 'none', padding: 0,
                            background: 'none', cursor: 'pointer', color: 'var(--gray-11)',
                            fontSize: '11px', lineHeight: 1,
                          }}
                        >{isOpen ? '▾' : '▸'}</button>
                      ) : (
                        <span style={{
                          width: 18, flexShrink: 0, color: GREY.muted, fontSize: '11px',
                          textAlign: 'center',
                        }}>–</span>
                      )}

                      <StatusDot status={project.status} size={7} />

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div
                          onClick={() => onTaskClick && onTaskClick(project.id)}
                          title={project.name}
                          style={{
                            fontSize: '13px', fontWeight: 600,
                            color: 'var(--color-foreground, #021f21)',
                            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                            cursor: onTaskClick ? 'pointer' : 'default',
                          }}
                        >{project.name}</div>
                        <div style={{
                          fontSize: '10.5px', marginTop: 1,
                          fontWeight: isLate ? 600 : 400,
                          color: isLate ? PALETTE.retard.fill : 'var(--gray-11)',
                          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                        }}>
                          {subtitle}
                          {hasTasks && ' · ' + plural(project.tasks.length, labels.taskOne, labels.taskMany)}
                        </div>
                      </div>

                      <span
                        title={project.owner_name}
                        style={{
                          width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
                          background: GREY.avatarBg, color: 'var(--accent-11)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '9.5px', fontWeight: 700,
                        }}
                      >{project.owner}</span>

                      <div style={{
                        width: META_WIDTH, flexShrink: 0, textAlign: 'right', lineHeight: 1.35,
                      }}>
                        <div style={{
                          fontSize: '11px', color: 'var(--gray-11)',
                          fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap',
                        }}>
                          {formatDay(parseDay(project.start), locale)} → {formatDay(parseDay(project.end), locale)}
                        </div>
                        <div style={{
                          fontSize: '11px', fontWeight: 700, fontVariantNumeric: 'tabular-nums',
                          color: isLate ? PALETTE.retard.fill : 'var(--gray-12)',
                        }}>{project.progress} %</div>
                      </div>
                    </div>

                    <div style={{
                      position: 'relative', width: trackWidth, flexShrink: 0,
                      background: trackBackground,
                    }}>
                      <Bar
                        item={project} kind="project" origin={origin} ppd={ppd}
                        locale={locale} labels={labels} ownerName={project.owner_name}
                      />
                    </div>
                  </div>

                  {isOpen && project.tasks.map((task, index) => (
                    <div key={project.id + '-' + index} style={{
                      display: 'flex', height: rowHeight.task,
                      borderBottom: '1px solid ' + GREY.grid, background: GREY.taskBg,
                    }}>
                      <div style={{
                        ...leftCell, background: GREY.taskBg, display: 'flex',
                        alignItems: 'center', gap: 8, padding: '0 12px 0 40px',
                      }}>
                        <StatusDot status={task.status} size={5} />
                        <span
                          title={task.name}
                          style={{
                            flex: 1, minWidth: 0, fontSize: '12px', fontWeight: 500,
                            color: 'var(--gray-11)',
                            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                          }}
                        >{task.name}</span>
                        <div style={{
                          width: META_WIDTH, flexShrink: 0, textAlign: 'right', fontSize: '11px',
                          color: 'var(--gray-11)', fontVariantNumeric: 'tabular-nums',
                          whiteSpace: 'nowrap',
                        }}>
                          {formatDay(parseDay(task.start), locale)} → {formatDay(parseDay(task.end), locale)}
                        </div>
                      </div>
                      <div style={{
                        position: 'relative', width: trackWidth, flexShrink: 0,
                        background: trackBackground,
                      }}>
                        <Bar
                          item={task} kind="task" origin={origin} ppd={ppd}
                          locale={locale} labels={labels}
                        />
                      </div>
                    </div>
                  ))}
                </React.Fragment>
              );
            })}
          </React.Fragment>
        ))}

        {/* --------------------------------------- overlays (non-interactive) */}
        {!isEmpty && <div style={{
          position: 'absolute', top: 0, bottom: 0, left: LEFT_WIDTH, width: trackWidth,
          pointerEvents: 'none', zIndex: 1,
        }}>
          {axis.separators.map(offset => (
            <div key={'sep-' + offset} style={{
              position: 'absolute', top: 0, bottom: 0, left: offset, width: 1,
              background: GREY.border,
            }} />
          ))}
          {todayOffset >= 0 && todayOffset <= trackWidth && (
            <div style={{
              position: 'absolute', top: 0, bottom: 0, left: todayOffset, width: 2,
              background: 'var(--accent-9)', opacity: 0.75,
            }} />
          )}
        </div>}
      </div>
      </div>
      {isEmpty && (
        <div style={{
          padding: '48px 24px', textAlign: 'center', color: 'var(--gray-11)', fontSize: '13px',
        }}>{labels.empty}</div>
      )}
    </div>
  );
}
