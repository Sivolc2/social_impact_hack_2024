import React from 'react';
import Map from './components/Map';
import Sidebar from './components/Sidebar';
import ChatPanel from './components/ChatPanel';

function App() {
  return (
    <div className="flex h-screen bg-black relative">
      {/* Left Sidebar - Floating */}
      <div className="absolute top-4 left-4 z-10">
        <Sidebar />
      </div>
      
      {/* Main Map Area - Full Screen */}
      <div className="w-full h-full">
        <Map />
      </div>
      
      {/* Right Chat Panel - Floating */}
      <div className="absolute top-4 right-4 z-10">
        <ChatPanel />
      </div>
    </div>
  );
}

export default App; 