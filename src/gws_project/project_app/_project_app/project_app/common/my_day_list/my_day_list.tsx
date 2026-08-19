import React, { useEffect, useMemo, useState } from 'react';
import type { DragEndEvent } from '@dnd-kit/core';
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { MyDayItemRow } from './my_day_item';
import type { MyDayItem, MyDayListProps } from './my_day_list_types';

export function MyDayList({ items, onReorder, onItemClick, reorderLabel }: MyDayListProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // Local order applied on drop so the list settles under the pointer instead of
  // snapping back while the server rewrites the slot times. Cleared as soon as a fresh
  // `items` array arrives, which makes the server's answer the truth again.
  const [pendingOrder, setPendingOrder] = useState<string[] | null>(null);
  useEffect(() => {
    setPendingOrder(null);
  }, [items]);

  const orderedItems: MyDayItem[] = useMemo(() => {
    if (!pendingOrder) return items;
    const byId = new Map(items.map((item) => [item.slot_id, item]));
    const ordered = pendingOrder
      .map((slotId) => byId.get(slotId))
      .filter((item): item is MyDayItem => item !== undefined);
    // Anything the pending order does not know about stays visible, at the end.
    const known = new Set(pendingOrder);
    return [...ordered, ...items.filter((item) => !known.has(item.slot_id))];
  }, [items, pendingOrder]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const currentIds = orderedItems.map((item) => item.slot_id);
    const from = currentIds.indexOf(active.id as string);
    const to = currentIds.indexOf(over.id as string);
    if (from === -1 || to === -1) return;

    const nextIds = arrayMove(currentIds, from, to);
    setPendingOrder(nextIds);
    onReorder?.({ ordered_slot_ids: nextIds });
  };

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext
        items={orderedItems.map((item) => item.slot_id)}
        strategy={verticalListSortingStrategy}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', width: '100%' }}>
          {orderedItems.map((item) => (
            <MyDayItemRow
              key={item.slot_id}
              item={item}
              onItemClick={onItemClick}
              reorderLabel={reorderLabel}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}
