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

// A "folder" entry (project or task-with-subtasks) in the quick-add destination browser
export interface QuickAddFolderItem {
  id: string;
  title: string;
}

// Props shared by both KanbanBoard and Column for the inline "quick add task" row
export interface QuickAddProps {
  quickAddColumnId?: string;
  quickAddTitle?: string;
  quickAddCanSubmit?: boolean;
  quickAddIsCreating?: boolean;
  quickAddBrowseOpen?: boolean;
  quickAddCurrentProjectTitle?: string;
  quickAddBreadcrumbTasks?: QuickAddFolderItem[];
  quickAddProjects?: QuickAddFolderItem[];
  quickAddTasks?: QuickAddFolderItem[];
  onQuickAddOpen?: (columnId: string) => void;
  onQuickAddCancel?: () => void;
  onQuickAddTitleChange?: (value: string) => void;
  onQuickAddToggleBrowse?: () => void;
  onQuickAddNavigate?: (kind: string, targetId: string) => void;
  onQuickAddSelectHere?: () => void;
  onQuickAddSubmit?: () => void;
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

export interface ColumnProps extends QuickAddProps {
  column: Column;
  cards: Card[];
  cardRenderer?: (card: Card) => React.ReactNode;
  onCardClick?: (cardId: string) => void;
  statusColorMap?: Record<string, string>;
  priorityColorMap?: Record<string, string>;
  userColorMap?: Record<string, string>;
}

export interface KanbanBoardProps extends QuickAddProps {
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
