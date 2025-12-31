// src/components/ui/Button.jsx
import React from 'react';
import { Loader2 } from 'lucide-react';

const Button = ({ 
  children, 
  variant = 'primary',
  size = 'md',
  icon: Icon,
  iconPosition = 'left',
  loading = false,
  disabled = false,
  fullWidth = false,
  className = '',
  ...props 
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 rounded focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black';
  
  const variants = {
    primary: 'bg-white text-black hover:bg-white/90 border border-white active:scale-95',
    secondary: 'border border-white/20 bg-white/5 text-white hover:bg-white/10 active:scale-95',
    ghost: 'bg-transparent text-white hover:bg-white/5 active:scale-95',
    danger: 'bg-red-500 text-white hover:bg-red-600 active:scale-95 border border-red-500',
    success: 'bg-green-500 text-white hover:bg-green-600 active:scale-95 border border-green-500',
    warning: 'bg-yellow-500 text-black hover:bg-yellow-600 active:scale-95 border border-yellow-500',
    outline: 'border-2 border-white text-white bg-transparent hover:bg-white/10 active:scale-95'
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2.5 text-sm',
    lg: 'px-6 py-3 text-base',
    xl: 'px-8 py-4 text-lg'
  };
  
  const disabledStyles = 'opacity-50 cursor-not-allowed';
  const widthStyles = fullWidth ? 'w-full' : '';
  
  const classes = [
    baseStyles,
    variants[variant],
    sizes[size],
    disabled ? disabledStyles : '',
    widthStyles,
    className
  ].filter(Boolean).join(' ');
  
  return (
    <button 
      className={classes} 
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <Loader2 className={`w-4 h-4 animate-spin ${iconPosition === 'left' ? 'mr-2' : 'ml-2'}`} />
      )}
      
      {!loading && Icon && iconPosition === 'left' && (
        <Icon className="w-4 h-4 mr-2" />
      )}
      
      {children}
      
      {!loading && Icon && iconPosition === 'right' && (
        <Icon className="w-4 h-4 ml-2" />
      )}
    </button>
  );
};

export const IconButton = ({ 
  icon: Icon,
  size = 'md',
  variant = 'ghost',
  className = '',
  ...props 
}) => {
  const sizes = {
    sm: 'p-1.5',
    md: 'p-2',
    lg: 'p-3',
    xl: 'p-4'
  };
  
  const variants = {
    primary: 'bg-white text-black hover:bg-white/90',
    secondary: 'bg-white/5 text-white hover:bg-white/10',
    ghost: 'bg-transparent text-white hover:bg-white/5',
    danger: 'bg-red-500 text-white hover:bg-red-600',
    outline: 'border border-white/20 text-white hover:bg-white/5'
  };
  
  return (
    <button
      className={`
        rounded transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black
        ${sizes[size]}
        ${variants[variant]}
        ${className}
      `}
      {...props}
    >
      <Icon className="w-4 h-4" />
    </button>
  );
};

export default Button;