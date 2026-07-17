import { useEffect, useState } from 'react';

const AUTH_BASE = '/auth';
const PLANNER_BASE = '/planners';

const emptyActivity = {
  title: '',
  description: '',
  category: '',
  start_time: '',
  end_time: '',
};

const todayIso = () => new Date().toISOString().slice(0, 10);

function App() {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [message, setMessage] = useState('');
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [planner, setPlanner] = useState(null);
  const [plannerDate, setPlannerDate] = useState(todayIso());
  const [plannerTitle, setPlannerTitle] = useState('');
  const [plannerNotes, setPlannerNotes] = useState('');
  const [activityForm, setActivityForm] = useState(emptyActivity);
  const [editingActivityId, setEditingActivityId] = useState(null);

  useEffect(() => {
    const hash = window.location.hash;
    if (!hash) return;

    const params = new URLSearchParams(hash.substring(1));
    const oauthToken = params.get('token');
    const oauthError = params.get('error');
    window.history.replaceState(null, '', window.location.pathname);

    if (oauthToken) {
      localStorage.setItem('token', oauthToken);
      setToken(oauthToken);
      setMessage('Signed in via OAuth2');
    } else if (oauthError) {
      setMessage(`OAuth2 error: ${oauthError}`);
    }
  }, []);

  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const apiRequest = async (path, options = {}) => {
    const response = await fetch(path, {
      ...options,
      headers: {
        ...authHeaders,
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    });

    if (response.status === 204) return null;

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Request failed');
    }
    return data;
  };

  const loadPlanner = async (date = plannerDate) => {
    const data = await apiRequest(`${PLANNER_BASE}/today?planner_date=${date}`);
    setPlanner(data);
    setPlannerTitle(data.title);
    setPlannerNotes(data.notes || '');
  };

  useEffect(() => {
    if (!token) return;

    const loadUserAndPlanner = async () => {
      try {
        const me = await apiRequest(`${AUTH_BASE}/me`);
        setUser(me);
        await loadPlanner(plannerDate);
      } catch (error) {
        localStorage.removeItem('token');
        setToken('');
        setUser(null);
        setPlanner(null);
        setMessage(error.message);
      }
    };

    loadUserAndPlanner();
  }, [token]);

  const submitAuth = async (event) => {
    event.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const isRegister = mode === 'register';
      const response = await fetch(
        isRegister ? `${AUTH_BASE}/register` : `${AUTH_BASE}/token`,
        isRegister
          ? {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email, username, password }),
            }
          : {
              method: 'POST',
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
              body: new URLSearchParams({ username: email, password }).toString(),
            },
      );

      const data = await response.json();
      if (!response.ok) {
        setMessage(data.detail || 'Request failed');
        return;
      }

      if (isRegister) {
        setMessage('Registered. Please sign in.');
        setMode('login');
      } else {
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        setMessage('Logged in');
      }
    } catch (error) {
      setMessage('Unable to reach the API. Make sure the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const savePlanner = async (event) => {
    event.preventDefault();
    if (!planner) return;

    try {
      const data = await apiRequest(`${PLANNER_BASE}/${planner.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          planner_date: plannerDate,
          title: plannerTitle,
          notes: plannerNotes || null,
        }),
      });
      setPlanner(data);
      setMessage('Planner updated');
    } catch (error) {
      setMessage(error.message);
    }
  };

  const changePlannerDate = async (event) => {
    const nextDate = event.target.value;
    setPlannerDate(nextDate);
    setActivityForm(emptyActivity);
    setEditingActivityId(null);
    try {
      await loadPlanner(nextDate);
    } catch (error) {
      setMessage(error.message);
    }
  };

  const submitActivity = async (event) => {
    event.preventDefault();
    if (!planner) return;

    const payload = {
      title: activityForm.title,
      description: activityForm.description || null,
      category: activityForm.category || null,
      start_time: activityForm.start_time || null,
      end_time: activityForm.end_time || null,
    };

    try {
      if (editingActivityId) {
        await apiRequest(`${PLANNER_BASE}/activities/${editingActivityId}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        });
        setMessage('Activity updated');
      } else {
        await apiRequest(`${PLANNER_BASE}/${planner.id}/activities`, {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        setMessage('Activity added');
      }
      setActivityForm(emptyActivity);
      setEditingActivityId(null);
      await loadPlanner(plannerDate);
    } catch (error) {
      setMessage(error.message);
    }
  };

  const editActivity = (activity) => {
    setEditingActivityId(activity.id);
    setActivityForm({
      title: activity.title,
      description: activity.description || '',
      category: activity.category || '',
      start_time: activity.start_time || '',
      end_time: activity.end_time || '',
    });
  };

  const deleteActivity = async (activityId) => {
    try {
      await apiRequest(`${PLANNER_BASE}/activities/${activityId}`, { method: 'DELETE' });
      setMessage('Activity deleted');
      await loadPlanner(plannerDate);
    } catch (error) {
      setMessage(error.message);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken('');
    setUser(null);
    setPlanner(null);
    setMessage('Logged out');
  };

  const oauthLogin = (provider) => {
    window.location.href = `${AUTH_BASE}/${provider}/authorize`;
  };

  if (!token) {
    return (
      <main style={styles.shell}>
        <section style={styles.panel}>
          <h1>DailyPlanner</h1>
          <p style={styles.muted}>Phase 0 auth and Phase 1 planner CRUD</p>

          <div style={styles.tabs}>
            <button style={mode === 'login' ? styles.activeButton : styles.button} onClick={() => setMode('login')}>
              Login
            </button>
            <button style={mode === 'register' ? styles.activeButton : styles.button} onClick={() => setMode('register')}>
              Register
            </button>
          </div>

          <form onSubmit={submitAuth} style={styles.form}>
            <input style={styles.input} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" />
            {mode === 'register' && (
              <input style={styles.input} value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Username" />
            )}
            <input
              style={styles.input}
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
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
  }

  return (
    <main style={styles.appShell}>
      <header style={styles.header}>
        <div>
          <h1 style={styles.heading}>DailyPlanner</h1>
          <p style={styles.muted}>{user ? `Hello, ${user.username}` : 'Loading user...'}</p>
        </div>
        <button style={styles.button} onClick={logout}>Logout</button>
      </header>

      {message && <p style={styles.message}>{message}</p>}

      <section style={styles.workspace}>
        <div style={styles.panel}>
          <form onSubmit={savePlanner} style={styles.form}>
            <label style={styles.label}>
              Planner date
              <input style={styles.input} type="date" value={plannerDate} onChange={changePlannerDate} />
            </label>
            <label style={styles.label}>
              Title
              <input style={styles.input} value={plannerTitle} onChange={(event) => setPlannerTitle(event.target.value)} />
            </label>
            <label style={styles.label}>
              Notes
              <textarea style={styles.textarea} value={plannerNotes} onChange={(event) => setPlannerNotes(event.target.value)} />
            </label>
            <button style={styles.primaryButton} type="submit">Save planner</button>
          </form>
        </div>

        <div style={styles.panel}>
          <h2 style={styles.subheading}>{editingActivityId ? 'Edit activity' : 'Add activity'}</h2>
          <form onSubmit={submitActivity} style={styles.form}>
            <input
              style={styles.input}
              value={activityForm.title}
              onChange={(event) => setActivityForm({ ...activityForm, title: event.target.value })}
              placeholder="Activity title"
              required
            />
            <input
              style={styles.input}
              value={activityForm.category}
              onChange={(event) => setActivityForm({ ...activityForm, category: event.target.value })}
              placeholder="Category"
            />
            <div style={styles.timeGrid}>
              <input
                style={styles.input}
                type="time"
                value={activityForm.start_time}
                onChange={(event) => setActivityForm({ ...activityForm, start_time: event.target.value })}
              />
              <input
                style={styles.input}
                type="time"
                value={activityForm.end_time}
                onChange={(event) => setActivityForm({ ...activityForm, end_time: event.target.value })}
              />
            </div>
            <textarea
              style={styles.textarea}
              value={activityForm.description}
              onChange={(event) => setActivityForm({ ...activityForm, description: event.target.value })}
              placeholder="Description"
            />
            <div style={styles.actions}>
              <button style={styles.primaryButton} type="submit">
                {editingActivityId ? 'Update activity' : 'Add activity'}
              </button>
              {editingActivityId && (
                <button
                  style={styles.button}
                  type="button"
                  onClick={() => {
                    setEditingActivityId(null);
                    setActivityForm(emptyActivity);
                  }}
                >
                  Cancel
                </button>
              )}
            </div>
          </form>
        </div>
      </section>

      <section style={styles.panel}>
        <h2 style={styles.subheading}>Activities</h2>
        {!planner?.activities?.length && <p style={styles.muted}>No activities yet.</p>}
        <div style={styles.activityList}>
          {planner?.activities?.map((activity) => (
            <article key={activity.id} style={styles.activityItem}>
              <div>
                <strong>{activity.title}</strong>
                <p style={styles.muted}>
                  {[activity.start_time, activity.end_time].filter(Boolean).join(' - ') || 'No time set'}
                  {activity.category ? ` | ${activity.category}` : ''}
                </p>
                {activity.description && <p>{activity.description}</p>}
              </div>
              <div style={styles.actions}>
                <button style={styles.button} onClick={() => editActivity(activity)}>Edit</button>
                <button style={styles.dangerButton} onClick={() => deleteActivity(activity.id)}>Delete</button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

const styles = {
  shell: {
    maxWidth: 520,
    margin: '3rem auto',
    padding: '0 1rem',
    fontFamily: 'ui-sans-serif, system-ui, sans-serif',
  },
  appShell: {
    maxWidth: 1100,
    margin: '2rem auto',
    padding: '0 1rem',
    fontFamily: 'ui-sans-serif, system-ui, sans-serif',
    color: '#17202a',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '1rem',
    marginBottom: '1rem',
  },
  heading: {
    margin: 0,
  },
  subheading: {
    margin: '0 0 1rem',
    fontSize: '1.1rem',
  },
  workspace: {
    display: 'grid',
    gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)',
    gap: '1rem',
    marginBottom: '1rem',
  },
  panel: {
    border: '1px solid #dde3ea',
    borderRadius: 8,
    padding: '1rem',
    background: '#ffffff',
  },
  tabs: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '1rem',
  },
  form: {
    display: 'grid',
    gap: '0.75rem',
  },
  label: {
    display: 'grid',
    gap: '0.35rem',
    fontSize: '0.9rem',
    fontWeight: 600,
  },
  input: {
    width: '100%',
    boxSizing: 'border-box',
    border: '1px solid #cfd8e3',
    borderRadius: 6,
    padding: '0.65rem 0.75rem',
    font: 'inherit',
  },
  textarea: {
    width: '100%',
    minHeight: 84,
    boxSizing: 'border-box',
    border: '1px solid #cfd8e3',
    borderRadius: 6,
    padding: '0.65rem 0.75rem',
    font: 'inherit',
    resize: 'vertical',
  },
  timeGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '0.75rem',
  },
  oauthGrid: {
    display: 'grid',
    gap: '0.5rem',
    marginTop: '1rem',
  },
  activityList: {
    display: 'grid',
    gap: '0.75rem',
  },
  activityItem: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: '1rem',
    border: '1px solid #edf1f5',
    borderRadius: 8,
    padding: '0.85rem',
    background: '#fbfcfe',
  },
  actions: {
    display: 'flex',
    gap: '0.5rem',
    flexWrap: 'wrap',
  },
  button: {
    border: '1px solid #cfd8e3',
    borderRadius: 6,
    padding: '0.6rem 0.85rem',
    background: '#ffffff',
    cursor: 'pointer',
    font: 'inherit',
  },
  activeButton: {
    border: '1px solid #17202a',
    borderRadius: 6,
    padding: '0.6rem 0.85rem',
    background: '#17202a',
    color: '#ffffff',
    cursor: 'pointer',
    font: 'inherit',
  },
  primaryButton: {
    border: '1px solid #276749',
    borderRadius: 6,
    padding: '0.65rem 0.9rem',
    background: '#276749',
    color: '#ffffff',
    cursor: 'pointer',
    font: 'inherit',
  },
  dangerButton: {
    border: '1px solid #b42318',
    borderRadius: 6,
    padding: '0.6rem 0.85rem',
    background: '#ffffff',
    color: '#b42318',
    cursor: 'pointer',
    font: 'inherit',
  },
  muted: {
    margin: '0.25rem 0',
    color: '#667085',
  },
  message: {
    border: '1px solid #c7d7fe',
    borderRadius: 6,
    padding: '0.75rem',
    background: '#eef4ff',
  },
};

export default App;
