/** How a row's edge marker (liseré) and due text should be coloured. */
export type MyDayDueStatus = 'overdue' | 'after_due';

export interface MyDayItem {
  slot_id: string;
  task_id: string;
  task_title: string;
  parent_task_title?: string | null;
  project_title: string;
  /** Pre-formatted, e.g. "09:00 - 11:00". */
  time_range: string;
  /** Pre-formatted and already translated, e.g. "Due Mar 4". */
  due_date_text?: string | null;
  due_status?: MyDayDueStatus | null;
  /** Set only when the task belongs to somebody else, e.g. "Thomas's task". */
  assignee_note?: string | null;
}

export interface MyDayListProps {
  items: MyDayItem[];
  /** Emitted after a drag, with the slot ids in their new order. */
  onReorder?: (event: { ordered_slot_ids: string[] }) => void;
  onItemClick?: (taskId: string) => void;
  /** Pre-translated, shown on the drag handle. */
  reorderLabel?: string;
}

export interface MyDayItemRowProps {
  item: MyDayItem;
  onItemClick?: (taskId: string) => void;
  reorderLabel?: string;
}
