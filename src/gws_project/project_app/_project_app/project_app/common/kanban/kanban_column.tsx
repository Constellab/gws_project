import React, { useCallback, useEffect, useRef } from 'react';
import { useDroppable } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { SortableCard } from './sortable_card';
import { AddCardRow } from './add_card_row';
import type { ColumnProps } from './kanban_types';

export const Column = React.memo(function Column({
  column,
  cards,
  cardRenderer,
  onCardClick,
  statusColorMap,
  priorityColorMap,
  userColorMap,
  quickAddColumnId,
  quickAddTitle,
  quickAddCanSubmit,
  quickAddIsCreating,
  quickAddBrowseOpen,
  quickAddCurrentProjectTitle,
  quickAddBreadcrumbTasks,
  quickAddProjects,
  quickAddTasks,
  onQuickAddOpen,
  onQuickAddCancel,
  onQuickAddTitleChange,
  onQuickAddToggleBrowse,
  onQuickAddNavigate,
  onQuickAddSelectHere,
  onQuickAddSubmit,
}: ColumnProps) {
  const cardIds = cards.map((card) => card.id);
  const { setNodeRef } = useDroppable({
    id: column.id,
  });

  const colorPrefix = statusColorMap?.[column.id] || 'gray';

  // Stable reference so per-card "+" buttons don't defeat SortableCard's memoization
  const handleAddClick = useCallback(() => {
    onQuickAddOpen?.(column.id);
  }, [onQuickAddOpen, column.id]);

  // Scroll the add-task row into view whenever it opens for this column, so it's
  // reachable in one click even when the column already has many cards
  const addRowRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (quickAddColumnId === column.id) {
      addRowRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [quickAddColumnId, column.id]);

  return (
    <div
      ref={setNodeRef}
      style={{
        // Grow to fill a wide board, but never shrink below a readable width: the
        // board container scrolls horizontally instead of squeezing the cards
        flex: '1 0 350px',
        minWidth: '350px',
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
        <button
          data-kanban-quick-add
          onClick={handleAddClick}
          title="Add task"
          style={{
            width: '24px',
            height: '24px',
            flexShrink: 0,
            borderRadius: '6px',
            border: 'none',
            background: `var(--${colorPrefix}-3)`,
            color: `var(--${colorPrefix}-11)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '16px',
            lineHeight: 1,
            cursor: 'pointer',
          }}
        >
          +
        </button>
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
        <div style={{ minHeight: '100px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <SortableContext items={cardIds} strategy={verticalListSortingStrategy}>
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
          </SortableContext>
          <div ref={addRowRef}>
            <AddCardRow
              columnId={column.id}
              quickAddColumnId={quickAddColumnId}
              quickAddTitle={quickAddTitle}
              quickAddCanSubmit={quickAddCanSubmit}
              quickAddIsCreating={quickAddIsCreating}
              quickAddBrowseOpen={quickAddBrowseOpen}
              quickAddCurrentProjectTitle={quickAddCurrentProjectTitle}
              quickAddBreadcrumbTasks={quickAddBreadcrumbTasks}
              quickAddProjects={quickAddProjects}
              quickAddTasks={quickAddTasks}
              onQuickAddOpen={onQuickAddOpen}
              onQuickAddCancel={onQuickAddCancel}
              onQuickAddTitleChange={onQuickAddTitleChange}
              onQuickAddToggleBrowse={onQuickAddToggleBrowse}
              onQuickAddNavigate={onQuickAddNavigate}
              onQuickAddSelectHere={onQuickAddSelectHere}
              onQuickAddSubmit={onQuickAddSubmit}
            />
          </div>
        </div>
      </div>
    </div>
  );
}, (prev, next) => {
  // Only re-render if column data, cards, or relevant props actually changed
  return prev.column.id === next.column.id
    && prev.cards === next.cards
    && prev.statusColorMap === next.statusColorMap
    && prev.priorityColorMap === next.priorityColorMap
    && prev.userColorMap === next.userColorMap
    && prev.cardRenderer === next.cardRenderer
    && prev.onCardClick === next.onCardClick
    && prev.quickAddColumnId === next.quickAddColumnId
    && prev.quickAddTitle === next.quickAddTitle
    && prev.quickAddCanSubmit === next.quickAddCanSubmit
    && prev.quickAddIsCreating === next.quickAddIsCreating
    && prev.quickAddBrowseOpen === next.quickAddBrowseOpen
    && prev.quickAddCurrentProjectTitle === next.quickAddCurrentProjectTitle
    && prev.quickAddBreadcrumbTasks === next.quickAddBreadcrumbTasks
    && prev.quickAddProjects === next.quickAddProjects
    && prev.quickAddTasks === next.quickAddTasks;
});
