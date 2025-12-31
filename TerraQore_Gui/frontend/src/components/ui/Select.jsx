// src/components/ui/Select.jsx
import React from 'react';
import { ChevronDown } from 'lucide-react';

const Select = React.forwardRef(({
  label,
  description,
  error,
  options = [],
  placeholder = 'Select an option',
  size = 'md',
  variant = 'default',
  fullWidth = true,
  className = '',
  ...props
}, ref) => {
  const baseStyles = 'bg-black border rounded appearance-none transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black focus:ring-white/50';
  
  const variants = {
    default: 'border-white/20 text-white',
    error: 'border-red-500/50 text-white',
    success: 'border-green-500/50 text-white',
    warning: 'border-yellow-500/50 text-white'
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm pr-8',
    md: 'px-4 py-2.5 text-sm pr-10',
    lg: 'px-4 py-3 text-base pr-10'
  };
  
  const widthClass = fullWidth ? 'w-full' : '';
  
  return (
    <div className={`space-y-1.5 ${widthClass}`}>
      {label && (
        <label className="block text-sm font-medium text-white">
          {label}
        </label>
      )}
      
      {description && (
        <p className="text-xs text-white/60">
          {description}
        </p>
      )}
      
      <div className="relative">
        <select
          ref={ref}
          className={`
            ${baseStyles}
            ${variants[error ? 'error' : variant]}
            ${sizes[size]}
            ${widthClass}
            ${className}
          `}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          
          {options.map((option) => (
            <option 
              key={option.value || option} 
              value={option.value || option}
            >
              {option.label || option}
            </option>
          ))}
        </select>
        
        <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/60 pointer-events-none" />
      </div>
      
      {error && (
        <p className="text-xs text-red-400">{error}</p>
      )}
    </div>
  );
});

Select.displayName = 'Select';

export default Select;