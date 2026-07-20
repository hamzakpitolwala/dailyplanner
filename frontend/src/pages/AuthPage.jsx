import { useState } from 'react';
import { styles } from '../utils/styles';
import { login, register, getOAuthUrl } from '../api/authApi';
import { useAuth } from '../contexts/AuthContext';

export const AuthPage = () => {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { login: setAuthToken } = useAuth();

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
    <main style={styles.shell}>
      <section style={styles.panel}>
        <h1>DailyPlanner</h1>
        <p style={styles.muted}>Phase 0–2: Auth, Planner CRUD, and Check-ins</p>

        <div style={styles.tabs}>
          <button style={mode === 'login' ? styles.activeButton : styles.button} onClick={() => setMode('login')}>
            Login
          </button>
          <button style={mode === 'register' ? styles.activeButton : styles.button} onClick={() => setMode('register')}>
            Register
          </button>
        </div>

        <form onSubmit={submitAuth} style={styles.form}>
          <input style={styles.input} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" required />
          {mode === 'register' && (
            <input style={styles.input} value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Username" required />
          )}
          <input
            style={styles.input}
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password"
            required
          />
          <button style={styles.primaryButton} type="submit" disabled={loading}>
            {loading ? 'Working...' : mode === 'register' ? 'Register' : 'Login'}
          </button>
        </form>

        <div style={styles.oauthGrid}>
          <button style={styles.button} onClick={() => oauthLogin('google')}>Sign in with Google</button>
          <button style={styles.button} onClick={() => oauthLogin('github')}>Sign in with GitHub</button>
        </div>

        {message && <p style={styles.message}>{message}</p>}
      </section>
    </main>
  );
};
