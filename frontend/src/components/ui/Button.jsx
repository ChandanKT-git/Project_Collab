import React from 'react';
import './ui.css';

/**
 * Material You (MD3) Button Component
 * 
 * Variants:
 * - filled: High emphasis (default)
 * - tonal: Medium emphasis
 * - outlined: Medium-low emphasis
 * - text: Low emphasis
 * - elevated: High emphasis with shadow
 */
export const Button = ({
  children,
  variant = 'filled',
  color = 'primary',
  size = 'medium',
  icon,
  iconPosition = 'left',
  disabled = false,
  className = '',
  onClick,
  type = 'button',
  ...props
}) => {
  const baseClass = 'md-button';
  const variantClass = `md-button--${variant}`;
  const colorClass = `md-button--${color}`;
  const sizeClass = `md-button--${size}`;
  const iconClass = icon ? `md-button--with-icon md-button--icon-${iconPosition}` : '';
  const disabledClass = disabled ? 'md-button--disabled' : '';

  return (
    <button
      type={type}
      className={`${baseClass} ${variantClass} ${colorClass} ${sizeClass} ${iconClass} ${disabledClass} state-layer ${className}`}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {icon && iconPosition === 'left' && <span className="md-button__icon">{icon}</span>}
      <span className="md-button__label">{children}</span>
      {icon && iconPosition === 'right' && <span className="md-button__icon">{icon}</span>}
    </button>
  );
};
