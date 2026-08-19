import React, { useState } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { MyDayItemRowProps } from './my_day_list_types';

/** Whether a row carries a deadline warning.
 *
 * An overdue task and a slot scheduled past its own due date are the same kind of problem
 * for whoever reads the row: the deadline is already lost either way.
 */
function isLate(dueStatus?: string | null): boolean {
  return dueStatus === 'overdue' || dueStatus === 'after_due';
}

/** Colour of the row's left edge marker (liseré).
 *
 * Neutral unless the row is late: the marker only carries meaning if a calm day leaves it
 * grey, and this app's accent scale is too close to the tertiary one to hold the contrast.
 */
function edgeColorFor(dueStatus?: string | null): string {
  return isLate(dueStatus) ? 'var(--tertiary-11)' : 'var(--gray-6)';
}

function GripIcon() {
  return (
    <svg width="10" height="16" viewBox="0 0 10 16" fill="currentColor" aria-hidden="true">
      <circle cx="2" cy="3" r="1.3" />
      <circle cx="8" cy="3" r="1.3" />
      <circle cx="2" cy="8" r="1.3" />
      <circle cx="8" cy="8" r="1.3" />
      <circle cx="2" cy="13" r="1.3" />
      <circle cx="8" cy="13" r="1.3" />
    </svg>
  );
}

export function MyDayItemRow({ item, onItemClick, reorderLabel }: MyDayItemRowProps) {
  const [isHovered, setIsHovered] = useState(false);
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.slot_id,
  });

  const isRowLate = isLate(item.due_status);

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.625rem 0.875rem',
    background: 'var(--card-background)',
    border: '1px solid var(--gray-6)',
    borderLeft: `3px solid ${edgeColorFor(item.due_status)}`,
    borderRadius: '0.5rem',
    boxShadow: isDragging ? '0 0.5rem 1rem var(--gray-a5)' : 'none',
  };

  return (
    <div ref={setNodeRef} style={style}>
      {/* The drag listeners live on the handle alone: bound to the whole row they would
          swallow the click that opens the task. */}
      <div
        {...attributes}
        {...listeners}
        title={reorderLabel}
        aria-label={reorderLabel}
        style={{
          display: 'flex',
          alignItems: 'center',
          color: isHovered ? 'var(--gray-11)' : 'var(--gray-8)',
          cursor: 'grab',
          touchAction: 'none',
          flexShrink: 0,
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <GripIcon />
      </div>

      <span
        style={{
          fontSize: '0.8125rem',
          fontWeight: 600,
          color: 'var(--gray-11)',
          fontVariantNumeric: 'tabular-nums',
          whiteSpace: 'nowrap',
          flexShrink: 0,
        }}
      >
        {item.time_range}
      </span>

      <div
        onClick={() => onItemClick?.(item.task_id)}
        style={{ flex: 1, minWidth: 0, cursor: onItemClick ? 'pointer' : 'default' }}
      >
        {item.parent_task_title && (
          <div
            style={{
              fontSize: '0.6875rem',
              color: 'var(--gray-9)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {item.parent_task_title}
          </div>
        )}
        <div
          style={{
            fontSize: '0.875rem',
            fontWeight: 500,
            color: 'var(--gray-12)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {item.task_title}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.6875rem',
            color: 'var(--gray-9)',
            marginTop: '0.125rem',
          }}
        >
          <span
            style={{
              color: 'var(--accent-11)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {item.project_title}
          </span>
          {item.assignee_note && <span>· {item.assignee_note}</span>}
        </div>
      </div>

      {item.due_date_text && (
        <span
          style={{
            fontSize: '0.6875rem',
            fontWeight: 600,
            color: isRowLate ? 'var(--tertiary-11)' : 'var(--gray-9)',
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          {item.due_date_text}
        </span>
      )}
    </div>
  );
}
