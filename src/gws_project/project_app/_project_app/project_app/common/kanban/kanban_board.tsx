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
  useDroppable,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

// Type definitions
interface Card {
  id: string;
  title: string;
  description?: string;
  priority?: 'LOW' | 'MEDIUM' | 'HIGH';
  assignee?: string;
  parent_task_title?: string;
  is_leaf?: boolean;
  project_name?: string;
}

interface Column {
  id: string;
  title: string;
  cards: Card[];
}

interface BoardData {
  columns: Column[];
}

interface CardMoveEvent {
  card_id: string;
  from_column_id: string;
  to_column_id: string;
}

interface SortableCardProps {
  id: string;
  card: Card;
  onCardClick?: (cardId: string) => void;
  customRenderer?: (card: Card) => React.ReactNode;
}

interface ColumnProps {
  column: Column;
  cards: Card[];
  cardRenderer?: (card: Card) => React.ReactNode;
  onCardClick?: (cardId: string) => void;
}

interface KanbanBoardProps {
  boardData: BoardData;
  onCardMove?: (event: CardMoveEvent) => void;
  onCardClick?: (cardId: string) => void;
  disableColumnDrag?: boolean;
  superTest?: any;
  cardRenderer?: (card: Card) => React.ReactNode;
}

// Sortable Card Component
function SortableCard({ id, card, onCardClick, customRenderer }: SortableCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    backgroundColor: 'white',
    padding: '12px',
    marginBottom: '8px',
    borderRadius: '8px',
    border: '1px solid #e0e0e0',
    cursor: onCardClick ? 'pointer' : 'grab',
    boxShadow: isDragging ? '0 4px 8px rgba(0,0,0,0.2)' : '0 1px 3px rgba(0,0,0,0.1)'
  };

  const handleClick = (e: React.MouseEvent) => {
    // Only trigger click if not dragging
    if (!isDragging && onCardClick) {
      e.stopPropagation();
      onCardClick(card.id);
    }
  };

  const priorityColors: Record<'LOW' | 'MEDIUM' | 'HIGH', string> = {
    LOW: '#4caf50',
    MEDIUM: '#ff9800',
    HIGH: '#f44336',
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} onClick={handleClick}>
      {customRenderer ? (
        customRenderer(card)
      ) : (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '14px' }}>
                {card.is_leaf ? '📄' : '📁'}
              </span>
              <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600', lineHeight: '1.1em' }}>{card.title}</h4>
            </div>
            {card.priority && (
              <span
                style={{
                  fontSize: '10px',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  backgroundColor: priorityColors[card.priority] || '#999',
                  color: 'white',
                  fontWeight: 'bold',
                }}
              >
                {card.priority}
              </span>
            )}
          </div>
          {card.project_name && (
            <div style={{ marginBottom: '8px', fontSize: '11px', color: '#888', fontWeight: '500' }}>
              📦 {card.project_name}
            </div>
          )}
          {card.parent_task_title && (
            <div style={{ marginBottom: '8px', fontSize: '11px', color: '#666' }}>
              📁 {card.parent_task_title}
            </div>
          )}
          {card.description && (
            <p style={{
              margin: '4px 0',
              fontSize: '12px',
              color: '#666',
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              lineHeight: '1.4'
            }}>
              {card.description}
            </p>
          )}
          {card.assignee && (
            <div style={{ marginTop: '8px', fontSize: '11px', color: '#888' }}>
              👤 {card.assignee}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// Column Component
function Column({ column, cards, cardRenderer, onCardClick }: ColumnProps) {
  const cardIds = cards.map((card) => card.id);
  const { setNodeRef } = useDroppable({
    id: column.id,
  });

  return (
    <div
      ref={setNodeRef}
      style={{
        flex: 1,
        minWidth: '280px',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        padding: '16px',
        marginRight: '16px',
      }}
    >
      <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#333' }}>
        {column.title} ({cards.length})
      </h3>
      <SortableContext items={cardIds} strategy={verticalListSortingStrategy}>
        <div style={{ minHeight: '100px' }}>
          {cards.map((card) => (
            <SortableCard
              key={card.id}
              id={card.id}
              card={card}
              customRenderer={cardRenderer}
              onCardClick={onCardClick}
            />
          ))}
        </div>
      </SortableContext>
    </div>
  );
}

// Main Kanban Board Component
export function KanbanBoard({ boardData, superTest, cardRenderer, onCardMove, onCardClick, disableColumnDrag = true }: KanbanBoardProps) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [columns, setColumns] = useState<Column[]>(boardData?.columns || []);
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
    // Store the original container before any drag operations
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

    // Visual feedback during drag - update local state
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
      // Reorder within the same column - update local state only
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
      // Moved to a different column - find the card (it's already been moved by handleDragOver)
      // So we need to find it across all columns, not just the original column
      const card = columns.flatMap(col => col.cards).find(c => c.id === active.id);

      if (!card) {
        setActiveId(null);
        setOriginalContainer(null);
        return;
      }

      if (onCardMove) {
        // Call the event handler with the required data
        // Reflex event handlers are functions that send data to the backend
        // They expect to be called with the event data object
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
    <div className="kanban-board-container" style={{ width: '100%', flex: 1, minHeight: 0, overflowY: 'auto' }}>
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
        <div style={{ display: 'flex', overflowX: 'auto', width: '100%', minHeight: '100%' }}>
          {columns.map((column) => (
            <Column
              key={column.id}
              column={column}
              cards={column.cards}
              cardRenderer={cardRenderer}
              onCardClick={onCardClick}
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
