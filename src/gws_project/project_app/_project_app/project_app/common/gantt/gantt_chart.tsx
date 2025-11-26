import React, { useState, useMemo } from 'react';
import { Gantt, Task, ViewMode } from 'gantt-task-react';
import 'gantt-task-react/dist/index.css';

const LINE_HEIGHT = 50;

// Type definitions
interface GanttTaskData {
  id: string;
  name: string;
  start: string;
  end: string;
  progress: number;
  type: 'task' | 'project';
  project?: string;
  dependencies?: string[];
  styles?: {
    backgroundColor?: string;
    progressColor?: string;
    progressSelectedColor?: string;
  };
  display_order: number;
  hide_children?: boolean;
}

interface GanttData {
  tasks: GanttTaskData[];
}

interface GanttChartProps {
  data: GanttData;
  viewMode?: 'Day' | 'Week' | 'Month' | 'Year';
  onTaskClick?: (taskId: string) => void;
}

// Convert our data format to gantt-task-react format
function convertToGanttTask(task: GanttTaskData): Task {
  return {
    id: task.id,
    name: task.name,
    start: new Date(task.start),
    end: new Date(task.end),
    progress: task.progress,
    type: task.type,
    project: task.project,
    dependencies: task.dependencies,
    styles: task.styles,
    displayOrder: task.display_order,
    isDisabled: false,
    hideChildren: task.hide_children || false,
  };
}

// Convert view mode string to ViewMode enum
function getViewMode(mode: string): ViewMode {
  switch (mode) {
    case 'Day':
      return ViewMode.Day;
    case 'Week':
      return ViewMode.Week;
    case 'Month':
      return ViewMode.Month;
    case 'Year':
      return ViewMode.Year;
    default:
      return ViewMode.Month;
  }
}

