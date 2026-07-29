import React, { useState } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { UserAvatar } from './user_avatar';
import { PriorityIcon } from './priority_icon';
import { formatDate } from './kanban_utils';
import type { Card, SortableCardProps } from './kanban_types';

export const SortableCard = React.memo(function SortableCard({ id, card, onCardClick, customRenderer, priorityColorMap, userColorMap, columnColorPrefix = 'gray' }: SortableCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: id, animateLayoutChanges: () => false });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition: transition ? `${transition}, border-color 0.15s ease, box-shadow 0.15s ease` : 'all 0.15s ease',
    opacity: isDragging ? 0.5 : 1,
    backgroundColor: '#fff',
    padding: '16px 18px',
    borderRadius: '12px',
    overflow: 'hidden',
    border: isHovered ? `1px solid var(--${columnColorPrefix}-8)` : `1px solid var(--${columnColorPrefix}-6)`,
    cursor: onCardClick ? 'pointer' : 'grab',
    boxShadow: isDragging
      ? '0 8px 16px rgba(0,0,0,0.15)'
      : isHovered
        ? '0 2px 8px rgba(0,0,0,0.08)'
        : '0 1px 3px rgba(0,0,0,0.04)',
  };

  const handleClick = (e: React.MouseEvent) => {
    if (!isDragging && onCardClick) {
      e.stopPropagation();
      onCardClick(card.id);
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {customRenderer ? (
        customRenderer(card)
      ) : (
        <>
          {/* Title + Priority */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px', marginBottom: '10px' }}>
            <h4 style={{ margin: 0, minWidth: 0, overflowWrap: 'break-word', fontSize: '14px', fontWeight: '600', lineHeight: '1.3em', color: 'var(--gray-12)' }}>{card.title}</h4>
            {card.priority && (() => {
              const pColorPrefix = priorityColorMap?.[card.priority] || 'gray';
              return (
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '3px',
                    backgroundColor: `var(--${pColorPrefix}-3)`,
                    color: `var(--${pColorPrefix}-11)`,
                    padding: '3px 8px',
                    borderRadius: '99px',
                    fontSize: '10px',
                    fontWeight: '600',
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                  }}
                >
                  <PriorityIcon priority={card.priority} />
                  {card.priority}
                </div>
              );
            })()}
          </div>
          {/* Project tag */}
          {card.project_name && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginBottom: '8px',
            }}>
              <div style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                background: 'var(--accent-9)',
                flexShrink: 0,
              }} />
              <span style={{
                fontSize: '12px',
                color: 'var(--accent-11)',
                fontWeight: 500,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}>{card.project_name}</span>
            </div>
          )}
          {/* Parent task folder */}
          {card.parent_task_title && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginBottom: '8px',
            }}>
              <span style={{ fontSize: '12px' }}>📁</span>
              <span style={{
                fontSize: '12px',
                color: 'var(--gray-9)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}>{card.parent_task_title}</span>
            </div>
          )}
          {/* Description */}
          {card.description && (
            <p style={{
              margin: '0 0 4px 0',
              fontSize: '12px',
              color: 'var(--gray-9)',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              lineHeight: '1.4',
            }}>
              {card.description}
            </p>
          )}
          {/* Footer with separator */}
          {(card.assignee || card.start_date || card.end_date) && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginTop: '12px',
              paddingTop: '10px',
              borderTop: '1px solid var(--gray-4)',
            }}>
              {(card.start_date || card.end_date) ? (
                <span style={{
                  fontSize: '11px',
                  color: 'var(--gray-9)',
                  fontWeight: 500,
                }}>
                  {card.start_date && formatDate(card.start_date)}
                  {card.start_date && card.end_date && ' → '}
                  {card.end_date && formatDate(card.end_date)}
                </span>
              ) : <span />}
              {card.assignee && (
                <UserAvatar
                  name={card.assignee}
                  profilePictureUrl={card.assignee_profile_picture_url}
                  userColorMap={userColorMap}
                  size={26}
                />
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}, (prev, next) => {
  return prev.id === next.id
    && prev.card === next.card
    && prev.columnColorPrefix === next.columnColorPrefix
    && prev.priorityColorMap === next.priorityColorMap
    && prev.userColorMap === next.userColorMap
    && prev.onCardClick === next.onCardClick
    && prev.customRenderer === next.customRenderer;
});
