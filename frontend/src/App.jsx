import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AuthPage } from './pages/AuthPage';
import { AppShell } from './pages/AppShell';

const AppContent = () => {
  const auth = useAuth();

  // During Vite HMR, context can momentarily be null before Provider remounts
  if (!auth) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Connecting...</div>;
  }

  const { user, loading } = auth;

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading DailyPlanner...</div>;
  }

  return user ? <AppShell /> : <AuthPage />;
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
