import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import type { DueStatus, GridTask } from './planning_grid_types';
import { taskDragId } from './planning_grid_types';

export interface TaskPanelProps {
  tasks: GridTask[];
  scheduledLabel: string;
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

export function TaskPanel({ tasks, scheduledLabel }: TaskPanelProps) {
  return (
    <div style={{ width: '260px', flexShrink: 0, overflowY: 'auto', paddingRight: '8px' }}>
      {tasks.map((task) => (
        <TaskPanelItem key={task.id} task={task} scheduledLabel={scheduledLabel} />
      ))}
    </div>
  );
}
