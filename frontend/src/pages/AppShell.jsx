import { useState, useEffect } from 'react';
import { styles } from '../utils/styles';
import { useAuth } from '../contexts/AuthContext';
import { PlannerPage } from './PlannerPage';
import { TemplateManager } from '../components/templates/TemplateManager';
import { FixedBlockManager } from '../components/templates/FixedBlockManager';
import { OnboardingFlow } from '../components/onboarding/OnboardingFlow';
import { PlannerSelection } from '../components/onboarding/PlannerSelection';
import { userApi } from '../api/userApi';

export const AppShell = () => {
  const { user, logout } = useAuth();
  const [appView, setAppView] = useState('planner');
  const [message, setMessage] = useState('');
  const [profile, setProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(true);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const data = await userApi.fetchUserProfile();
        setProfile(data);
      } catch (err) {
        console.error('Failed to load user profile', err);
      } finally {
        setLoadingProfile(false);
      }
    };
    if (user) {
      loadProfile();
    }
  }, [user]);

  if (!user || loadingProfile) return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading...</div>;

  if (profile && !profile.onboarding_completed) {
    return <OnboardingFlow onComplete={() => setProfile({ ...profile, onboarding_completed: true })} />;
  }

  if (profile && profile.onboarding_completed && !profile.active_planner_id) {
    return <PlannerSelection profile={profile} onComplete={(id) => setProfile({ ...profile, active_planner_id: id })} />;
  }

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
        <PlannerPage setMessage={setMessage} profile={profile} setAppView={setAppView} />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <TemplateManager setMessage={setMessage} profile={profile} setProfile={setProfile} setAppView={setAppView} />
          <FixedBlockManager setMessage={setMessage} />
        </div>
      )}
    </main>
  );
};
