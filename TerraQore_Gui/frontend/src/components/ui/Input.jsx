// src/components/ui/Input.jsx
import React from 'react';
import { Search, Eye, EyeOff } from 'lucide-react';

const Input = React.forwardRef(({
  label,
  description,
  error,
  icon: Icon,
  type = 'text',
  variant = 'default',
  size = 'md',
  fullWidth = true,
  className = '',
  ...props
}, ref) => {
  const [showPassword, setShowPassword] = React.useState(false);
  
  const baseStyles = 'bg-black border rounded transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black focus:ring-white/50';
  
  const variants = {
    default: 'border-white/20 text-white placeholder:text-white/40',
    error: 'border-red-500/50 text-white placeholder:text-white/40',
    success: 'border-green-500/50 text-white placeholder:text-white/40',
    warning: 'border-yellow-500/50 text-white placeholder:text-white/40'
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2.5 text-sm',
    lg: 'px-4 py-3 text-base'
  };
  
  const inputType = type === 'password' && showPassword ? 'text' : type;
  
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
        {Icon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/60">
            <Icon className="w-4 h-4" />
          </div>
        )}
        
        <input
          ref={ref}
          type={inputType}
          className={`
            ${baseStyles}
            ${variants[error ? 'error' : variant]}
            ${sizes[size]}
            ${Icon ? 'pl-10' : ''}
            ${type === 'password' ? 'pr-10' : ''}
            ${widthClass}
            ${className}
          `}
          {...props}
        />
        
        {type === 'password' && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/60 hover:text-white"
          >
            {showPassword ? (
              <EyeOff className="w-4 h-4" />
            ) : (
              <Eye className="w-4 h-4" />
            )}
          </button>
        )}
      </div>
      
      {error && (
        <p className="text-xs text-red-400">{error}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

// Search Input Component
export const SearchInput = React.forwardRef(({
  placeholder = 'Search...',
  size = 'md',
  className = '',
  ...props
}, ref) => {
  const sizes = {
    sm: 'px-3 py-1.5 pl-9 text-sm',
    md: 'px-4 py-2.5 pl-10 text-sm',
    lg: 'px-4 py-3 pl-10 text-base'
  };
  
  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/60" />
      <input
        ref={ref}
        type="search"
        placeholder={placeholder}
        className={`
          w-full bg-black border border-white/20 rounded text-white placeholder:text-white/40
          transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 
          focus:ring-offset-black focus:ring-white/50
          ${sizes[size]}
          ${className}
        `}
        {...props}
      />
    </div>
  );
});

SearchInput.displayName = 'SearchInput';

export default Input;