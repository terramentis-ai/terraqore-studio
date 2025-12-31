// src/components/ui/Slider.jsx
import React from 'react';

const Slider = React.forwardRef(({
  label,
  description,
  min = 0,
  max = 100,
  step = 1,
  value,
  onChange,
  showValue = true,
  showMarks = false,
  disabled = false,
  className = '',
  ...props
}, ref) => {
  const [internalValue, setInternalValue] = React.useState(value || min);
  
  const handleChange = (e) => {
    const newValue = parseFloat(e.target.value);
    setInternalValue(newValue);
    if (onChange) onChange(newValue);
  };
  
  const percentage = ((internalValue - min) / (max - min)) * 100;
  
  const marks = showMarks ? Array.from(
    { length: Math.floor((max - min) / step) + 1 },
    (_, i) => min + i * step
  ) : [];
  
  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between">
        {label && (
          <label className="text-sm font-medium text-white">
            {label}
          </label>
        )}
        
        {showValue && (
          <span className="text-sm text-white/60">
            {internalValue.toFixed(step < 1 ? 1 : 0)}
          </span>
        )}
      </div>
      
      {description && (
        <p className="text-xs text-white/60">
          {description}
        </p>
      )}
      
      <div className="relative pt-2">
        <input
          ref={ref}
          type="range"
          min={min}
          max={max}
          step={step}
          value={internalValue}
          onChange={handleChange}
          disabled={disabled}
          className={`
            w-full h-1.5 appearance-none rounded-full
            bg-gradient-to-r from-white/20 via-white/20 to-white/20
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:h-4
            [&::-webkit-slider-thumb]:w-4
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:bg-white
            [&::-webkit-slider-thumb]:border-2
            [&::-webkit-slider-thumb]:border-white/20
            [&::-webkit-slider-thumb]:shadow-lg
            [&::-webkit-slider-thumb]:cursor-pointer
            [&::-webkit-slider-thumb]:transition-transform
            [&::-webkit-slider-thumb]:hover:scale-110
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          style={{
            background: `linear-gradient(to right, white ${percentage}%, transparent ${percentage}%)`
          }}
          {...props}
        />
        
        {showMarks && marks.length > 0 && (
          <div className="flex justify-between px-1 mt-1">
            {marks.map((mark) => (
              <div
                key={mark}
                className="flex flex-col items-center"
                style={{ left: `${((mark - min) / (max - min)) * 100}%` }}
              >
                <div className="w-px h-1.5 bg-white/30" />
                <span className="text-xs text-white/60 mt-1">{mark}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
});

Slider.displayName = 'Slider';

export default Slider;