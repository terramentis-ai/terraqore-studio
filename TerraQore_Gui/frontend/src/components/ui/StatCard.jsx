// src/components/ui/StatsCard.jsx
import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const StatsCard = ({ 
  title,
  value,
  subtitle,
  icon: Icon,
  trend = 0,
  trendLabel,
  variant = 'default',
  size = 'md',
  className = '',
  ...props 
}) => {
  const baseStyles = 'border rounded p-4 transition-all duration-200';
  
  const variants = {
    default: 'border-white/10 bg-white/5',
    elevated: 'border-white/20 bg-white/10 shadow-lg',
    success: 'border-green-500/20 bg-green-500/5',
    warning: 'border-yellow-500/20 bg-yellow-500/5',
    danger: 'border-red-500/20 bg-red-500/5',
    info: 'border-blue-500/20 bg-blue-500/5'
  };
  
  const sizes = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6'
  };
  
  const valueSizes = {
    sm: 'text-2xl',
    md: 'text-3xl',
    lg: 'text-4xl'
  };
  
  const getTrendIcon = () => {
    if (trend > 0) {
      return <TrendingUp className="w-4 h-4 text-green-400" />;
    } else if (trend < 0) {
      return <TrendingDown className="w-4 h-4 text-red-400" />;
    }
    return <Minus className="w-4 h-4 text-white/60" />;
  };
  
  const getTrendColor = () => {
    if (trend > 0) return 'text-green-400';
    if (trend < 0) return 'text-red-400';
    return 'text-white/60';
  };
  
  return (
    <div 
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="text-white/60 text-xs font-medium mb-1">
            {title}
          </div>
          <div className={`font-bold ${valueSizes[size]} mb-1`}>
            {value}
          </div>
          {subtitle && (
            <div className="text-white/60 text-sm">
              {subtitle}
            </div>
          )}
        </div>
        
        {Icon && (
          <div className="p-2 bg-white/5 rounded">
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
      
      {(trend !== 0 || trendLabel) && (
        <div className="flex items-center gap-1.5 mt-2">
          {getTrendIcon()}
          <span className={`text-xs ${getTrendColor()}`}>
            {trendLabel || `${trend > 0 ? '+' : ''}${trend}%`}
          </span>
        </div>
      )}
    </div>
  );
};

export default StatsCard;