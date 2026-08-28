import React, { useMemo } from 'react';
import { useDroppable } from '@dnd-kit/core';
import { PlanningSlotBlock } from './planning_slot_block';
import { cellDropId } from './planning_grid_types';
import type { GridSlot, ResizeEdge } from './planning_grid_types';
import {
  DayBounds,
  clockMinutesToPixels,
  dayColumnHeightPx,
  gridLineMinutes,
  minutesToTime,
  pixelYToClockMinutes,
} from './planning_grid_utils';

export interface DayCellProps {
  personId: string;
  day: string;
  slots: GridSlot[];
  bounds: DayBounds;
  stepMinutes: number;
  lunchLabel: string;
  selectedSlotId: string | null;
  onResize?: (slotId: string, edge: ResizeEdge, newTime: string) => void;
  onSelectSlot?: (slotId: string) => void;
  onOpenSlot?: (slotId: string) => void;
  onSlotTaskClick?: (taskId: string) => void;
  onEmptyClick?: (personId: string, day: string, startTime: string) => void;
}

export function DayCell({
  personId,
  day,
  slots,
  bounds,
  stepMinutes,
  lunchLabel,
  selectedSlotId,
  onResize,
  onSelectSlot,
  onOpenSlot,
  onSlotTaskClick,
  onEmptyClick,
}: DayCellProps) {
  const { setNodeRef, isOver } = useDroppable({ id: cellDropId(personId, day) });

  const height = dayColumnHeightPx(bounds);
  const gridLines = useMemo(() => gridLineMinutes(bounds), [bounds]);

  // Only a click on the column's own background counts: a click on a slot (or at
  // the end of a drag, see PlanningGrid's guard) must not open the add dialog.
  const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!onEmptyClick || event.target !== event.currentTarget) return;
    const offsetY = event.clientY - event.currentTarget.getBoundingClientRect().top;
    onEmptyClick(personId, day, minutesToTime(pixelYToClockMinutes(offsetY, bounds, stepMinutes)));
  };

  const hasLunch = bounds.lunchEndMinutes > bounds.lunchStartMinutes;
  const lunchTop = clockMinutesToPixels(bounds.lunchStartMinutes, bounds);
  const lunchHeight = hasLunch ? clockMinutesToPixels(bounds.lunchEndMinutes, bounds) - lunchTop : 0;

  return (
    <div
      ref={setNodeRef}
      data-day-column="true"
      onClick={handleClick}
      style={{
        position: 'relative',
        flex: '1 0 140px',
        minWidth: '140px',
        height: `${height}px`,
        borderLeft: '1px solid var(--gray-4)',
        backgroundColor: isOver ? 'var(--accent-2)' : 'var(--gray-1)',
        cursor: onEmptyClick ? 'copy' : 'default',
      }}
    >
      {/* Gridlines: solid on the hour (labelled by the row's hour axis), dashed on
          the half hour (deliberately unlabelled). Drawn as elements rather than a
          repeating gradient, which cannot dash a horizontal rule; pointerEvents
          none keeps them out of the drop, resize and click handling. */}
      {gridLines.map((line) => (
        <div
          key={line.minutes}
          style={{
            position: 'absolute',
            top: `${clockMinutesToPixels(line.minutes, bounds)}px`,
            left: 0,
            right: 0,
            borderTop: line.isHour ? '1px solid var(--gray-4)' : '1px dashed var(--gray-4)',
            pointerEvents: 'none',
          }}
        />
      ))}
      {/* Lunch break: real, colored, non-schedulable space (a drop/resize landing
          here is redirected to its nearest edge by clampOutsideLunch). */}
      {hasLunch && (
        <div
          style={{
            position: 'absolute',
            top: `${lunchTop}px`,
            left: 0,
            right: 0,
            height: `${lunchHeight}px`,
            background:
              'repeating-linear-gradient(45deg, var(--gray-5), var(--gray-5) 6px, var(--gray-3) 6px, var(--gray-3) 12px)',
            borderTop: '1px solid var(--gray-6)',
            borderBottom: '1px solid var(--gray-6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
          }}
        >
          {lunchHeight > 20 && (
            <span style={{ fontSize: '10px', fontWeight: 600, color: 'var(--gray-10)' }}>{lunchLabel}</span>
          )}
        </div>
      )}
      {slots.map((slot) => (
        <PlanningSlotBlock
          key={slot.id}
          slot={slot}
          bounds={bounds}
          stepMinutes={stepMinutes}
          isSelected={slot.id === selectedSlotId}
          onResize={onResize}
          onSelect={onSelectSlot}
          onOpen={onOpenSlot}
          onTaskClick={onSlotTaskClick}
        />
      ))}
    </div>
  );
}
