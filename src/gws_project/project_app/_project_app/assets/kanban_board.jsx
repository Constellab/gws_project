import React, { useState } from 'react';
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
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

// Sortable Card Component
function SortableCard({ id, card, onCardClick }) {
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
    cursor: 'grab',
    boxShadow: isDragging ? '0 4px 8px rgba(0,0,0,0.2)' : '0 1px 3px rgba(0,0,0,0.1)',
  };

  const priorityColors = {
    LOW: '#4caf50',
    MEDIUM: '#ff9800',
    HIGH: '#f44336',
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600' }}>{card.title}</h4>
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
      {card.description && (
        <p style={{ margin: '4px 0', fontSize: '12px', color: '#666' }}>
          {card.description}
        </p>
      )}
      {card.assignee && (
        <div style={{ marginTop: '8px', fontSize: '11px', color: '#888' }}>
          👤 {card.assignee}
        </div>
      )}
    </div>
  );
}

// Column Component
function Column({ column, cards }) {
  const cardIds = cards.map((card) => card.id);

  return (
    <div
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
            <SortableCard key={card.id} id={card.id} card={card} />
          ))}
        </div>
      </SortableContext>
    </div>
  );
}

// Main Kanban Board Component
export function KanbanBoard({ boardData, onCardMove, disableColumnDrag = true }) {
  console.log('[KanbanBoard] Component initialized with:', {
    boardData,
    hasOnCardMove: !!onCardMove,
    onCardMoveType: typeof onCardMove,
    disableColumnDrag
  });

  const [activeId, setActiveId] = useState(null);
  const [columns, setColumns] = useState(boardData?.columns || []);

  // Update columns when boardData changes
  React.useEffect(() => {
    console.log('[KanbanBoard] boardData changed:', boardData);
    if (boardData?.columns) {
      setColumns(boardData.columns);
      console.log('[KanbanBoard] Columns updated:', boardData.columns);
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
  const findContainer = (id) => {
    for (const column of columns) {
      if (column.cards.some((card) => card.id === id)) {
        return column.id;
      }
    }
    return null;
  };

  const handleDragStart = (event) => {
    console.log('[KanbanBoard] Drag started:', {
      activeId: event.active.id,
      activeData: event.active.data
    });
    setActiveId(event.active.id);
  };

  const handleDragOver = (event) => {
    const { active, over } = event;

    if (!over) {
      console.log('[KanbanBoard] Drag over - no over target');
      return;
    }

    const activeContainer = findContainer(active.id);
    const overContainer = findContainer(over.id) || over.id;

    console.log('[KanbanBoard] Drag over:', {
      activeId: active.id,
      overId: over.id,
      activeContainer,
      overContainer
    });

    if (!activeContainer || !overContainer) {
      console.log('[KanbanBoard] Missing container - skipping');
      return;
    }

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

  const handleDragEnd = (event) => {
    const { active, over } = event;

    console.log('[KanbanBoard] ===== DRAG ENDED =====');
    console.log('[KanbanBoard] Drag ended event:', {
      activeId: active.id,
      overId: over?.id,
      hasOver: !!over
    });

    if (!over) {
      console.log('[KanbanBoard] No drop target - cancelling drag');
      setActiveId(null);
      return;
    }

    const activeContainer = findContainer(active.id);
    const overContainer = findContainer(over.id) || over.id;

    console.log('[KanbanBoard] Containers:', {
      activeContainer,
      overContainer,
      sameContainer: activeContainer === overContainer
    });

    if (!activeContainer || !overContainer) {
      console.log('[KanbanBoard] Missing container - cancelling');
      setActiveId(null);
      return;
    }

    const activeColumn = columns.find((col) => col.id === activeContainer);
    const overColumn = columns.find((col) => col.id === overContainer);

    if (!activeColumn || !overColumn) {
      setActiveId(null);
      return;
    }

    const activeCardIndex = activeColumn.cards.findIndex((card) => card.id === active.id);
    const overCardIndex = overColumn.cards.findIndex((card) => card.id === over.id);

    if (activeCardIndex === -1) {
      setActiveId(null);
      return;
    }

    if (activeContainer === overContainer) {
      // Reorder within the same column - update local state only
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
      // Moved to a different column - trigger the callback
      const card = activeColumn.cards[activeCardIndex];

      if (onCardMove) {
        // Call the event handler with the required data
        console.log('Triggering onCardMove event', {
          card,
          from: activeContainer,
          to: overContainer,
          onCardMove: typeof onCardMove
        });

        // Reflex event handlers are functions that send data to the backend
        // They expect to be called with the event data object
        try {
          const eventPayload = {
            new_board: { columns },
            card: card,
            source: { fromColumnId: activeContainer },
            destination: { toColumnId: overContainer }
          };
          console.log('Calling onCardMove with:', eventPayload);
          onCardMove(eventPayload);
        } catch (error) {
          console.error('Error calling onCardMove:', error);
        }
      } else {
        console.warn('onCardMove handler is not defined');
      }
    }

    setActiveId(null);
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
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div style={{ display: 'flex', padding: '20px', overflowX: 'auto', width: '100%' }}>
        {columns.map((column) => (
          <Column
            key={column.id}
            column={column}
            cards={column.cards}
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
  );
}