// Tooltip component for task hover
function TaskTooltip({ task }: { task: Task }) {
  return (
    <div style={{
      backgroundColor: 'white',
      padding: '12px',
      borderRadius: '6px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      minWidth: '200px',
    }}>
      <div style={{ fontWeight: '600', marginBottom: '8px', fontSize: '14px' }}>
        {task.name}
      </div>
      <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
        <strong>Start:</strong> {task.start.toLocaleDateString()}
      </div>
      <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
        <strong>End:</strong> {task.end.toLocaleDateString()}
      </div>
      <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
        <strong>Progress:</strong> {task.progress}%
      </div>
      <div style={{
        marginTop: '8px',
        width: '100%',
        height: '6px',
        backgroundColor: '#e0e0e0',
        borderRadius: '3px',
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${task.progress}%`,
          height: '100%',
          backgroundColor: task.styles?.progressColor || '#1976d2',
          transition: 'width 0.3s ease'
        }} />
      </div>
    </div>
  );
}

// Custom task list header component
function TaskListHeader({ headerHeight }: { headerHeight: number }) {
  return (
    <div style={{ display: 'flex', height: headerHeight, width: '360px' }}>
      <div style={{ width: '200px', padding: '8px', fontWeight: 600 }}>Project</div>
      <div style={{ width: '80px', padding: '8px', fontWeight: 600 }}>From</div>
      <div style={{ width: '80px', padding: '8px', fontWeight: 600 }}>To</div>
    </div>
  );
}

// Custom task list table component
function TaskListTable({ 
  tasks, 
  onExpanderClick 
}: { 
  tasks: Task[];
  locale: string;
  onExpanderClick: (task: Task) => void;
}) {
  return (
    <div>
      {tasks.map((task) => {
        // Skip the dummy view extender task
        if (task.id === '__view_extender__') {
          return null;
        }
        
        // Calculate left padding for child tasks
        const isChildTask = task.type === 'task' && task.project;
        const leftPadding = isChildTask ? '32px' : '8px';
        
        return (
          <div key={task.id} style={{ display: 'flex', height: `${LINE_HEIGHT}px`, borderBottom: '1px solid #e0e0e0', width: '360px' }}>
            <div style={{ width: '200px', padding: `8px 8px 8px ${leftPadding}`, display: 'flex', alignItems: 'center', boxSizing: 'border-box' }}>
              {task.type === 'project' && (
                <button
                  onClick={() => onExpanderClick(task)}
                  style={{
                    marginRight: '8px',
                    border: 'none',
                    background: 'none',
                    cursor: 'pointer',
                    fontSize: '16px',
                    flexShrink: 0
                  }}
                >
                  {task.hideChildren ? '▶' : '▼'}
                </button>
              )}
              <span style={{
                fontSize: task.type === 'project' ? '13px' : '14px',
                wordWrap: 'break-word',
                overflowWrap: 'break-word',
                whiteSpace: 'normal',
                lineHeight: '1.3',
                flex: 1
              }}>
                {task.name}
              </span>
            </div>
            <div style={{ width: '80px', padding: '8px', display: 'flex', alignItems: 'center', fontSize: '13px', boxSizing: 'border-box' }}>
              {task.start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </div>
            <div style={{ width: '80px', padding: '8px', display: 'flex', alignItems: 'center', fontSize: '13px', boxSizing: 'border-box' }}>
              {task.end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
export function GanttChart({ data, viewMode = 'Month', onTaskClick }: GanttChartProps) {
  const [view, setView] = useState<ViewMode>(getViewMode(viewMode));
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());

  // Convert tasks to gantt-task-react format with collapse logic
  const tasks = useMemo(() => {
    if (!data || !data.tasks || data.tasks.length === 0) {
      return [];
    }

    // Filter tasks based on expanded state
    const filteredTasks = data.tasks.filter(task => {
      // Always show projects
      if (task.type === 'project') {
        return true;
      }
      // Show tasks only if their parent project is expanded
      if (task.project) {
        return expandedProjects.has(task.project);
      }
      return true;
    });

    const convertedTasks = filteredTasks.map(task => {
      const convertedTask = convertToGanttTask(task);
      // Set hideChildren based on whether the project is expanded
      if (task.type === 'project') {
        convertedTask.hideChildren = !expandedProjects.has(task.id);
      }
      return convertedTask;
    });

    // Ensure at least 1 year view range for better visualization
    if (convertedTasks.length > 0) {
      const dates = convertedTasks.flatMap(t => [t.start, t.end]);
      const minDate = new Date(Math.min(...dates.map(d => d.getTime())));
      const maxDate = new Date(Math.max(...dates.map(d => d.getTime())));
      
      // Calculate the span in months
      const monthsDiff = (maxDate.getFullYear() - minDate.getFullYear()) * 12 + 
                        (maxDate.getMonth() - minDate.getMonth());
      
      // If the span is less than 12 months, extend the end date
      if (monthsDiff < 12) {
        const extendedEndDate = new Date(minDate);
        extendedEndDate.setFullYear(minDate.getFullYear() + 1);
        
        // Get the maximum display order
        const maxDisplayOrder = Math.max(...convertedTasks.map(t => t.displayOrder || 0));
        
        // Add a dummy invisible task to extend the view (always last)
        convertedTasks.push({
          id: '__view_extender__',
          name: '',
          start: minDate,
          end: extendedEndDate,
          progress: 0,
          type: 'task',
          displayOrder: maxDisplayOrder + 1,
          isDisabled: true,
          hideChildren: false,
          styles: { backgroundColor: 'transparent', progressColor: 'transparent' }
        });
      }
    }

    return convertedTasks;
  }, [data, expandedProjects]);

  // Update view when viewMode prop changes
  React.useEffect(() => {
    setView(getViewMode(viewMode));
  }, [viewMode]);

  // Initialize expanded projects to empty set (all collapsed by default)
  React.useEffect(() => {
    if (data && data.tasks) {
      setExpandedProjects(new Set());
    }
  }, [data]);

  // Handle expander click (arrow icon on projects)
  const handleExpanderClick = (task: Task) => {
    setExpandedProjects(prev => {
      const newSet = new Set(prev);
      if (newSet.has(task.id)) {
        newSet.delete(task.id);
      } else {
        newSet.add(task.id);
      }
      return newSet;
    });
  };

  // Handle task click
  const handleTaskClick = (task: Task) => {
    // For tasks, call the provided click handler
    if (onTaskClick) {
      onTaskClick(task.id);
    }
  };

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Gantt Chart */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #e0e0e0',
        overflow: 'auto',
        flex: 1,
        minHeight: 0,
        height: '100%'
      }}>
        <Gantt
          tasks={tasks}
          viewMode={view}
          onClick={handleTaskClick}
          onExpanderClick={handleExpanderClick}
          columnWidth={view === ViewMode.Month ? 65 : undefined}
          listCellWidth="360px"
          ganttHeight={tasks.length * LINE_HEIGHT}
          barBackgroundColor="#f5f5f5"
          barBackgroundSelectedColor="#e0e0e0"
          arrowColor="#999"
          todayColor="#7c84813d"
          TooltipContent={TaskTooltip}
          TaskListHeader={TaskListHeader}
          TaskListTable={TaskListTable}
        />
      </div>
    </div>
  );
}
