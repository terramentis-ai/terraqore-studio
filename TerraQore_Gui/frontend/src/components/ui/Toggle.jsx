// src/components/ui/Toggle.jsx
import React from 'react';

const Toggle = React.forwardRef(({
  label,
  description,
  checked,
  onChange,
  disabled = false,
  size = 'md',
  variant = 'default',
  className = '',
  ...props
}, ref) => {
  const sizes = {
    sm: 'w-8 h-4',
    md: 'w-12 h-6',
    lg: 'w-16 h-8'
  };
  
  const toggleSizes = {
    sm: 'w-3 h-3',
    md: 'w-5 h-5',
    lg: 'w-7 h-7'
  };
  
  const variants = {
    default: 'bg-white/20',
    primary: 'bg-blue-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    danger: 'bg-red-500'
  };
  
  const toggleClasses = `
    absolute transition-transform duration-200 ease-in-out
    bg-white rounded-full shadow-lg transform
    ${toggleSizes[size]}
    ${checked ? 'translate-x-full' : 'translate-x-0.5'}
  `;
  
  const containerClasses = `
    relative inline-flex items-center cursor-pointer rounded-full transition-colors duration-200
    ${sizes[size]}
    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
    ${checked ? variants[variant] : 'bg-white/10'}
  `;
  
  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <button
        ref={ref}
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        className={containerClasses}
        onClick={disabled ? undefined : onChange}
        {...props}
      >
        <span className="sr-only">{label}</span>
        <span className={toggleClasses} />
      </button>
      
      {(label || description) && (
        <div className="flex flex-col">
          {label && (
            <span className="text-sm font-medium text-white">
              {label}
            </span>
          )}
          
          {description && (
            <span className="text-xs text-white/60">
              {description}
            </span>
          )}
        </div>
      )}
    </div>
  );
});

Toggle.displayName = 'Toggle';

export default Toggle;