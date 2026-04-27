import React from 'react';
import './ui.css';

/**
 * Material You (MD3) Badge/Chip Component
 */
export const Badge = ({
  children,
  variant = 'assist', // assist, filter, input, suggestion, status-*
  icon,
  className = '',
  onClick,
  ...props
}) => {
  const baseClass = 'md-chip';
  const variantClass = `md-chip--${variant}`;
  const interactiveClass = onClick ? 'state-layer' : '';

  return (
    <div 
      className={`${baseClass} ${variantClass} ${interactiveClass} ${className}`}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
      {...props}
    >
      {icon && <span className="md-chip__icon flex-center">{icon}</span>}
      <span className="md-chip__label">{children}</span>
    </div>
  );
};
