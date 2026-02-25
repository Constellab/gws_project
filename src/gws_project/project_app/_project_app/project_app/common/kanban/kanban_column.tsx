import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { SortableCard } from './sortable_card';
import type { ColumnProps } from './kanban_types';

export function Column({ column, cards, cardRenderer, onCardClick, statusColorMap, priorityColorMap, userColorMap }: ColumnProps) {
  const cardIds = cards.map((card) => card.id);
  const { setNodeRef } = useDroppable({
    id: column.id,
  });

  const colorPrefix = statusColorMap?.[column.id] || 'gray';

  return (
    <div
      ref={setNodeRef}
      style={{
        flex: 1,
        minWidth: '280px',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        marginRight: '16px',
      }}
    >
      {/* Column header with colored top border */}
      <div style={{
        borderTopWidth: '3px',
        borderTopStyle: 'solid',
        borderTopColor: `var(--${colorPrefix}-9)`,
        borderLeftWidth: '1px',
        borderLeftStyle: 'solid',
        borderLeftColor: `var(--${colorPrefix}-4)`,
        borderRightWidth: '1px',
        borderRightStyle: 'solid',
        borderRightColor: `var(--${colorPrefix}-4)`,
        borderRadius: '12px 12px 0 0',
        backgroundColor: `var(--${colorPrefix}-2)`,
        padding: '14px 18px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontWeight: 750, fontSize: '15px', color: 'var(--gray-12)' }}>
            {column.title}
          </span>
          <span style={{
            fontSize: '12px',
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: '99px',
            backgroundColor: `var(--${colorPrefix}-3)`,
            color: `var(--${colorPrefix}-9)`,
          }}>
            {cards.length}
          </span>
        </div>
      </div>
      {/* Cards container */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        backgroundColor: `var(--${colorPrefix}-2)`,
        borderRadius: '0 0 12px 12px',
        borderWidth: '0 1px 1px 1px',
        borderStyle: 'solid',
        borderColor: `var(--${colorPrefix}-4)`,
        padding: '12px',
      }}>
        <SortableContext items={cardIds} strategy={verticalListSortingStrategy}>
          <div style={{ minHeight: '100px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {cards.map((card) => (
              <SortableCard
                key={card.id}
                id={card.id}
                card={card}
                customRenderer={cardRenderer}
                onCardClick={onCardClick}
                priorityColorMap={priorityColorMap}
                userColorMap={userColorMap}
                columnColorPrefix={colorPrefix}
              />
            ))}
          </div>
        </SortableContext>
      </div>
    </div>
  );
}
