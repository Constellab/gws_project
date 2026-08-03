import React, { useState, useRef, useMemo } from 'react';
import type {
  CollisionDetection,
  DragStartEvent,
  DragOverEvent,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  DndContext,
  DragOverlay,
  pointerWithin,
  rectIntersection,
  getFirstCollision,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  MeasuringStrategy,
} from '@dnd-kit/core';
import {
  arrayMove,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable';
import { Column } from './kanban_column';
import type { Card, Column as ColumnType, KanbanBoardProps } from './kanban_types';

export function KanbanBoard({
  boardData,
  superTest,
  cardRenderer,
  onCardMove,
  onCardClick,
  disableColumnDrag = true,
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
}: KanbanBoardProps) {
  const [columns, setColumns] = useState<ColumnType[]>(boardData?.columns || []);
  const [activeId, setActiveId] = useState<string | null>(null);
  // Lightweight state: just the target column id during a cross-column drag
  const [overColumnId, setOverColumnId] = useState<string | null>(null);
  const originalContainerRef = useRef<string | null>(null);
  const activeCardRef = useRef<Card | null>(null);

  // Only measure droppables before dragging starts — not on every re-render during drag
  const measuringConfig = useMemo(() => ({
    droppable: {
      strategy: MeasuringStrategy.BeforeDragging,
    },
  }), []);

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
  const findContainer = (id: string, cols: ColumnType[]): string | null => {
    for (const column of cols) {
      if (column.cards.some((card) => card.id === id)) {
        return column.id;
      }
    }
    return null;
  };

  // Custom collision detection: closestCorners alone fails to register a drop in
  // the empty space below the last card of a column (its corners are far from a
  // small nearby card's corners, which often "wins" the comparison even though the
  // pointer is well past it). pointerWithin checks the actual pointer coordinate
  // against droppable rects first, which reliably covers that empty area since the
  // column's own droppable spans its full height. Falls back to rectIntersection,
  // then narrows a container-level match down to its closest card so in-column
  // reordering stays precise. This mirrors dnd-kit's own multi-container example.
  const collisionDetectionStrategy: CollisionDetection = (args) => {
    const pointerIntersections = pointerWithin(args);
    const intersections = pointerIntersections.length > 0 ? pointerIntersections : rectIntersection(args);
    let overId = getFirstCollision(intersections, 'id');

    if (overId == null) {
      return [];
    }

    const overColumn = columns.find((col) => col.id === overId);
    if (overColumn && overColumn.cards.length > 0) {
      const closestCard = closestCenter({
        ...args,
        droppableContainers: args.droppableContainers.filter((container) =>
          overColumn.cards.some((card) => card.id === container.id)
        ),
      });
      if (closestCard.length > 0) {
        overId = closestCard[0].id;
      }
    }

    return [{ id: overId }];
  };

  // Derive displayed columns: if dragging across columns, move the card virtually
  const displayedColumns = useMemo(() => {
    if (!activeId || !overColumnId || !originalContainerRef.current) return columns;

    const sourceColId = findContainer(activeId, columns);
    if (!sourceColId || sourceColId === overColumnId) return columns;

    const sourceCol = columns.find(c => c.id === sourceColId);
    const targetCol = columns.find(c => c.id === overColumnId);
    if (!sourceCol || !targetCol) return columns;

    const card = sourceCol.cards.find(c => c.id === activeId);
    if (!card) return columns;

    return columns.map(col => {
      if (col.id === sourceColId) {
        return { ...col, cards: col.cards.filter(c => c.id !== activeId) };
      }
      if (col.id === overColumnId) {
        return { ...col, cards: [...col.cards, card] };
      }
      return col;
    });
  }, [columns, activeId, overColumnId]);

  const handleDragStart = (event: DragStartEvent) => {
    const id = event.active.id as string;
    setActiveId(id);
    originalContainerRef.current = findContainer(id, columns);
    activeCardRef.current = columns.flatMap(col => col.cards).find(c => c.id === id) || null;
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) {
      setOverColumnId(prev => prev === null ? prev : null);
      return;
    }

    // Determine which column the pointer is over
    const overContainer = findContainer(over.id as string, displayedColumns) || (over.id as string);
    const activeContainer = originalContainerRef.current;

    if (!activeContainer || !overContainer) return;

    // Only update if the target column actually changed
    if (activeContainer !== overContainer) {
      setOverColumnId(prev => prev === overContainer ? prev : overContainer);
    } else {
      setOverColumnId(prev => prev === null ? prev : null);
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    const activeContainer = originalContainerRef.current;
    const targetColumn = overColumnId;

    // Reset drag state
    setActiveId(null);
    setOverColumnId(null);
    originalContainerRef.current = null;
    activeCardRef.current = null;

    if (!over || !activeContainer) return;

    const overContainer = targetColumn || findContainer(over.id as string, columns) || (over.id as string);

    if (!overContainer) return;

    if (activeContainer === overContainer) {
      // Same column reorder
      const activeColumn = columns.find((col) => col.id === activeContainer);
      if (!activeColumn) return;

      const activeCardIndex = activeColumn.cards.findIndex((card) => card.id === active.id);
      const overCardIndex = activeColumn.cards.findIndex((card) => card.id === over.id);

      if (activeCardIndex !== -1 && overCardIndex !== -1 && activeCardIndex !== overCardIndex) {
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
      // Cross-column move: optimistically commit the move to columns state
      // so the card stays in the target column until boardData arrives
      const cardId = active.id as string;
      setColumns((prevColumns) => {
        const sourceCol = prevColumns.find(col => col.id === activeContainer);
        if (!sourceCol) return prevColumns;

        const card = sourceCol.cards.find(c => c.id === cardId);
        if (!card) return prevColumns;

        return prevColumns.map(col => {
          if (col.id === activeContainer) {
            return { ...col, cards: col.cards.filter(c => c.id !== cardId) };
          }
          if (col.id === overContainer) {
            return { ...col, cards: [...col.cards, card] };
          }
          return col;
        });
      });

      if (onCardMove) {
        onCardMove({
          card_id: cardId,
          from_column_id: activeContainer,
          to_column_id: overContainer,
        });
      }
    }
  };

  const activeCard = activeCardRef.current;

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
        collisionDetection={collisionDetectionStrategy}
        measuring={measuringConfig}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div style={{ display: 'flex', overflowX: 'auto', width: '100%', flex: 1, minHeight: 0 }}>
          {displayedColumns.map((column) => (
            <Column
              key={column.id}
              column={column}
              cards={column.cards}
              cardRenderer={cardRenderer}
              onCardClick={onCardClick}
              statusColorMap={statusColorMap}
              priorityColorMap={priorityColorMap}
              userColorMap={userColorMap}
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
