import { lazy, Suspense, useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { OnboardingFlow } from '../components/onboarding/OnboardingFlow';
import { PlannerSelection } from '../components/onboarding/PlannerSelection';
import { userApi } from '../api/userApi';
import { MainLayout } from '../components/Layout/MainLayout';

const PlannerPage = lazy(() => import('./PlannerPage').then(m => ({ default: m.PlannerPage })));
const DashboardPage = lazy(() => import('./DashboardPage').then(m => ({ default: m.DashboardPage })));
const HistoryPage = lazy(() => import('./HistoryPage').then(m => ({ default: m.HistoryPage })));
const UserProfilePage = lazy(() => import('./UserProfilePage').then(m => ({ default: m.UserProfilePage })));
const ManageTemplatePage = lazy(() => import('./ManageTemplatePage').then(m => ({ default: m.ManageTemplatePage })));

export const AppShell = () => {
  const { user } = useAuth();
  
  // View states: 'planner', 'dashboard', 'templates', 'profile'
  const [appView, setAppView] = useState<string>('planner');
  const [message, setMessage] = useState('');
  const [profile, setProfile] = useState<any>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);

  // Active top navigation tab (templates view is an overlay state)
  const [activeView, setActiveView] = useState<'planner' | 'dashboard' | 'history'>('planner');

  useEffect(() => {
    // Sync appView and activeView when navigating
    if (appView === 'planner' || appView === 'dashboard' || appView === 'history') {
      setActiveView(appView as 'planner' | 'dashboard' | 'history');
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
        <Suspense fallback={<div className="p-8 text-center text-zinc-500">Loading view...</div>}>
          {appView === 'planner' && (
            <PlannerPage setMessage={setMessage} profile={profile} setAppView={setAppView} />
          )}
          
          {appView === 'dashboard' && (
            <DashboardPage />
          )}

          {appView === 'history' && (
            <HistoryPage />
          )}

          {appView === 'templates' && (
            <ManageTemplatePage 
              activeView={activeView}
              setAppView={setAppView}
              profile={profile}
              setProfile={setProfile}
              setMessage={setMessage}
            />
          )}

          {appView === 'profile' && (
            <UserProfilePage profile={profile} setProfile={setProfile} setMessage={setMessage} setAppView={setAppView} />
          )}
        </Suspense>
      </div>
    </MainLayout>
  );
};
