import { useState, useEffect } from 'react';
import { styles } from '../../utils/styles';
import { fetchMissedReasons, fetchAlternateActivities } from '../../api/taskApi';

export const TaskCheckinModal = ({
  task,
  plannerDate,
  initialStatus,
  onSubmit,
  onCancel,
  setMessage
}) => {
  const [reasons, setReasons] = useState([]);
  const [alternates, setAlternates] = useState([]);
  
  const [status, setStatus] = useState(initialStatus);
  const [missedReasonId, setMissedReasonId] = useState('');
  const [alternateActivityId, setAlternateActivityId] = useState('');
  const [notes, setNotes] = useState('');
  
  const initialStart = task.start_time ? task.start_time.split('T')[1]?.substring(0, 5) || '' : '';
  const initialEnd = task.due_date ? task.due_date.split('T')[1]?.substring(0, 5) || '' : '';
  const [rescheduleStart, setRescheduleStart] = useState(initialStart);
  const [rescheduleEnd, setRescheduleEnd] = useState(initialEnd);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadOptions = async () => {
      try {
        if (task.requires_reason) {
          const fetchedReasons = await fetchMissedReasons();
          setReasons(fetchedReasons);
        }
        if (task.allows_alternate) {
          const fetchedAlternates = await fetchAlternateActivities();
          setAlternates(fetchedAlternates);
        }
      } catch (err) {
        setMessage(err.message);
      }
    };
    loadOptions();
  }, [task, setMessage]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    let new_start_time = undefined;
    let new_due_date = undefined;
    if (status === 'rescheduled') {
      if (!rescheduleStart || !rescheduleEnd) {
        setError('Please select start and end times for rescheduling.');
        return;
      }
      if (rescheduleStart >= rescheduleEnd) {
        setError('End time must be after start time.');
        return;
      }
      const proposedStartIso = `${plannerDate}T${rescheduleStart}:00`;
      const proposedEndIso = `${plannerDate}T${rescheduleEnd}:00`;
      
      new_start_time = proposedStartIso;
      new_due_date = proposedEndIso;
    }

    onSubmit({
      status,
      missed_reason_id: missedReasonId || null,
      alternate_activity_id: alternateActivityId || null,
      notes: notes || null,
      new_start_time,
      new_due_date
    });
  };

  const showReason = status === 'not_done' && task.requires_reason;
  const showAlternate = status === 'not_done' && task.allows_alternate;

  return (
    <div style={{...styles.modalOverlay, display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.5)', position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', zIndex: 1000}}>
      <div style={{...styles.panel, width: '400px', maxWidth: '90%'}}>
        <h2>Check-in: {task.title}</h2>
        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Status
            <select
              style={styles.input}
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="completed">✅ Done</option>
              <option value="not_done">❌ Not Done</option>
              <option value="partial">🌓 Partial</option>
              <option value="rescheduled">📅 Rescheduled</option>
              <option value="in_progress">🔄 In Progress</option>
              <option value="pending">⏳ Pending</option>
            </select>
          </label>

          {error && <div style={{ color: '#b91c1c', marginBottom: '1rem', fontSize: '0.875rem' }}>{error}</div>}

          {status === 'rescheduled' && (
            <div style={{ display: 'flex', gap: '1rem' }}>
              <label style={styles.label}>
                Start Time
                <input
                  style={styles.input}
                  type="time"
                  value={rescheduleStart}
                  onChange={(e) => setRescheduleStart(e.target.value)}
                  required
                />
              </label>
              <label style={styles.label}>
                End Time
                <input
                  style={styles.input}
                  type="time"
                  value={rescheduleEnd}
                  onChange={(e) => setRescheduleEnd(e.target.value)}
                  required
                />
              </label>
            </div>
          )}

          {showReason && (
            <label style={styles.label}>
              Reason for missing
              <select
                style={styles.input}
                value={missedReasonId}
                onChange={(e) => setMissedReasonId(e.target.value)}
                required={task.requires_reason}
              >
                <option value="">-- Select a reason --</option>
                {reasons.map(r => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </select>
            </label>
          )}

          {showAlternate && (
            <label style={styles.label}>
              Alternate Activity
              <select
                style={styles.input}
                value={alternateActivityId}
                onChange={(e) => setAlternateActivityId(e.target.value)}
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
            <textarea
              style={styles.textarea}
              placeholder="Any additional notes..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </label>

          <div style={styles.actions}>
            <button style={styles.primaryButton} type="submit">Submit Check-in</button>
            <button style={styles.button} type="button" onClick={onCancel}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
};
