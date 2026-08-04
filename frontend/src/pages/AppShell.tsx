import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { PlannerPage } from './PlannerPage';
import { DashboardPage } from './DashboardPage.tsx';
import { TemplateManager } from '../components/templates/TemplateManager';
import { FixedBlockManager } from '../components/templates/FixedBlockManager';
import { OnboardingFlow } from '../components/onboarding/OnboardingFlow';
import { PlannerSelection } from '../components/onboarding/PlannerSelection';
import { userApi } from '../api/userApi';
import { MainLayout } from '../components/Layout/MainLayout';

export const AppShell = () => {
  const { user } = useAuth();
  
  // View states: 'planner', 'dashboard', 'templates'
  const [appView, setAppView] = useState<string>('planner');
  const [message, setMessage] = useState('');
  const [profile, setProfile] = useState<any>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);

  // Active top navigation tab (templates view is an overlay state)
  const [activeView, setActiveView] = useState<'planner' | 'dashboard'>('planner');

  useEffect(() => {
    // Sync appView and activeView when navigating
    if (appView === 'planner' || appView === 'dashboard') {
      setActiveView(appView);
    }
  }, [appView]);

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

  if (!user || loadingProfile) return <div className="p-8 text-center text-zinc-500">Loading workspace...</div>;

  if (profile && !profile.onboarding_completed) {
    return <OnboardingFlow onComplete={() => setProfile({ ...profile, onboarding_completed: true })} />;
  }

  if (profile && profile.onboarding_completed && !profile.active_planner_id) {
    return <PlannerSelection profile={profile} onComplete={(id: string) => setProfile({ ...profile, active_planner_id: id })} />;
  }

  return (
    <MainLayout 
      activeView={activeView} 
      setActiveView={(v) => {
        setActiveView(v);
        setAppView(v);
      }}
      profile={profile}
      setProfile={setProfile}
      setAppView={setAppView}
    >
      {message && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 bg-zinc-800 text-white rounded-lg shadow-lg text-sm">
          {message}
          <button onClick={() => setMessage('')} className="ml-4 opacity-70 hover:opacity-100">&times;</button>
        </div>
      )}

      <div className="flex-1 w-full h-full relative overflow-hidden">
        {appView === 'planner' && (
          <PlannerPage setMessage={setMessage} profile={profile} setAppView={setAppView} />
        )}
        
        {appView === 'dashboard' && (
          <DashboardPage />
        )}

        {appView === 'templates' && (
          <div className="flex flex-col gap-6 p-6 h-full overflow-y-auto bg-zinc-50/50">
            <div className="flex items-center gap-4 mb-4">
              <button 
                onClick={() => setAppView(activeView)}
                className="px-4 py-2 text-sm font-medium text-zinc-600 bg-white border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors"
              >
                &larr; Back to {activeView === 'planner' ? 'Planner' : 'Dashboard'}
              </button>
              <h2 className="text-xl font-bold text-zinc-800">Template Settings</h2>
            </div>
            
            <div className="max-w-4xl w-full mx-auto space-y-8">
              <TemplateManager setMessage={setMessage} profile={profile} setProfile={setProfile} setAppView={setAppView} />
              <FixedBlockManager setMessage={setMessage} />
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
};
