# Create Layout.jsx in the layout folder
cat > src/components/layout/Layout.jsx << 'EOF'
import React from 'react';
import Header from './Header';
import Sidebar from './Sidebar';

const Layout = ({ children, activePanel, setActivePanel }) => {
  return (
    <div className="min-h-screen bg-black text-white font-mono">
      <Header />
      
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-12 gap-6">
          <Sidebar activePanel={activePanel} setActivePanel={setActivePanel} />
          
          <div className="col-span-9">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Layout;
EOF