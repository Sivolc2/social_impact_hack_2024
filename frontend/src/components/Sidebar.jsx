import React from 'react';

function Sidebar() {
  return (
    <div className="w-80 bg-gray-900/90 backdrop-blur-sm text-white p-4 rounded-lg shadow-lg">
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Data Metrics</h2>
        <select className="w-full bg-gray-800/90 p-2 rounded">
          <option>Desertification</option>
          {/* Add other metrics as needed */}
        </select>
      </div>

      <div className="mb-4">
        <div className="p-3 bg-gray-800/80 rounded">
          <p className="text-sm text-gray-300 mb-1">Desertification indicator value</p>
          <p className="text-xs text-gray-400">Unit: binary</p>
        </div>
      </div>

      <div className="mb-6">
        <div className="flex items-center mb-2">
          <input type="checkbox" className="mr-2" id="landDegradation" />
          <label htmlFor="landDegradation">Show Land Degradation</label>
        </div>
      </div>

      <button className="w-full bg-gray-800/90 p-2 rounded flex items-center justify-center gap-2 hover:bg-gray-700/90 transition-colors">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        <span>Export CSV</span>
      </button>
    </div>
  );
}

export default Sidebar; 