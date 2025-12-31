// src/components/ui/ProgressBar.jsx
import React from 'react';

const ProgressBar = ({ 
  value = 0,
  max = 100,
  label,
  showLabel = true,
  showPercentage = true,
  size = 'md',
  variant = 'default',
  animate = false,
  striped = false,
  className = '',
  ...props 
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  
  const heights = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
    xl: 'h-4'
  };
  
  const variants = {
    default: 'bg-white',
    primary: 'bg-blue-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    danger: 'bg-red-500',
    gradient: 'bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500'
  };
  
  const animationClass = animate ? 'animate-pulse' : '';
  const stripeClass = striped ? 'progress-bar-striped' : '';
  
  return (
    <div className={`space-y-2 ${className}`} {...props}>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between">
          {label && (
            <span className="text-sm font-medium text-white">
              {label}
            </span>
          )}
          
          {showPercentage && (
            <span className="text-sm text-white/60">
              {value.toFixed(1)}/{max} ({percentage.toFixed(0)}%)
            </span>
          )}
        </div>
      )}
      
      <div className={`w-full bg-white/10 rounded overflow-hidden ${heights[size]}`}>
        <div
          className={`
            h-full rounded transition-all duration-500 ease-out
            ${variants[variant]}
            ${animationClass}
            ${stripeClass}
          `}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;