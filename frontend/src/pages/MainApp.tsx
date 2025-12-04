import React, { useState } from 'react';
import Dashboard from './Dashboard';
import PublicHauntDirectory from '../components/public/PublicHauntDirectory';
import UserPreferences from '../components/settings/UserPreferences';
import './MainApp.css';

type View = 'dashboard' | 'directory' | 'settings';

const MainApp: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  return (
    <div className="main-app">
      <nav className="app-nav">
        <div className="app-nav-brand">
          <h1>Watcher</h1>
        </div>
        <div className="app-nav-links">
          <button
            className={`nav-link ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            My Haunts
          </button>
          <button
            className={`nav-link ${currentView === 'directory' ? 'active' : ''}`}
            onClick={() => setCurrentView('directory')}
          >
            Public Directory
          </button>
          <button
            className={`nav-link ${currentView === 'settings' ? 'active' : ''}`}
            onClick={() => setCurrentView('settings')}
          >
            Settings
          </button>
        </div>
      </nav>

      <div className="app-content">
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'directory' && <PublicHauntDirectory />}
        {currentView === 'settings' && <UserPreferences />}
      </div>
    </div>
  );
};

export default MainApp;
