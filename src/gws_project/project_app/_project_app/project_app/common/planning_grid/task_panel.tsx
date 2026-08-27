import React, { useMemo, useState } from 'react';
import { useDraggable } from '@dnd-kit/core';
import type { DueStatus, GridTask } from './planning_grid_types';
import { taskDragId } from './planning_grid_types';

export interface TaskPanelProps {
  tasks: GridTask[];
  scheduledLabel: string;
  searchPlaceholder: string;
  noTaskFoundLabel: string;
  helpText: string;
}

// Every text of a task card is searchable, so one query box covers what the
// project / company / person filters used to do, plus the due date.
function taskMatches(task: GridTask, query: string): boolean {
  return [task.title, task.project_title, task.company_name, task.assignee_name, task.due_date_text]
    .filter(Boolean)
    .some((field) => (field as string).toLowerCase().includes(query));
}

// Constellab brand colors (see gws_theme.css): tertiary = pink, secondary = violet.
function dueDateColor(status?: DueStatus): string {
  if (status === 'overdue') return 'var(--tertiary-11)';
  if (status === 'this_week') return 'var(--secondary-11)';
  return 'var(--gray-9)';
}

function TaskPanelItem({ task, scheduledLabel }: { task: GridTask; scheduledLabel: string }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({ id: taskDragId(task.id) });

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      style={{
        padding: '8px 10px',
        marginBottom: '8px',
        borderRadius: '8px',
        border: '1px solid var(--gray-5)',
        background: task.is_scheduled ? 'var(--gray-2)' : 'var(--gray-1)',
        opacity: isDragging ? 0.5 : 1,
        cursor: 'grab',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '6px' }}>
        <span
          style={{
            fontSize: '13px',
            fontWeight: 600,
            color: 'var(--gray-12)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {task.title}
        </span>
        {task.is_scheduled && (
          <span
            style={{
              fontSize: '9px',
              fontWeight: 700,
              padding: '2px 6px',
              borderRadius: '99px',
              background: 'var(--accent-3)',
              color: 'var(--accent-11)',
              whiteSpace: 'nowrap',
              flexShrink: 0,
            }}
          >
            {scheduledLabel}
          </span>
        )}
      </div>
      <div
        style={{
          fontSize: '11px',
          color: 'var(--gray-9)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {task.project_title}
        {task.company_name ? ` · ${task.company_name}` : ''}
      </div>
      <div style={{ fontSize: '11px', color: 'var(--gray-9)' }}>{task.assignee_name}</div>
      {task.due_date_text && (
        <div
          style={{
            fontSize: '11px',
            fontWeight: task.due_status ? 700 : 400,
            color: dueDateColor(task.due_status),
          }}
        >
          {task.due_date_text}
        </div>
      )}
    </div>
  );
}

export function TaskPanel({ tasks, scheduledLabel, searchPlaceholder, noTaskFoundLabel, helpText }: TaskPanelProps) {
  const [query, setQuery] = useState('');

  // Filtering client-side keeps the list responsive on every keystroke: the panel
  // already holds every task of the week, so no round trip is needed.
  const visibleTasks = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return tasks;
    return tasks.filter((task) => taskMatches(task, normalized));
  }, [tasks, query]);

  return (
    <div style={{ width: '260px', flexShrink: 0, display: 'flex', flexDirection: 'column', minHeight: 0, paddingRight: '8px' }}>
      <input
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder={searchPlaceholder}
        style={{
          width: '100%',
          boxSizing: 'border-box',
          marginBottom: '8px',
          padding: '6px 10px',
          fontSize: '13px',
          fontFamily: 'inherit',
          borderRadius: '8px',
          border: '1px solid var(--gray-6)',
          background: 'var(--gray-1)',
          color: 'var(--gray-12)',
          outline: 'none',
        }}
      />

      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        {visibleTasks.map((task) => (
          <TaskPanelItem key={task.id} task={task} scheduledLabel={scheduledLabel} />
        ))}
        {visibleTasks.length === 0 && (
          <div style={{ fontSize: '12px', color: 'var(--gray-9)', padding: '8px 2px' }}>{noTaskFoundLabel}</div>
        )}
      </div>

      <div
        style={{
          flexShrink: 0,
          paddingTop: '8px',
          marginTop: '4px',
          borderTop: '1px solid var(--gray-4)',
          fontSize: '11px',
          lineHeight: 1.4,
          color: 'var(--gray-9)',
        }}
      >
        {helpText}
      </div>
    </div>
  );
}
