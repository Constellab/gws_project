import React, { useState } from 'react';
import type {
  DragStartEvent,
  DragOverEvent,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable';
import { Column } from './kanban_column';
import type { Column as ColumnType, KanbanBoardProps } from './kanban_types';

export function KanbanBoard({ boardData, superTest, cardRenderer, onCardMove, onCardClick, disableColumnDrag = true, statusColorMap, priorityColorMap, userColorMap }: KanbanBoardProps) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [columns, setColumns] = useState<ColumnType[]>(boardData?.columns || []);
  const [originalContainer, setOriginalContainer] = useState<string | null>(null);

  // Update columns when boardData changes
  React.useEffect(() => {
    if (boardData?.columns) {
      setColumns(boardData.columns);
    }
  }, [boardData]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Find which column a card belongs to
  const findContainer = (id: string): string | null => {
    for (const column of columns) {
      if (column.cards.some((card) => card.id === id)) {
        return column.id;
      }
    }
    return null;
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
    const container = findContainer(event.active.id as string);
    setOriginalContainer(container);
    console.log('Drag started - original container:', container);
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;

    if (!over) return;

    const activeContainer = findContainer(active.id as string);
    const overContainer = findContainer(over.id as string) || (over.id as string);

    if (!activeContainer || !overContainer) return;

    if (activeContainer !== overContainer) {
      setColumns((prevColumns) => {
        const newColumns = prevColumns.map(col => ({
          ...col,
          cards: [...col.cards]
        }));

        const activeColumn = newColumns.find((col) => col.id === activeContainer);
        const overColumn = newColumns.find((col) => col.id === overContainer);

        if (!activeColumn || !overColumn) return prevColumns;

        const activeCardIndex = activeColumn.cards.findIndex((card) => card.id === active.id);
        const overCardIndex = overColumn.cards.findIndex((card) => card.id === over.id);

        if (activeCardIndex === -1) return prevColumns;

        const [activeCard] = activeColumn.cards.splice(activeCardIndex, 1);

        if (overCardIndex >= 0) {
          overColumn.cards.splice(overCardIndex, 0, activeCard);
        } else {
          overColumn.cards.push(activeCard);
        }

        return newColumns;
      });
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over) {
      setActiveId(null);
      setOriginalContainer(null);
      return;
    }

    // Use the original container stored at drag start instead of finding it
    // (because handleDragOver may have already moved the card)
    const activeContainer = originalContainer;
    const overContainer = findContainer(over.id as string) || (over.id as string);

    if (!activeContainer || !overContainer) {
      setActiveId(null);
      setOriginalContainer(null);
      return;
    }

    const activeColumn = columns.find((col) => col.id === activeContainer);
    const overColumn = columns.find((col) => col.id === overContainer);

    if (!activeColumn || !overColumn) {
      setActiveId(null);
      setOriginalContainer(null);
      return;
    }

    if (activeContainer === overContainer) {
      const activeCardIndex = activeColumn.cards.findIndex((card) => card.id === active.id);
      const overCardIndex = overColumn.cards.findIndex((card) => card.id === over.id);

      if (activeCardIndex === -1) {
        setActiveId(null);
        setOriginalContainer(null);
        return;
      }

      if (activeCardIndex !== overCardIndex) {
        setColumns((prevColumns) => {
          const newColumns = prevColumns.map(col => ({
            ...col,
            cards: [...col.cards]
          }));
          const column = newColumns.find((col) => col.id === activeContainer);
          if (column) {
            column.cards = arrayMove(column.cards, activeCardIndex, overCardIndex);
          }
          return newColumns;
        });
      }
    } else {
      const card = columns.flatMap(col => col.cards).find(c => c.id === active.id);

      if (!card) {
        setActiveId(null);
        setOriginalContainer(null);
        return;
      }

      if (onCardMove) {
        const eventPayload = {
          card_id: card.id,
          from_column_id: activeContainer,
          to_column_id: overContainer,
        };
        onCardMove(eventPayload);
      }
    }

    setActiveId(null);
    setOriginalContainer(null);
  };

  const activeCard = activeId
    ? columns
        .flatMap((col) => col.cards)
        .find((card) => card.id === activeId)
    : null;

  if (!boardData || !boardData.columns) {
    return <div style={{ padding: '20px' }}>No data available</div>;
  }

  return (
    <div className="kanban-board-container" style={{ width: '100%', flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      {/* Test component display area */}
      {superTest && (
        <div style={{
          padding: '20px',
          marginBottom: '20px',
          backgroundColor: '#f0f4f8',
          borderRadius: '8px',
          border: '2px solid #3b82f6',
        }}>
          <h3 style={{ margin: '0 0 12px 0', color: '#1e40af', fontSize: '14px', fontWeight: '600' }}>
            Test Component:
          </h3>
          <div>
            {superTest}
          </div>
        </div>
      )}

      {/* Kanban Board */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div style={{ display: 'flex', overflowX: 'auto', width: '100%', flex: 1, minHeight: 0 }}>
          {columns.map((column) => (
            <Column
              key={column.id}
              column={column}
              cards={column.cards}
              cardRenderer={cardRenderer}
              onCardClick={onCardClick}
              statusColorMap={statusColorMap}
              priorityColorMap={priorityColorMap}
              userColorMap={userColorMap}
            />
          ))}
        </div>
        <DragOverlay>
          {activeCard ? (
            <div
              style={{
                backgroundColor: 'white',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid #e0e0e0',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                cursor: 'grabbing',
              }}
            >
              <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600' }}>{activeCard.title}</h4>
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}
