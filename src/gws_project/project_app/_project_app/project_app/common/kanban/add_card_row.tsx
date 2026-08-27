import React from 'react';
import type { QuickAddFolderItem, QuickAddProps } from './kanban_types';

interface AddCardRowProps extends QuickAddProps {
  columnId: string;
}

const rowStyle: React.CSSProperties = {
  padding: '6px 8px',
  fontSize: '12px',
  cursor: 'pointer',
  borderRadius: '6px',
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
};

export function AddCardRow({
  columnId,
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
}: AddCardRowProps) {
  // Drives the focus ring on the title input (no stylesheet available here, so the
  // ":focus" state has to be tracked in React)
  const [titleFocused, setTitleFocused] = React.useState(false);
  const isActive = quickAddColumnId === columnId;

  if (!isActive) {
    return (
      <div
        onClick={() => onQuickAddOpen?.(columnId)}
        style={{
          padding: '8px 10px',
          borderRadius: '8px',
          cursor: 'pointer',
          color: 'var(--gray-9)',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <span style={{ fontSize: '16px', lineHeight: 1 }}>+</span> Add task
      </div>
    );
  }

  const hasProject = !!quickAddCurrentProjectTitle;
  const folderItems: QuickAddFolderItem[] = hasProject ? quickAddTasks || [] : quickAddProjects || [];

  return (
    <div
      style={{
        background: 'var(--card-background)',
        borderRadius: '10px',
        border: '1px solid var(--gray-6)',
        padding: '10px',
      }}
    >
      <label
        style={{
          display: 'block',
          fontSize: '11px',
          fontWeight: 600,
          color: 'var(--gray-11)',
          marginBottom: '4px',
        }}
      >
        Task title
      </label>
      <input
        autoFocus
        value={quickAddTitle || ''}
        onChange={(e) => onQuickAddTitleChange?.(e.target.value)}
        onFocus={() => setTitleFocused(true)}
        onBlur={() => setTitleFocused(false)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && quickAddCanSubmit) onQuickAddSubmit?.();
          if (e.key === 'Escape') onQuickAddCancel?.();
        }}
        placeholder="Write the task title..."
        style={{
          width: '100%',
          boxSizing: 'border-box',
          padding: '7px 9px',
          borderRadius: '6px',
          borderWidth: '1px',
          borderStyle: 'solid',
          borderColor: titleFocused ? 'var(--accent-8)' : 'var(--gray-7)',
          boxShadow: titleFocused
            ? '0 0 0 2px color-mix(in srgb, var(--accent-8) 30%, transparent)'
            : 'none',
          outline: 'none',
          background: 'var(--color-background)',
          color: 'var(--gray-12)',
          fontSize: '13px',
          marginBottom: '8px',
          fontFamily: 'inherit',
        }}
      />
      <div style={{ position: 'relative' }}>
        <button
          onClick={() => onQuickAddToggleBrowse?.()}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            padding: '4px 8px',
            borderRadius: '6px',
            border: '1px solid var(--gray-6)',
            background: 'var(--gray-2)',
            cursor: 'pointer',
            width: '100%',
            textAlign: 'left',
            color: hasProject ? 'var(--gray-12)' : 'var(--gray-9)',
          }}
        >
          <span>📁</span>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {quickAddCurrentProjectTitle || 'Choose project'}
          </span>
        </button>
        {quickAddBrowseOpen && (
          <div
            style={{
              position: 'absolute',
              top: '110%',
              left: 0,
              right: 0,
              zIndex: 20,
              background: 'var(--card-background)',
              border: '1px solid var(--gray-6)',
              borderRadius: '8px',
              boxShadow: '0 4px 12px color-mix(in srgb, var(--gray-12) 15%, transparent)',
              maxHeight: '260px',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Breadcrumb */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '4px',
                fontSize: '11px',
                padding: '8px 10px 6px 10px',
              }}
            >
              <span
                style={{ cursor: 'pointer', color: 'var(--accent-11)' }}
                onClick={() => onQuickAddNavigate?.('projects_root', '')}
              >
                Projects
              </span>
              {hasProject && (
                <>
                  <span style={{ color: 'var(--gray-8)' }}>/</span>
                  <span
                    style={{ cursor: 'pointer', color: 'var(--accent-11)' }}
                    onClick={() => onQuickAddNavigate?.('project_root', '')}
                  >
                    {quickAddCurrentProjectTitle}
                  </span>
                </>
              )}
              {(quickAddBreadcrumbTasks || []).map((task) => (
                <React.Fragment key={task.id}>
                  <span style={{ color: 'var(--gray-8)' }}>/</span>
                  <span
                    style={{ cursor: 'pointer', color: 'var(--accent-11)' }}
                    onClick={() => onQuickAddNavigate?.('breadcrumb_task', task.id)}
                  >
                    {task.title}
                  </span>
                </React.Fragment>
              ))}
            </div>

            {/* Scrollable list of the folders available at the current level */}
            <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '0 6px 6px 6px' }}>
              {folderItems.length === 0 ? (
                <div style={{ padding: '10px 8px', fontSize: '12px', color: 'var(--gray-9)' }}>
                  {hasProject ? 'No subfolders here.' : 'No projects found.'}
                </div>
              ) : (
                folderItems.map((item) => (
                  <div
                    key={item.id}
                    onClick={() =>
                      onQuickAddNavigate?.(hasProject ? 'task' : 'project', item.id)
                    }
                    style={rowStyle}
                  >
                    <span>📁</span>
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.title}
                    </span>
                  </div>
                ))
              )}
            </div>

            {/* Confirm the current level as the destination */}
            {hasProject && (
              <div
                style={{
                  borderTop: '1px solid var(--gray-5)',
                  padding: '8px',
                  display: 'flex',
                  justifyContent: 'flex-end',
                  flexShrink: 0,
                }}
              >
                <button
                  onClick={() => onQuickAddSelectHere?.()}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    fontSize: '12px',
                    fontWeight: 600,
                    padding: '5px 10px',
                    borderRadius: '6px',
                    border: 'none',
                    background: 'var(--accent-9)',
                    color: 'var(--accent-contrast)',
                    cursor: 'pointer',
                  }}
                >
                  <span>✓</span> Select this folder
                </button>
              </div>
            )}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', gap: '6px', marginTop: '8px', justifyContent: 'flex-end' }}>
        <button
          onClick={() => onQuickAddCancel?.()}
          style={{
            fontSize: '12px',
            padding: '4px 10px',
            borderRadius: '6px',
            border: 'none',
            background: 'transparent',
            cursor: 'pointer',
            color: 'var(--gray-9)',
          }}
        >
          Cancel
        </button>
        <button
          disabled={!quickAddCanSubmit || quickAddIsCreating}
          onClick={() => onQuickAddSubmit?.()}
          style={{
            fontSize: '12px',
            padding: '4px 10px',
            borderRadius: '6px',
            border: 'none',
            background: 'var(--accent-9)',
            color: 'var(--accent-contrast)',
            cursor: quickAddCanSubmit ? 'pointer' : 'not-allowed',
            opacity: quickAddCanSubmit ? 1 : 0.5,
          }}
        >
          {quickAddIsCreating ? '...' : 'Add'}
        </button>
      </div>
    </div>
  );
}
