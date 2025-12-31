// src/components/ui/Tabs.jsx
import React from 'react';

const Tabs = ({
  tabs,
  activeTab,
  onChange,
  variant = 'default',
  size = 'md',
  fullWidth = false,
  className = '',
  ...props
}) => {
  const baseStyles = 'flex transition-all duration-200';
  
  const variants = {
    default: 'border-b border-white/10',
    pills: 'gap-1',
    underline: ''
  };
  
  const widthClass = fullWidth ? 'w-full' : '';
  
  return (
    <div className={`${baseStyles} ${variants[variant]} ${widthClass} ${className}`} {...props}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        
        const tabStyles = {
          default: `
            px-4 py-2 border-b-2 transition-colors
            ${isActive
              ? 'border-white text-white'
              : 'border-transparent text-white/60 hover:text-white'
            }
          `,
          pills: `
            px-4 py-2 rounded transition-colors
            ${isActive
              ? 'bg-white text-black'
              : 'bg-white/5 text-white/60 hover:bg-white/10'
            }
          `,
          underline: `
            px-4 py-2 transition-colors relative
            ${isActive
              ? 'text-white after:absolute after:bottom-0 after:left-0 after:w-full after:h-0.5 after:bg-white'
              : 'text-white/60 hover:text-white'
            }
          `
        };
        
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={`${tabStyles[variant]} ${fullWidth ? 'flex-1' : ''}`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
};

export const TabPanel = ({ children, active, className = '', ...props }) => {
  if (!active) return null;
  
  return (
    <div className={`mt-4 ${className}`} {...props}>
      {children}
    </div>
  );
};

Tabs.Panel = TabPanel;

export default Tabs;