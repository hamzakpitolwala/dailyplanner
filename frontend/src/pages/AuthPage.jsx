import { useState, useEffect } from 'react';
import { login, register, getOAuthUrl } from '../api/authApi';
import { useAuth } from '../contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, User, Lock, ArrowRight } from 'lucide-react';

const GoogleIcon = () => (
  <svg viewBox="0 0 24 24" width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
  </svg>
);

const GithubIcon = () => (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
  </svg>
);

export const AuthPage = () => {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { login: setAuthToken } = useAuth();

  useEffect(() => {
    const hash = window.location.hash;
    if (hash.includes('error=google_oauth_not_configured')) {
      setMessage('Google OAuth is not configured on the backend server.');
    } else if (hash.includes('error=github_oauth_not_configured')) {
      setMessage('GitHub OAuth is not configured on the backend server.');
    } else if (hash.includes('error=')) {
      const errorParam = hash.split('error=')[1]?.split('&')[0];
      if (errorParam) {
        setMessage(`OAuth login failed: ${decodeURIComponent(errorParam)}`);
      }
    }
  }, []);

  const submitAuth = async (event) => {
    event.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      let data;
      if (mode === 'register') {
        data = await register(email, username, password);
      } else {
        data = await login(email, password);
      }
      
      setAuthToken(data.access_token);
      setMessage('Success!');
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  const oauthLogin = (provider) => {
    window.location.href = getOAuthUrl(provider);
  };

  return (
    <main className="min-h-screen w-full flex items-center justify-center p-4 relative overflow-hidden">
      {/* Dynamic Background Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />

      <motion.section 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-md bg-card/80 backdrop-blur-xl border border-border rounded-3xl shadow-2xl p-8 relative z-10"
      >
        <div className="flex flex-col items-center mb-8">
          <motion.div 
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", bounce: 0.5, delay: 0.2 }}
            className="w-16 h-16 bg-gradient-to-br from-orange-400 via-orange-500 to-orange-600 rounded-2xl flex items-center justify-center mb-4 shadow-[0_4px_12px_rgba(249,115,22,0.4)] border border-orange-300/30"
          >
            <img src="/logo.png" alt="Logo" className="w-12 h-12 object-contain relative z-10 drop-shadow-md" />
          </motion.div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-zinc-900 to-zinc-500 dark:from-zinc-100 dark:to-zinc-500">
            DailyPlanner
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-2 text-center">
            Master your day. Own your time.
          </p>
        </div>

        <div className="flex p-1 bg-zinc-100 dark:bg-zinc-900 rounded-xl mb-8">
          <button 
            className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${mode === 'login' ? 'bg-card text-text shadow-sm' : 'text-zinc-500 hover:text-text'}`}
            onClick={() => { setMode('login'); setMessage(''); }}
          >
            Sign In
          </button>
          <button 
            className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${mode === 'register' ? 'bg-card text-text shadow-sm' : 'text-zinc-500 hover:text-text'}`}
            onClick={() => { setMode('register'); setMessage(''); }}
          >
            Register
          </button>
        </div>

        <form onSubmit={submitAuth} className="space-y-4">
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
            <input 
              className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              placeholder="Email address" 
              required 
            />
          </div>

          <AnimatePresence>
            {mode === 'register' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="relative"
              >
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
                <input 
                  className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                  value={username} 
                  onChange={(e) => setUsername(e.target.value)} 
                  placeholder="Username" 
                  required 
                />
              </motion.div>
            )}
          </AnimatePresence>

          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
            <input
              className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              required
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-primary hover:bg-primary-hover text-white rounded-xl py-3 font-medium transition-all flex items-center justify-center gap-2 group disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                {mode === 'register' ? 'Create Account' : 'Sign In'}
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </form>

        <div className="mt-8">
          <div className="relative flex items-center justify-center mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border"></div>
            </div>
            <div className="relative bg-card px-4 text-xs text-zinc-500 uppercase tracking-wider font-medium">
              Or continue with
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <button 
              onClick={() => oauthLogin('google')}
              className="flex items-center justify-center gap-2 py-2.5 border border-border rounded-xl hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
            >
              <GoogleIcon />
              <span className="text-sm font-medium">Google</span>
            </button>
            <button 
              onClick={() => oauthLogin('github')}
              className="flex items-center justify-center gap-2 py-2.5 border border-border rounded-xl hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
            >
              <GithubIcon />
              <span className="text-sm font-medium">GitHub</span>
            </button>
          </div>
        </div>

        <AnimatePresence>
          {message && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-6 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm text-center border border-red-100 dark:border-red-900/30"
            >
              {message}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.section>
    </main>
  );
};
