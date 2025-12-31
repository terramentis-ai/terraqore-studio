// src/components/ui/Badge.jsx
import React from 'react';
import { 
  Activity, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  Sparkles, 
  GitBranch, 
  Shield, 
  Zap,
  Clock,
  Play,
  Pause,
  LucideIcon
} from 'lucide-react';

const Badge = ({ 
  children, 
  variant = 'default',
  size = 'md',
  icon: Icon,
  className = '',
  ...props 
}) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-full font-medium transition-colors';
  
  const variants = {
    default: 'bg-white/10 text-white border border-white/20',
    primary: 'bg-white text-black border border-white',
    secondary: 'bg-blue-500/20 text-blue-300 border border-blue-500/30',
    success: 'bg-green-500/20 text-green-300 border border-green-500/30',
    warning: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
    danger: 'bg-red-500/20 text-red-300 border border-red-500/30',
    outline: 'bg-transparent text-white border border-white/30'
  };
  
  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-xs',
    lg: 'px-4 py-1.5 text-sm'
  };
  
  return (
    <span 
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {Icon && <Icon className="w-3 h-3 mr-1.5" />}
      {children}
    </span>
  );
};

// Status Badge Component
export const StatusBadge = ({ status, blocked = false, size = 'md' }) => {
  const statusConfig = {
    in_progress: {
      label: 'IN PROGRESS',
      icon: Activity,
      variant: 'secondary'
    },
    completed: {
      label: 'COMPLETED',
      icon: CheckCircle,
      variant: 'success'
    },
    draft: {
      label: 'DRAFT',
      icon: Clock,
      variant: 'outline'
    },
    blocked: {
      label: 'BLOCKED',
      icon: AlertCircle,
      variant: 'danger'
    },
    pending: {
      label: 'PENDING',
      icon: Clock,
      variant: 'warning'
    },
    running: {
      label: 'RUNNING',
      icon: Play,
      variant: 'secondary'
    },
    paused: {
      label: 'PAUSED',
      icon: Pause,
      variant: 'warning'
    },
    error: {
      label: 'ERROR',
      icon: XCircle,
      variant: 'danger'
    }
  };
  
  const config = blocked ? statusConfig.blocked : statusConfig[status] || statusConfig.draft;
  const Icon = config.icon;
  
  return (
    <Badge variant={config.variant} size={size} icon={Icon}>
      {config.label}
    </Badge>
  );
};

// Agent Type Badge Component
export const AgentTypeBadge = ({ type, size = 'md' }) => {
  const typeConfig = {
    generation: {
      label: 'GENERATION',
      icon: Sparkles,
      variant: 'secondary'
    },
    planning: {
      label: 'PLANNING',
      icon: GitBranch,
      variant: 'primary'
    },
    validation: {
      label: 'VALIDATION',
      icon: CheckCircle,
      variant: 'success'
    },
    security: {
      label: 'SECURITY',
      icon: Shield,
      variant: 'danger'
    },
    psmp: {
      label: 'PSMP',
      icon: Zap,
      variant: 'warning'
    },
    analysis: {
      label: 'ANALYSIS',
      icon: Activity,
      variant: 'outline'
    },
    default: {
      label: 'AGENT',
      icon: Sparkles,
      variant: 'default'
    }
  };
  
  const config = typeConfig[type] || typeConfig.default;
  const Icon = config.icon;
  
  return (
    <Badge variant={config.variant} size={size} icon={Icon}>
      {config.label}
    </Badge>
  );
};

export default Badge;
export { StatusBadge, AgentTypeBadge };