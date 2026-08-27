export interface GridPerson {
  id: string;
  name: string;
  photo_url?: string;
  total_hours: number;
  capacity_hours: number;
  is_overloaded: boolean;
  daily_hours: Record<string, number>;
  daily_capacity_hours: number;
  overloaded_dates: string[];
}

export interface GridSlot {
  id: string;
  task_id: string;
  task_title: string;
  project_title: string;
  company_name?: string;
  assigned_user_id: string;
  start_datetime: string;
  end_datetime: string;
  is_overlapping: boolean;
}

export type DueStatus = 'overdue' | 'this_week';

export interface GridTask {
  id: string;
  title: string;
  project_title: string;
  company_name?: string;
  assignee_name: string;
  is_scheduled: boolean;
  due_date_text?: string;
  due_status?: DueStatus;
}

export interface PlanningGridData {
  days: string[];
  day_labels: string[];
  people: GridPerson[];
  slots: GridSlot[];
  day_start_time: string;
  day_end_time: string;
  lunch_start_time: string;
  lunch_end_time: string;
  step_minutes: number;
  lunch_label: string;
  scheduled_label: string;
  search_placeholder: string;
  no_task_found_label: string;
  tasks_help_text: string;
}

export interface SlotCreateEvent {
  task_id: string;
  person_id: string;
  day: string;
  start_time: string;
}

export interface SlotMoveEvent {
  slot_id: string;
  person_id: string;
  day: string;
  start_time: string;
}

export type ResizeEdge = 'start' | 'end';

export interface SlotResizeEvent {
  slot_id: string;
  edge: ResizeEdge;
  new_time: string;
}

export interface PlanningGridProps {
  gridData: PlanningGridData;
  tasks: GridTask[];
  onSlotCreate?: (event: SlotCreateEvent) => void;
  onSlotMove?: (event: SlotMoveEvent) => void;
  onSlotResize?: (event: SlotResizeEvent) => void;
  onSlotDelete?: (slotId: string) => void;
}

// Prefix used to tell a draggable task-panel item apart from a draggable existing
// slot in dnd-kit's shared id space (both live in the same DndContext).
export const TASK_DRAG_PREFIX = 'task:';
export const SLOT_DRAG_PREFIX = 'slot:';
export const CELL_DROP_PREFIX = 'cell:';

export function taskDragId(taskId: string): string {
  return `${TASK_DRAG_PREFIX}${taskId}`;
}

export function slotDragId(slotId: string): string {
  return `${SLOT_DRAG_PREFIX}${slotId}`;
}

export function cellDropId(personId: string, day: string): string {
  return `${CELL_DROP_PREFIX}${personId}:${day}`;
}

export function parseCellDropId(id: string): { personId: string; day: string } | null {
  if (!id.startsWith(CELL_DROP_PREFIX)) return null;
  const [personId, day] = id.slice(CELL_DROP_PREFIX.length).split(':');
  if (!personId || !day) return null;
  return { personId, day };
}
