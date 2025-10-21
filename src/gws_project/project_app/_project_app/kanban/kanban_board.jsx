import React, { useState } from 'react';
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
            <SortableCard key={card.id} id={card.id} card={card} />
          ))}
        </div>
      </SortableContext>
    </div>
  );
}

// Main Kanban Board Component
export function KanbanBoard({ boardData, onCardMove, disableColumnDrag = true }) {
  const [activeId, setActiveId] = useState(null);
  const [columns, setColumns] = useState(boardData?.columns || []);
  const [originalContainer, setOriginalContainer] = useState(null);

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
  const findContainer = (id) => {
    for (const column of columns) {
      if (column.cards.some((card) => card.id === id)) {
        return column.id;
      }
    }
    return null;
  };

  const handleDragStart = (event) => {
    setActiveId(event.active.id);
    // Store the original container before any drag operations
    const container = findContainer(event.active.id);
    setOriginalContainer(container);
    console.log('Drag started - original container:', container);
  };

  const handleDragOver = (event) => {
    const { active, over } = event;

    if (!over) return;

    const activeContainer = findContainer(active.id);
    const overContainer = findContainer(over.id) || over.id;

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

  const handleDragEnd = (event) => {
    const { active, over } = event;

    console.log('=== DRAG END START ===');
    console.log('Event:', event);
    console.log('Active ID:', active?.id);
    console.log('Over ID:', over?.id);
    console.log('Current columns state:', columns);

    if (!over) {
      console.log('No over target - drag cancelled');
      setActiveId(null);
      setOriginalContainer(null);
      return;
    }

    // Use the original container stored at drag start instead of finding it
    // (because handleDragOver may have already moved the card)
    const activeContainer = originalContainer;
    const overContainer = findContainer(over.id) || over.id;

    console.log('Active container (from drag start):', activeContainer);
    console.log('Over container:', overContainer);

    if (!activeContainer || !overContainer) {
      console.log('Missing container - activeContainer:', activeContainer, 'overContainer:', overContainer);
      setActiveId(null);
      setOriginalContainer(null);
      return;
    }

    const activeColumn = columns.find((col) => col.id === activeContainer);
    const overColumn = columns.find((col) => col.id === overContainer);

    console.log('Active column:', activeColumn);
    console.log('Over column:', overColumn);

    if (!activeColumn || !overColumn) {
      console.log('Column not found - activeColumn:', activeColumn, 'overColumn:', overColumn);
      setActiveId(null);
      setOriginalContainer(null);
      return;
    }

    if (activeContainer === overContainer) {
      console.log('Same container - reordering within column');
      // Reorder within the same column - update local state only
      const activeCardIndex = activeColumn.cards.findIndex((card) => card.id === active.id);
      const overCardIndex = overColumn.cards.findIndex((card) => card.id === over.id);

      console.log('Active card index:', activeCardIndex);
      console.log('Over card index:', overCardIndex);

      if (activeCardIndex === -1) {
        console.log('Active card not found in column');
        setActiveId(null);
        setOriginalContainer(null);
        return;
      }

      if (activeCardIndex !== overCardIndex) {
        console.log('Reordering from index', activeCardIndex, 'to', overCardIndex);
        setColumns((prevColumns) => {
          const newColumns = prevColumns.map(col => ({
            ...col,
            cards: [...col.cards]
          }));
          const column = newColumns.find((col) => col.id === activeContainer);
          if (column) {
            column.cards = arrayMove(column.cards, activeCardIndex, overCardIndex);
          }
          console.log('New columns after reorder:', newColumns);
          return newColumns;
        });
      } else {
        console.log('Same position - no reorder needed');
      }
    } else {
      console.log('Different container - moving card between columns');
      // Moved to a different column - find the card (it's already been moved by handleDragOver)
      // So we need to find it across all columns, not just the original column
      const card = columns.flatMap(col => col.cards).find(c => c.id === active.id);
      console.log('Card being moved:', card);

      if (!card) {
        console.error('Card not found in any column!');
        setActiveId(null);
        setOriginalContainer(null);
        return;
      }

      if (onCardMove) {
        // Call the event handler with the required data
        console.log('onCardMove handler available, type:', typeof onCardMove);
        console.log('Moving card from', activeContainer, 'to', overContainer);

        // Reflex event handlers are functions that send data to the backend
        // They expect to be called with the event data object
        try {
          const eventPayload = {
            card_id: card.id,
            from_column_id: activeContainer,
            to_column_id: overContainer,
          };
          console.log('Event payload:', JSON.stringify(eventPayload, null, 2));
          console.log('Calling onCardMove...');
          onCardMove(eventPayload);
          console.log('onCardMove called successfully');
        } catch (error) {
          console.error('Error calling onCardMove:', error);
          console.error('Error stack:', error.stack);
        }
      } else {
        console.warn('onCardMove handler is not defined');
      }
    }

    console.log('Setting activeId to null');
    setActiveId(null);
    setOriginalContainer(null);
    console.log('=== DRAG END COMPLETE ===');
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
