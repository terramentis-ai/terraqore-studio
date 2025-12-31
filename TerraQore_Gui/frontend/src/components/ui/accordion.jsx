// src/components/ui/Accordion.jsx
import React, { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

const Accordion = ({
  items,
  multiple = false,
  defaultOpen = [],
  variant = 'default',
  className = '',
  ...props
}) => {
  const [openItems, setOpenItems] = useState(defaultOpen);
  
  const toggleItem = (id) => {
    if (multiple) {
      setOpenItems(prev =>
        prev.includes(id)
          ? prev.filter(itemId => itemId !== id)
          : [...prev, id]
      );
    } else {
      setOpenItems(prev => prev.includes(id) ? [] : [id]);
    }
  };
  
  const variants = {
    default: 'border border-white/10 divide-y divide-white/10',
    ghost: 'space-y-2',
    bordered: 'space-y-2'
  };
  
  const itemVariants = {
    default: '',
    ghost: 'border border-white/10 rounded',
    bordered: 'border-b border-white/10 last:border-0'
  };
  
  return (
    <div className={`${variants[variant]} ${className}`} {...props}>
      {items.map((item) => {
        const isOpen = openItems.includes(item.id);
        
        return (
          <div key={item.id} className={itemVariants[variant]}>
            <button
              type="button"
              onClick={() => toggleItem(item.id)}
              className={`
                w-full flex items-center justify-between
                px-4 py-3 text-left transition-colors
                ${variant === 'ghost' ? 'hover:bg-white/5 rounded' : ''}
              `}
            >
              <div className="flex items-center gap-3">
                {item.icon && (
                  <item.icon className="w-4 h-4 text-white/60" />
                )}
                <span className="font-medium text-white">
                  {item.title}
                </span>
              </div>
              
              {isOpen ? (
                <ChevronDown className="w-4 h-4 text-white/60 transition-transform" />
              ) : (
                <ChevronRight className="w-4 h-4 text-white/60 transition-transform" />
              )}
            </button>
            
            {isOpen && (
              <div className="px-4 py-3">
                <div className="text-white/80">
                  {item.content}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default Accordion;