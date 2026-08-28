import React, { useCallback, useRef } from 'react';
import { useDraggable } from '@dnd-kit/core';
import type { GridSlot, ResizeEdge } from './planning_grid_types';
import { slotDragId } from './planning_grid_types';
import {
  DayBounds,
  clockMinutesToPixels,
  clockTimeOf,
  minutesToTime,
  pixelYToClockMinutes,
  timeToMinutes,
} from './planning_grid_utils';

export interface PlanningSlotBlockProps {
  slot: GridSlot;
  bounds: DayBounds;
  stepMinutes: number;
  isSelected: boolean;
  onResize?: (slotId: string, edge: ResizeEdge, newTime: string) => void;
  onSelect?: (slotId: string) => void;
  onOpen?: (slotId: string) => void;
  onTaskClick?: (taskId: string) => void;
}

const MIN_DURATION_MINUTES = 30;

export function PlanningSlotBlock({
  slot,
  bounds,
  stepMinutes,
  isSelected,
  onResize,
  onSelect,
  onOpen,
  onTaskClick,
}: PlanningSlotBlockProps) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: slotDragId(slot.id),
  });

  const startMinutes = timeToMinutes(clockTimeOf(slot.start_datetime));
  const endMinutes = timeToMinutes(clockTimeOf(slot.end_datetime));

  // Tracked in a ref (not state) so the pointermove/pointerup listeners created at
  // drag-start always see the latest value; a tick counter forces the re-renders
  // needed to reflect it visually while dragging.
  const resizeRef = useRef<{ edge: ResizeEdge; start: number; end: number } | null>(null);
  const [, setTick] = React.useState(0);
  const blockRef = useRef<HTMLDivElement | null>(null);

  const live = resizeRef.current;
  const effectiveStart = live ? live.start : startMinutes;
  const effectiveEnd = live ? live.end : endMinutes;

  const top = clockMinutesToPixels(effectiveStart, bounds);
  const bottom = clockMinutesToPixels(effectiveEnd, bounds);
  const height = Math.max(bottom - top, 4);

  // Resize is deliberately kept OUTSIDE of dnd-kit's DndContext: dnd-kit has no
  // resize primitive, and the drag (move) listeners below are only ever spread on
  // the block's inner "body" div, never on these handles, so the two interactions
  // never fight over the same pointerdown.
  const startResize = useCallback(
    (edge: ResizeEdge) => (event: React.PointerEvent<HTMLDivElement>) => {
      event.stopPropagation();
      event.preventDefault();

      const dayColumn = blockRef.current?.closest('[data-day-column]') as HTMLElement | null;
      if (!dayColumn) return;
      const columnRect = dayColumn.getBoundingClientRect();

      resizeRef.current = { edge, start: startMinutes, end: endMinutes };
      setTick((t) => t + 1);

      const handleMove = (moveEvent: PointerEvent) => {
        const pointerY = moveEvent.clientY - columnRect.top;
        const newClockMinutes = pixelYToClockMinutes(pointerY, bounds, stepMinutes);
        const current = resizeRef.current;
        if (!current) return;

        if (edge === 'start') {
          resizeRef.current = { ...current, start: Math.min(newClockMinutes, endMinutes - MIN_DURATION_MINUTES) };
        } else {
          resizeRef.current = { ...current, end: Math.max(newClockMinutes, startMinutes + MIN_DURATION_MINUTES) };
        }
        setTick((t) => t + 1);
      };

      const handleUp = () => {
        window.removeEventListener('pointermove', handleMove);
        window.removeEventListener('pointerup', handleUp);
        const finalState = resizeRef.current;
        resizeRef.current = null;
        setTick((t) => t + 1);
        if (finalState && onResize) {
          const finalMinutes = finalState.edge === 'start' ? finalState.start : finalState.end;
          onResize(slot.id, finalState.edge, minutesToTime(finalMinutes));
        }
      };

      window.addEventListener('pointermove', handleMove);
      window.addEventListener('pointerup', handleUp);
    },
    [bounds, stepMinutes, startMinutes, endMinutes, onResize, slot.id]
  );

  return (
    <div
      ref={blockRef}
      // Click selects (the keyboard Delete of PlanningGrid acts on the selection) and
      // shows the task in the details panel; right click opens the slot dialog, which is
      // where the hours are edited. stopPropagation keeps both away from the day column,
      // whose own click is what adds a task on empty space.
      onClick={(event) => {
        event.stopPropagation();
        onSelect?.(slot.id);
        onTaskClick?.(slot.task_id);
      }}
      onContextMenu={(event) => {
        // The slot's own menu replaces the browser's: right clicking a créneau is how
        // its hours are edited, so the default menu would only ever be in the way.
        event.preventDefault();
        event.stopPropagation();
        onSelect?.(slot.id);
        onOpen?.(slot.id);
      }}
      style={{
        position: 'absolute',
        top: `${top}px`,
        height: `${height}px`,
        left: '4px',
        right: '4px',
        borderRadius: '6px',
        // Constellab brand pink (tertiary) for overlap, consistent with the
        // overload/overlap warnings and the person capacity indicator.
        background: slot.is_overlapping ? 'var(--tertiary-4)' : 'var(--accent-4)',
        border: slot.is_overlapping ? '1px solid var(--tertiary-8)' : '1px solid var(--accent-8)',
        boxShadow: isDragging ? '0 6px 14px rgba(0,0,0,0.18)' : '0 1px 2px rgba(0,0,0,0.06)',
        outline: isSelected ? '2px solid var(--accent-9)' : 'none',
        outlineOffset: '1px',
        opacity: isDragging ? 0.4 : 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        zIndex: live ? 5 : 1,
      }}
    >
      {/* Draggable body (move): title + time range */}
      <div
        ref={setNodeRef}
        {...attributes}
        {...listeners}
        style={{ flex: 1, minHeight: 0, padding: '4px 6px', cursor: 'grab', overflow: 'hidden' }}
        title={slot.task_title}
      >
        <div
          style={{
            fontSize: '11px',
            fontWeight: 600,
            color: slot.is_overlapping ? 'var(--tertiary-12)' : 'var(--accent-12)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {slot.task_title}
        </div>
        {/* Project before hours: a short slot is clipped from the bottom, and the
            project is what has to survive that clipping (the hours are already
            readable from the block's own position and height). */}
        {slot.project_title && (
          <div
            style={{
              fontSize: '10px',
              color: slot.is_overlapping ? 'var(--tertiary-10)' : 'var(--accent-10)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {slot.project_title}
          </div>
        )}
        <div style={{ fontSize: '10px', color: slot.is_overlapping ? 'var(--tertiary-11)' : 'var(--accent-11)' }}>
          {minutesToTime(effectiveStart)} - {minutesToTime(effectiveEnd)}
        </div>
      </div>

      {/* Resize handles */}
      <div
        onPointerDown={startResize('start')}
        style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '6px', cursor: 'ns-resize' }}
      />
      <div
        onPointerDown={startResize('end')}
        style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: '6px', cursor: 'ns-resize' }}
      />
    </div>
  );
}
