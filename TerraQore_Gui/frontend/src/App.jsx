// src/App.js
import React, { useState } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import DashboardPanel from './components/panels/DashboardPanel';
import AgentsHubPanel from './components/panels/AgentsHubPanel';
import SettingsPanel from './components/panels/SettingsPanel';

const App = () => {
  const [activePanel, setActivePanel] = useState('dashboard');

  const renderPanel = () => {
    switch (activePanel) {
      case 'dashboard':
        return <DashboardPanel />;
      case 'agents':
        return <AgentsHubPanel />;
      case 'settings':
        return <SettingsPanel />;
      default:
        return <DashboardPanel />;
    }
  };

  return (
    <div className="min-h-screen bg-black text-white font-mono">
      <Header />
      
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-12 gap-6">
          <Sidebar activePanel={activePanel} setActivePanel={setActivePanel} />
          
          <div className="col-span-9">
            {renderPanel()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;