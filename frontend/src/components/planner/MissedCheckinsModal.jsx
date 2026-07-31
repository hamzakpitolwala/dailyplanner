import { useState, useEffect } from 'react';
import { styles } from '../../utils/styles';
import { fetchMissedReasons, fetchAlternateActivities, postTaskCheckin } from '../../api/taskApi';

export const MissedCheckinsModal = ({
  tasks,
  onComplete,
  setMessage
}) => {
  const [reasons, setReasons] = useState([]);
  const [alternates, setAlternates] = useState([]);
  
  // State maps taskId -> { missed_reason_id, alternate_activity_id, notes }
  const [checkinsData, setCheckinsData] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const loadOptions = async () => {
      try {
        const fetchedReasons = await fetchMissedReasons();
        setReasons(fetchedReasons);
        const fetchedAlternates = await fetchAlternateActivities();
        setAlternates(fetchedAlternates);
        
        // Initialize state
        const initial = {};
        tasks.forEach(t => {
          initial[t.id] = { missed_reason_id: '', alternate_activity_id: '', notes: '' };
        });
        setCheckinsData(initial);
      } catch (err) {
        setMessage(err.message);
      }
    };
    loadOptions();
  }, [tasks, setMessage]);

  const handleChange = (taskId, field, value) => {
    setCheckinsData(prev => ({
      ...prev,
      [taskId]: {
        ...prev[taskId],
        [field]: value
      }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      for (const t of tasks) {
        const data = checkinsData[t.id];
        // Validate required
        if (t.requires_reason && !data.missed_reason_id) {
          throw new Error(`Reason is required for task: ${t.title}`);
        }
        
        await postTaskCheckin(t.id, {
          status: t.status, // Preserve the auto-marked status
          missed_reason_id: data.missed_reason_id || null,
          alternate_activity_id: data.alternate_activity_id || null,
          notes: data.notes || null
        });
      }
      setMessage("Missed check-ins submitted successfully.");
      onComplete();
    } catch (err) {
      setMessage(err.message);
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{...styles.modalOverlay, display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.5)', position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', zIndex: 1000}}>
      <div style={{...styles.panel, width: '600px', maxWidth: '90%', maxHeight: '80vh', overflowY: 'auto' }}>
        <h2>Review Missed Tasks</h2>
        <p style={styles.muted}>The following tasks from previous days were not marked as done. Please provide a reason or alternate activity.</p>
        
        <form onSubmit={handleSubmit}>
          {tasks.map(t => {
            const data = checkinsData[t.id] || {};
            return (
              <div key={t.id} style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
                <h4 style={{ margin: '0 0 0.5rem 0' }}>{t.title} <span style={{fontSize: '0.8rem', color: '#6b7280'}}>({t.status.replace(/_/g, ' ')})</span></h4>
                
                {t.requires_reason && (
                  <label style={{...styles.label, marginBottom: '0.5rem'}}>
                    Reason for missing <span style={{color: 'red'}}>*</span>
                    <select
                      style={styles.input}
                      value={data.missed_reason_id || ''}
                      onChange={(e) => handleChange(t.id, 'missed_reason_id', e.target.value)}
                      required
                    >
                      <option value="">-- Select a reason --</option>
                      {reasons.map(r => (
                        <option key={r.id} value={r.id}>{r.name}</option>
                      ))}
                    </select>
                  </label>
                )}

                {t.allows_alternate && (
                  <label style={{...styles.label, marginBottom: '0.5rem'}}>
                    Alternate Activity
                    <select
                      style={styles.input}
                      value={data.alternate_activity_id || ''}
                      onChange={(e) => handleChange(t.id, 'alternate_activity_id', e.target.value)}
                    >
                      <option value="">-- Select an alternate activity --</option>
                      {alternates.map(a => (
                        <option key={a.id} value={a.id}>{a.name}</option>
                      ))}
                    </select>
                  </label>
                )}
                
                <label style={styles.label}>
                  Notes
                  <input
                    style={{...styles.input, marginBottom: 0}}
                    type="text"
                    placeholder="Optional notes"
                    value={data.notes || ''}
                    onChange={(e) => handleChange(t.id, 'notes', e.target.value)}
                  />
                </label>
              </div>
            );
          })}

          <div style={styles.actions}>
            <button style={styles.primaryButton} type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Submit Check-ins'}
            </button>
            <button style={styles.button} type="button" onClick={onComplete} disabled={isSubmitting}>
              Skip
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
