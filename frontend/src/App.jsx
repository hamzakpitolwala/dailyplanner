import { useEffect, useState } from 'react';

const AUTH_BASE = '/auth';
const PLANNER_BASE = '/planners';

const CHECKIN_STATUSES = [
  { value: 'done', label: '✅ Done', color: '#276749' },
  { value: 'not_done', label: '❌ Not Done', color: '#b42318' },
  { value: 'partial', label: '🔶 Partial', color: '#b54708' },
  { value: 'rescheduled', label: '📅 Rescheduled', color: '#3538cd' },
];

const REASON_CODES = [
  { value: 'too_busy', label: 'Too busy' },
  { value: 'forgot', label: 'Forgot' },
  { value: 'not_feeling_well', label: 'Not feeling well' },
  { value: 'schedule_conflict', label: 'Schedule conflict' },
  { value: 'low_priority', label: 'Low priority' },
  { value: 'other', label: 'Other' },
];

const ALTERNATE_PRESETS = [
  'Doing some important work',
  'Attending an unscheduled meeting',
  'Helping a colleague',
  'Personal errand',
];

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
  const [appView, setAppView] = useState('planner'); // 'planner' or 'templates'
  const [planner, setPlanner] = useState(null);
  const [plannerDate, setPlannerDate] = useState(todayIso());
  const [plannerTitle, setPlannerTitle] = useState('');
  const [plannerNotes, setPlannerNotes] = useState('');
  const [activityForm, setActivityForm] = useState(emptyActivity);
  const [editingActivityId, setEditingActivityId] = useState(null);

  // Check-in modal state
  const [checkinModal, setCheckinModal] = useState(null); // { activity, status }
  const [checkinNotes, setCheckinNotes] = useState('');
  const [reasonCode, setReasonCode] = useState('');
  const [reasonText, setReasonText] = useState('');
  const [altDescription, setAltDescription] = useState('');
  const [altCategory, setAltCategory] = useState('');
  const [targetDate, setTargetDate] = useState('');

  // Check-in history
  const [historyActivityId, setHistoryActivityId] = useState(null);
  const [checkinHistory, setCheckinHistory] = useState([]);

  // Templates
  const [templates, setTemplates] = useState([]);
  const [templateName, setTemplateName] = useState('');

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

  const loadTemplates = async () => {
    const data = await apiRequest(`/templates`);
    setTemplates(data || []);
  };

  useEffect(() => {
    if (!token) return;

    const loadUserAndPlanner = async () => {
      try {
        const me = await apiRequest(`${AUTH_BASE}/me`);
        setUser(me);
        await loadPlanner(plannerDate);
        await loadTemplates();
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

  // --- Check-in logic ---

  const openCheckinModal = (activity, statusValue) => {
    if (statusValue === 'not_done' || statusValue === 'rescheduled') {
      // Open the conditional modal
      setCheckinModal({ activity, status: statusValue });
      setCheckinNotes('');
      setReasonCode('');
      setReasonText('');
      setAltDescription('');
      setAltCategory('');
      
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      setTargetDate(tomorrow.toISOString().slice(0, 10));
    } else {
      // Directly submit for done/partial
      submitCheckin(activity.id, statusValue, '');
    }
  };

  const submitCheckin = async (activityId, status, notes, missedReason = null, alternate = null, tgtDate = null) => {
    const payload = { action_type: 'status_change', new_state: status, notes: notes || null };

    if (status === 'not_done' && missedReason) {
        payload.missed_reason = missedReason;
    }
    if (status === 'not_done' && alternate) {
      payload.alternate_activity = alternate;
    }
    if (status === 'rescheduled' && tgtDate) {
      payload.target_date = tgtDate;
    }

    try {
      await apiRequest(`${PLANNER_BASE}/activities/${activityId}/history`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setMessage(`Checked in: ${status.replace('_', ' ')}`);
      setCheckinModal(null);
      await loadPlanner(plannerDate);
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleCheckinModalSubmit = (event) => {
    event.preventDefault();
    const { activity, status } = checkinModal;

    const missedReason = reasonCode
      ? { reason_code: reasonCode, free_text: reasonText || null }
      : null;

    const alternate = altDescription
      ? { description: altDescription, category: altCategory || null }
      : null;

    submitCheckin(activity.id, status, checkinNotes, missedReason, alternate, targetDate);
  };

  const loadCheckinHistory = async (activityId) => {
    if (historyActivityId === activityId) {
      setHistoryActivityId(null);
      setCheckinHistory([]);
      return;
    }
    try {
      const data = await apiRequest(`${PLANNER_BASE}/activities/${activityId}/history`);
      setCheckinHistory(data);
      setHistoryActivityId(activityId);
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

  const getStatusBadge = (status) => {
    const config = CHECKIN_STATUSES.find((s) => s.value === status) || {
      label: status,
      color: '#667085',
    };
    return (
      <span
        style={{
          ...styles.badge,
          background: config.color + '18',
          color: config.color,
          border: `1px solid ${config.color}40`,
        }}
      >
        {config.label}
      </span>
    );
  };

  // --- Auth screen ---

  if (!token) {
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

  // --- Main app ---

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
              onClick={() => {
                localStorage.removeItem('token');
                setToken('');
                setUser(null);
                setPlanner(null);
              }}
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

      {appView === 'templates' ? (
        <div>
          <h2>Templates Library</h2>
          <form onSubmit={submitTemplate} style={{ marginBottom: '1rem' }}>
            <input
              style={styles.input}
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              placeholder="New Template Name..."
              required
            />
            <button type="submit" style={styles.primaryButton}>Create Template</button>
          </form>

          {templates.map(tmpl => (
            <div key={tmpl.id} style={styles.panel}>
              <div style={styles.header}>
                <h3>{tmpl.name} {tmpl.in_use && <span style={{color: 'green'}}>(Active)</span>}</h3>
                <div>
                  <button style={styles.smallButton} onClick={() => toggleTemplateInUse(tmpl.id, tmpl.in_use)}>
                    {tmpl.in_use ? 'Deactivate' : 'Set Active'}
                  </button>
                  <button style={styles.smallButton} onClick={() => addTemplateActivity(tmpl.id)}>Add Activity</button>
                </div>
              </div>
              <div>
                {tmpl.activity_templates.map(act => (
                  <div key={act.id} style={{ padding: '0.5rem', borderBottom: '1px solid #ccc' }}>
                    {act.title}
                  </div>
                ))}
                {tmpl.activity_templates.length === 0 && <p style={styles.muted}>No activities in template.</p>}
              </div>
            </div>
          ))}
          {templates.length === 0 && <p>No templates yet.</p>}
        </div>
      ) : (
        <div style={styles.workspace}>
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
        </div>
      )}

      {appView === 'planner' && (
        <section style={styles.panel}>
          <h2 style={styles.subheading}>Activities</h2>
          {!planner?.activities?.length && <p style={styles.muted}>No activities yet.</p>}
          <div style={styles.activityList}>
            {planner?.activities?.map((activity) => {
              const isDone = activity.status === 'done';
              const isNotDone = activity.status === 'not_done';
              const isTerminal = ['done', 'not_done', 'rescheduled', 'cancelled'].includes(activity.status);
              
              let containerStyle = { ...styles.activityItem };
              if (isDone) containerStyle.opacity = 0.7;
              if (isNotDone) containerStyle.background = '#fdeded';

              return (
              <article key={activity.id} style={containerStyle}>
                <div style={{ flex: 1, textDecoration: isDone ? 'line-through' : 'none' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <strong style={{ color: isNotDone ? '#b42318' : 'inherit' }}>{activity.title}</strong>
                    {getStatusBadge(activity.status)}
                    {activity.carried_over_from_id && (
                      <span style={{ fontSize: '0.8rem', color: '#b54708', background: '#ffead5', padding: '0.1rem 0.4rem', borderRadius: 4 }}>
                        ↳ Carried over
                      </span>
                    )}
                  </div>
                  <p style={styles.muted}>
                    {[activity.start_time, activity.end_time].filter(Boolean).join(' – ') || 'No time set'}
                    {activity.category ? ` | ${activity.category}` : ''}
                  </p>
                  {activity.description && <p>{activity.description}</p>}

                  {/* Status check-in buttons */}
                  <div style={{ ...styles.actions, marginTop: '0.5rem' }}>
                    {CHECKIN_STATUSES.map((s) => {
                      // Primitive state machine for UI display logic (Slice 1 requirement)
                      const allowedStates = {
                        planned: ['in_progress', 'partial', 'done', 'not_done', 'rescheduled', 'cancelled'],
                        in_progress: ['partial', 'done', 'not_done', 'rescheduled', 'cancelled'],
                        partial: ['done', 'not_done', 'rescheduled', 'cancelled'],
                        done: [],
                        not_done: [],
                        rescheduled: [],
                        cancelled: [],
                      };
                      // Time check
                      let isPastEndTime = false;
                      if (activity.end_time && planner.planner_date) {
                        const now = new Date();
                        const todayStr = now.toISOString().slice(0, 10);
                        if (planner.planner_date < todayStr) {
                          isPastEndTime = true; // past day
                        } else if (planner.planner_date === todayStr) {
                          const timeParts = activity.end_time.split(':');
                          const end = new Date();
                          end.setHours(parseInt(timeParts[0], 10), parseInt(timeParts[1], 10), 0, 0);
                          if (now > end) {
                            isPastEndTime = true;
                          }
                        }
                      }
                      
                      const isDisabled = activity.status === s.value || !isAllowed || (isPastEndTime && !['rescheduled', 'cancelled'].includes(s.value));

                      if (!isAllowed && activity.status !== s.value) return null;

                      return (
                        <button
                          key={s.value}
                          style={{
                            ...styles.smallButton,
                            borderColor: s.color,
                            color: activity.status === s.value ? '#fff' : s.color,
                            background: activity.status === s.value ? s.color : '#fff',
                            opacity: isDisabled ? 0.5 : 1,
                            cursor: isDisabled ? 'not-allowed' : 'pointer'
                          }}
                          onClick={() => openCheckinModal(activity, s.value)}
                          disabled={isDisabled}
                        >
                          {s.label}
                        </button>
                      );
                    })}
                  </div>

                  {/* History toggle */}
                  <button
                    style={{ ...styles.linkButton, marginTop: '0.5rem' }}
                    onClick={() => loadCheckinHistory(activity.id)}
                  >
                    {historyActivityId === activity.id ? 'Hide history' : 'Show history'}
                  </button>

                  {/* Check-in history */}
                  {historyActivityId === activity.id && (
                    <div style={styles.historyList}>
                      {checkinHistory.length === 0 && (
                        <p style={styles.muted}>No check-ins yet.</p>
                      )}
                      {checkinHistory.map((ci) => (
                        <div key={ci.id} style={styles.historyItem}>
                          <span>{getStatusBadge(ci.new_state)}</span>
                          <span style={styles.muted}>
                            {new Date(ci.timestamp).toLocaleString()}
                          </span>
                          {ci.notes && <span> — {ci.notes}</span>}
                          {ci.missed_reason && (
                            <span style={{ color: '#b42318' }}>
                              {' '}| Reason: {ci.missed_reason.reason_code.replace('_', ' ')}
                              {ci.missed_reason.free_text ? ` (${ci.missed_reason.free_text})` : ''}
                            </span>
                          )}
                          {ci.alternate_activity && (
                            <span style={{ color: '#3538cd' }}>
                              {' '}| Instead: {ci.alternate_activity.description}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div style={styles.actions}>
                  {!isTerminal && (
                    <button style={styles.button} onClick={() => editActivity(activity)}>Edit</button>
                  )}
                  <button style={styles.dangerButton} onClick={() => deleteActivity(activity.id)}>Delete</button>
                </div>
              </article>
            );
          })}
          </div>
        </section>
      )}

      {/* ---- Check-in modal ---- */}
      {checkinModal && (
        <div style={styles.modalOverlay} onClick={() => setCheckinModal(null)}>
          <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h3 style={styles.subheading}>
              {checkinModal.status === 'not_done' ? 'Mark as Not Done' : 'Reschedule Activity'}
            </h3>
            <p style={{ margin: '0 0 1rem', fontWeight: 'bold' }}>{checkinModal.activity.title}</p>

            <form onSubmit={handleCheckinModalSubmit} style={styles.form}>
              {checkinModal.status === 'rescheduled' && (
                <label style={styles.label}>
                  Target Date <span style={{ color: '#b42318' }}>*</span>
                  <input
                    style={styles.input}
                    type="date"
                    value={targetDate}
                    onChange={(e) => setTargetDate(e.target.value)}
                    required
                  />
                </label>
              )}

              <label style={styles.label}>
                Notes (optional)
                <textarea
                  style={styles.textarea}
                  value={checkinNotes}
                  onChange={(e) => setCheckinNotes(e.target.value)}
                  placeholder="Any additional notes…"
                />
              </label>

              {/* Reason picker (shown if policy requires reason or user wants to provide one) */}
              {checkinModal.status === 'not_done' && checkinModal.activity.policy?.requires_reason !== false && (
                <>
                  <label style={styles.label}>
                    Why was it missed? {checkinModal.activity.policy?.requires_reason && <span style={{ color: '#b42318' }}>*</span>}
                    <select
                      style={styles.input}
                      value={reasonCode}
                      onChange={(e) => setReasonCode(e.target.value)}
                      required={checkinModal.activity.policy?.requires_reason}
                    >
                      <option value="">Select a reason…</option>
                      {REASON_CODES.map((r) => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                  </label>
                  {reasonCode && (
                    <label style={styles.label}>
                      Additional detail (optional)
                      <input
                        style={styles.input}
                        value={reasonText}
                        onChange={(e) => setReasonText(e.target.value)}
                        placeholder="Explain further…"
                      />
                    </label>
                  )}
                </>
              )}

              {/* Alternate activity (shown if policy allows) */}
              {checkinModal.status === 'not_done' && checkinModal.activity.policy?.allows_alternate !== false && (
                <>
                  <label style={styles.label}>
                    What did you do instead? (optional)
                    <select
                      style={styles.input}
                      value={altDescription}
                      onChange={(e) => setAltDescription(e.target.value)}
                    >
                      <option value="">Select or type below…</option>
                      {ALTERNATE_PRESETS.map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                    <input
                      style={{ ...styles.input, marginTop: '0.35rem' }}
                      value={altDescription}
                      onChange={(e) => setAltDescription(e.target.value)}
                      placeholder="Or type a custom description…"
                    />
                  </label>
                  {altDescription && (
                    <label style={styles.label}>
                      Category (optional)
                      <input
                        style={styles.input}
                        value={altCategory}
                        onChange={(e) => setAltCategory(e.target.value)}
                        placeholder="e.g. work, personal, errands"
                      />
                    </label>
                  )}
                </>
              )}

              <div style={styles.actions}>
                <button style={styles.primaryButton} type="submit">
                  Submit check-in
                </button>
                <button
                  style={styles.button}
                  type="button"
                  onClick={() => setCheckinModal(null)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
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
  smallButton: {
    border: '1px solid',
    borderRadius: 5,
    padding: '0.35rem 0.6rem',
    fontSize: '0.8rem',
    cursor: 'pointer',
    font: 'inherit',
    fontWeight: 500,
  },
  linkButton: {
    border: 'none',
    background: 'none',
    color: '#3538cd',
    cursor: 'pointer',
    font: 'inherit',
    fontSize: '0.85rem',
    padding: 0,
    textDecoration: 'underline',
  },
  badge: {
    display: 'inline-block',
    fontSize: '0.75rem',
    fontWeight: 600,
    padding: '0.2rem 0.55rem',
    borderRadius: 12,
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
  historyList: {
    marginTop: '0.5rem',
    padding: '0.5rem',
    borderTop: '1px solid #edf1f5',
  },
  historyItem: {
    padding: '0.35rem 0',
    fontSize: '0.85rem',
    borderBottom: '1px solid #f3f4f6',
  },
  modalOverlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.4)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    background: '#fff',
    borderRadius: 12,
    padding: '1.5rem',
    width: '100%',
    maxWidth: 480,
    maxHeight: '90vh',
    overflowY: 'auto',
    boxShadow: '0 8px 30px rgba(0, 0, 0, 0.15)',
  },
};

export default App;
