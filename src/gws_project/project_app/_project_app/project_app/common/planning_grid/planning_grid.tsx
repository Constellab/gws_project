import React, { useMemo, useState } from 'react';
import type { DragEndEvent, DragStartEvent } from '@dnd-kit/core';
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  MeasuringStrategy,
  PointerSensor,
  pointerWithin,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { DayCell } from './day_cell';
import { TaskPanel } from './task_panel';
import type { GridSlot, PlanningGridProps } from './planning_grid_types';
import { SLOT_DRAG_PREFIX, TASK_DRAG_PREFIX, parseCellDropId } from './planning_grid_types';
import { dayBoundsFromSettings, isoDateOf, minutesToTime, pixelYToClockMinutes } from './planning_grid_utils';

function PersonAvatar({ name, photoUrl }: { name: string; photoUrl?: string }) {
  if (photoUrl) {
    return (
      <img
        src={photoUrl}
        alt={name}
        style={{ width: '24px', height: '24px', borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }}
      />
    );
  }
  return (
    <div
      style={{
        width: '24px',
        height: '24px',
        borderRadius: '50%',
        flexShrink: 0,
        background: 'var(--accent-4)',
        color: 'var(--accent-11)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '11px',
        fontWeight: 700,
      }}
    >
      {name.charAt(0).toUpperCase()}
    </div>
  );
}

export function PlanningGrid({ gridData, tasks, onSlotCreate, onSlotMove, onSlotResize, onSlotDelete }: PlanningGridProps) {
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor)
  );

  const measuring = useMemo(() => ({ droppable: { strategy: MeasuringStrategy.BeforeDragging } }), []);

  const bounds = useMemo(
    () =>
      dayBoundsFromSettings(
        gridData.day_start_time,
        gridData.day_end_time,
        gridData.lunch_start_time,
        gridData.lunch_end_time
      ),
    [gridData.day_start_time, gridData.day_end_time, gridData.lunch_start_time, gridData.lunch_end_time]
  );

  const slotsByCell = useMemo(() => {
    const map = new Map<string, GridSlot[]>();
    for (const slot of gridData.slots) {
      const key = `${slot.assigned_user_id}:${isoDateOf(slot.start_datetime)}`;
      const list = map.get(key) || [];
      list.push(slot);
      map.set(key, list);
    }
    return map;
  }, [gridData.slots]);

  const activeTask = activeId?.startsWith(TASK_DRAG_PREFIX)
    ? tasks.find((t) => t.id === activeId.slice(TASK_DRAG_PREFIX.length))
    : null;
  const activeSlot = activeId?.startsWith(SLOT_DRAG_PREFIX)
    ? gridData.slots.find((s) => s.id === activeId.slice(SLOT_DRAG_PREFIX.length))
    : null;

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);
    if (!over) return;

    const target = parseCellDropId(over.id as string);
    if (!target) return;

    // The dragged item's own final rect (tracked by dnd-kit regardless of which
    // sensor drove the drag) tells us where it was actually dropped within the
    // target column - this is what lets a drop position the slot at the time of
    // day it was dropped on, instead of always defaulting to day start.
    const translatedRect = active.rect.current.translated;
    const offsetInColumn = translatedRect ? translatedRect.top - over.rect.top : 0;
    const startTime = minutesToTime(pixelYToClockMinutes(offsetInColumn, bounds, gridData.step_minutes));

    const activeIdStr = active.id as string;

    if (activeIdStr.startsWith(TASK_DRAG_PREFIX)) {
      const taskId = activeIdStr.slice(TASK_DRAG_PREFIX.length);
      onSlotCreate?.({ task_id: taskId, person_id: target.personId, day: target.day, start_time: startTime });
      return;
    }

    if (activeIdStr.startsWith(SLOT_DRAG_PREFIX)) {
      const slotId = activeIdStr.slice(SLOT_DRAG_PREFIX.length);
      onSlotMove?.({ slot_id: slotId, person_id: target.personId, day: target.day, start_time: startTime });
    }
  };

  return (
    <DndContext
      sensors={sensors}
      measuring={measuring}
      collisionDetection={pointerWithin}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div style={{ display: 'flex', width: '100%', flex: 1, minHeight: 0, gap: '16px' }}>
        <TaskPanel tasks={tasks} scheduledLabel={gridData.scheduled_label} />

        <div style={{ flex: 1, minWidth: 0, overflow: 'auto' }}>
          {/* Header row: empty corner + day labels. Non-working days are already
              excluded server-side, so every column here is a working day. */}
          <div style={{ display: 'flex', position: 'sticky', top: 0, zIndex: 2, background: 'var(--color-background)' }}>
            <div style={{ width: '180px', flexShrink: 0 }} />
            {gridData.days.map((day, i) => (
              <div
                key={day}
                style={{
                  flex: '1 0 140px',
                  minWidth: '140px',
                  padding: '6px 8px',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--gray-11)',
                  textAlign: 'center',
                  borderLeft: '1px solid var(--gray-4)',
                  background: 'var(--gray-2)',
                }}
              >
                {gridData.day_labels[i]}
              </div>
            ))}
          </div>

          {/* One row per person: photo/name/capacity bar + one droppable cell per day */}
          {gridData.people.map((person) => (
            <div key={person.id} style={{ display: 'flex', borderBottom: '2px solid var(--gray-6)' }}>
              <div style={{ width: '180px', flexShrink: 0, padding: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <PersonAvatar name={person.name} photoUrl={person.photo_url} />
                  <div
                    style={{
                      fontSize: '13px',
                      fontWeight: 600,
                      color: 'var(--gray-12)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {person.name}
                  </div>
                </div>
                <div
                  style={{
                    fontSize: '11px',
                    // Constellab brand pink (tertiary), consistent with the overlap
                    // highlighting and the overload/overlap banners.
                    color: person.is_overloaded ? 'var(--tertiary-11)' : 'var(--gray-9)',
                    marginBottom: '4px',
                  }}
                >
                  {person.total_hours}h / {person.capacity_hours}h
                </div>
                <div style={{ height: '6px', borderRadius: '99px', background: 'var(--gray-4)', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${Math.min((person.total_hours / Math.max(person.capacity_hours, 1)) * 100, 100)}%`,
                      background: person.is_overloaded ? 'var(--tertiary-9)' : 'var(--accent-9)',
                    }}
                  />
                </div>
              </div>
              {gridData.days.map((day) => (
                <DayCell
                  key={day}
                  personId={person.id}
                  day={day}
                  slots={slotsByCell.get(`${person.id}:${day}`) || []}
                  bounds={bounds}
                  stepMinutes={gridData.step_minutes}
                  lunchLabel={gridData.lunch_label}
                  onResize={(slotId, edge, newTime) => onSlotResize?.({ slot_id: slotId, edge, new_time: newTime })}
                  onDelete={onSlotDelete}
                />
              ))}
            </div>
          ))}
        </div>
      </div>

      <DragOverlay>
        {activeTask ? (
          <div
            style={{
              padding: '8px 10px',
              borderRadius: '8px',
              background: 'white',
              border: '1px solid var(--gray-6)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              width: '220px',
            }}
          >
            <div style={{ fontSize: '13px', fontWeight: 600 }}>{activeTask.title}</div>
          </div>
        ) : activeSlot ? (
          <div
            style={{
              padding: '4px 6px',
              borderRadius: '6px',
              background: 'var(--accent-4)',
              border: '1px solid var(--accent-8)',
              width: '140px',
            }}
          >
            <div style={{ fontSize: '11px', fontWeight: 600 }}>{activeSlot.task_title}</div>
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
