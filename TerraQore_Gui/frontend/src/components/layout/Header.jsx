import React from 'react';
import { Cpu, Settings } from 'lucide-react';

const Header = () => {
  return (
    <div className="border-b border-white/10 bg-white/5 backdrop-blur">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-white rounded flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold">TERRAQORE OS</div>
            <div className="text-xs text-white/60">Multi-Agent Engineering Platform</div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-xs text-white/60">v1.0.0</div>
          <button className="p-2 hover:bg-white/10 rounded transition">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Header;