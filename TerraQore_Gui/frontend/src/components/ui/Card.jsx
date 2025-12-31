// src/components/ui/Card.jsx
import React from 'react';

const Card = ({ 
  children, 
  variant = 'default',
  hoverable = false,
  className = '',
  ...props 
}) => {
  const baseStyles = 'rounded transition-all duration-200';
  
  const variants = {
    default: 'border border-white/10 bg-white/5',
    elevated: 'border border-white/10 bg-white/10 shadow-lg',
    ghost: 'border border-white/5 bg-transparent',
    warning: 'border border-yellow-500/20 bg-yellow-500/5',
    danger: 'border border-red-500/20 bg-red-500/5',
    success: 'border border-green-500/20 bg-green-500/5',
    info: 'border border-blue-500/20 bg-blue-500/5'
  };
  
  const hoverStyles = hoverable ? 'hover:bg-white/10 hover:border-white/20 hover:shadow-lg' : '';
  
  return (
    <div 
      className={`${baseStyles} ${variants[variant]} ${hoverStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

const CardHeader = ({ children, className = '', ...props }) => (
  <div className={`px-6 py-4 border-b border-white/10 ${className}`} {...props}>
    {children}
  </div>
);

const CardTitle = ({ children, className = '', ...props }) => (
  <h3 className={`text-lg font-medium ${className}`} {...props}>
    {children}
  </h3>
);

const CardDescription = ({ children, className = '', ...props }) => (
  <p className={`text-sm text-white/60 ${className}`} {...props}>
    {children}
  </p>
);

const CardContent = ({ children, className = '', ...props }) => (
  <div className={`px-6 py-4 ${className}`} {...props}>
    {children}
  </div>
);

const CardFooter = ({ children, className = '', ...props }) => (
  <div className={`px-6 py-4 border-t border-white/10 ${className}`} {...props}>
    {children}
  </div>
);

Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Description = CardDescription;
Card.Content = CardContent;
Card.Footer = CardFooter;

export default Card;