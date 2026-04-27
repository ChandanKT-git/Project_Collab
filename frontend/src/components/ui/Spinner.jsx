import React from 'react';
import './ui.css';

export const Spinner = ({
  size = 'medium', // small, medium, large
  variant = 'primary', // primary, light
  className = ''
}) => {
  return (
    <div 
      className={`md-spinner md-spinner--${size} md-spinner--${variant} ${className}`}
      role="status"
      aria-label="Loading"
    />
  );
};
