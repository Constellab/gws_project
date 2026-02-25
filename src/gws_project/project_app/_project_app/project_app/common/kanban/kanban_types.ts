export interface Card {
  id: string;
  title: string;
  description?: string;
  priority?: 'LOW' | 'MEDIUM' | 'HIGH';
  assignee?: string;
  assignee_profile_picture_url?: string;
  parent_task_title?: string;
  is_leaf?: boolean;
  project_name?: string;
  start_date?: string;
  end_date?: string;
}

export interface Column {
  id: string;
  title: string;
  cards: Card[];
}

export interface BoardData {
  columns: Column[];
}

export interface CardMoveEvent {
  card_id: string;
  from_column_id: string;
  to_column_id: string;
}

export interface SortableCardProps {
  id: string;
  card: Card;
  onCardClick?: (cardId: string) => void;
  customRenderer?: (card: Card) => React.ReactNode;
  priorityColorMap?: Record<string, string>;
  userColorMap?: Record<string, string>;
  columnColorPrefix?: string;
}

export interface ColumnProps {
  column: Column;
  cards: Card[];
  cardRenderer?: (card: Card) => React.ReactNode;
  onCardClick?: (cardId: string) => void;
  statusColorMap?: Record<string, string>;
  priorityColorMap?: Record<string, string>;
  userColorMap?: Record<string, string>;
}

export interface KanbanBoardProps {
  boardData: BoardData;
  onCardMove?: (event: CardMoveEvent) => void;
  onCardClick?: (cardId: string) => void;
  disableColumnDrag?: boolean;
  superTest?: any;
  cardRenderer?: (card: Card) => React.ReactNode;
  statusColorMap?: Record<string, string>;
  priorityColorMap?: Record<string, string>;
  userColorMap?: Record<string, string>;
}
