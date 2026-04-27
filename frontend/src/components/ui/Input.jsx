import React, { forwardRef } from 'react';
import './ui.css';

/**
 * Material You (MD3) Input Component
 * Implements the filled text field style
 */
export const Input = forwardRef(({
  label,
  id,
  error,
  supportingText,
  iconLeft,
  iconRight,
  className = '',
  wrapperClassName = '',
  ...props
}, ref) => {
  const generatedId = id || `input-${Math.random().toString(36).substring(2, 9)}`;
  const hasError = !!error;
  
  return (
    <div className={`md-input-container ${className}`}>
      {label && (
        <label htmlFor={generatedId} className="md-input-label">
          {label}
        </label>
      )}
      
      <div className={`md-input-wrapper ${hasError ? 'md-input-wrapper--error' : ''} ${wrapperClassName}`}>
        {iconLeft && <div className="md-input-icon md-input-icon--left">{iconLeft}</div>}
        
        <input
          ref={ref}
          id={generatedId}
          className="md-input"
          {...props}
        />
        
        {iconRight && <div className="md-input-icon md-input-icon--right">{iconRight}</div>}
      </div>
      
      {(error || supportingText) && (
        <div className={`md-input-supporting-text ${hasError ? 'md-input-supporting-text--error' : ''}`}>
          {error || supportingText}
        </div>
      )}
    </div>
  );
});

Input.displayName = 'Input';
