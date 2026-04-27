import React from 'react';
import './ui.css';

/**
 * Material You (MD3) Card Component
 * 
 * Variants:
 * - elevated: Card with shadow (default)
 * - filled: Solid color background without border/shadow
 * - outlined: Border with surface background
 */
export const Card = ({
  children,
  variant = 'elevated',
  interactive = false,
  className = '',
  onClick,
  ...props
}) => {
  const baseClass = 'md-card';
  const variantClass = `md-card--${variant}`;
  const interactiveClass = interactive || onClick ? 'md-card--interactive state-layer' : '';

  return (
    <div 
      className={`${baseClass} ${variantClass} ${interactiveClass} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  );
};
