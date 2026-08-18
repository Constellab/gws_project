import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { PlanningSlotBlock } from './planning_slot_block';
import { cellDropId } from './planning_grid_types';
import type { GridSlot, ResizeEdge } from './planning_grid_types';
import { DayBounds, PX_PER_MINUTE, clockMinutesToPixels, dayColumnHeightPx } from './planning_grid_utils';

export interface DayCellProps {
  personId: string;
  day: string;
  slots: GridSlot[];
  bounds: DayBounds;
  stepMinutes: number;
  lunchLabel: string;
  onResize?: (slotId: string, edge: ResizeEdge, newTime: string) => void;
  onDelete?: (slotId: string) => void;
}

export function DayCell({ personId, day, slots, bounds, stepMinutes, lunchLabel, onResize, onDelete }: DayCellProps) {
  const { setNodeRef, isOver } = useDroppable({ id: cellDropId(personId, day) });

  const height = dayColumnHeightPx(bounds);
  const hourPx = PX_PER_MINUTE * 60;

  const hasLunch = bounds.lunchEndMinutes > bounds.lunchStartMinutes;
  const lunchTop = clockMinutesToPixels(bounds.lunchStartMinutes, bounds);
  const lunchHeight = hasLunch ? clockMinutesToPixels(bounds.lunchEndMinutes, bounds) - lunchTop : 0;

  return (
    <div
      ref={setNodeRef}
      data-day-column="true"
      style={{
        position: 'relative',
        flex: '1 0 140px',
        minWidth: '140px',
        height: `${height}px`,
        borderLeft: '1px solid var(--gray-4)',
        // backgroundColor (not the `background` shorthand): a shorthand resets
        // background-image as an implicit side effect of the CSSOM setter, so
        // toggling `isOver` on drag-hover would silently wipe the hour gridlines
        // the very first time a cell was dragged over (which is exactly what
        // happened to the columns that had ever received a dropped slot).
        backgroundColor: isOver ? 'var(--accent-2)' : 'var(--gray-1)',
        backgroundImage: `repeating-linear-gradient(to bottom, transparent, transparent ${hourPx - 1}px, var(--gray-4) ${hourPx - 1}px, var(--gray-4) ${hourPx}px)`,
      }}
    >
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
          onResize={onResize}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
