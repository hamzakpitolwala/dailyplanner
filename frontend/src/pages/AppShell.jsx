import { useState } from 'react';
import { styles } from '../utils/styles';
import { useAuth } from '../contexts/AuthContext';
import { PlannerPage } from './PlannerPage';
import { TemplateManager } from '../components/templates/TemplateManager';

export const AppShell = () => {
  const { user, logout } = useAuth();
  const [appView, setAppView] = useState('planner');
  const [message, setMessage] = useState('');

  if (!user) return <p>Loading user profile...</p>;

  return (
    <main style={styles.appShell}>
      <header style={styles.header}>
        <div style={styles.header}>
          <h1 style={styles.heading}>DailyPlanner</h1>
          <div>
            <button 
              style={styles.button} 
              onClick={() => setAppView(appView === 'planner' ? 'templates' : 'planner')}
            >
              {appView === 'planner' ? 'Manage Templates' : 'Back to Planner'}
            </button>
            <button
              style={{ ...styles.button, marginLeft: '0.5rem' }}
              onClick={logout}
            >
              Sign out ({user.email})
            </button>
          </div>
        </div>
      </header>

      {message && (
        <div style={{ padding: '0.75rem', background: '#d1e7dd', color: '#0f5132', borderRadius: 4, marginBottom: '1rem' }}>
          {message}
        </div>
      )}

      {appView === 'planner' ? (
        <PlannerPage setMessage={setMessage} />
      ) : (
        <TemplateManager setMessage={setMessage} />
      )}
    </main>
  );
};
