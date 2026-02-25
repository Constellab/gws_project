import React from 'react';

const DEFAULT_COLOR = '#6C63FF';

interface UserAvatarProps {
  name: string;
  profilePictureUrl?: string;
  userColorMap?: Record<string, string>;
  size?: number;
}

export function UserAvatar({ name, profilePictureUrl, userColorMap, size = 24 }: UserAvatarProps) {
  const parts = name.trim().split(/\s+/);
  const firstInitial = (parts[0]?.[0] || '').toUpperCase();
  const lastInitial = (parts[1]?.[0] || '').toUpperCase();
  const initials = firstInitial + lastInitial;

  const bgColor = userColorMap?.[firstInitial] || DEFAULT_COLOR;

  if (profilePictureUrl) {
    return (
      <img
        src={profilePictureUrl}
        alt={name}
        style={{
          width: `${size}px`,
          height: `${size}px`,
          borderRadius: '50%',
          objectFit: 'cover',
          border: '2px solid var(--accent-10)',
          flexShrink: 0,
        }}
      />
    );
  }

  return (
    <div
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: '50%',
        backgroundColor: bgColor,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        fontSize: `${Math.round(size * 0.45)}px`,
        fontWeight: 600,
        color: 'white',
      }}
    >
      {initials}
    </div>
  );
}
