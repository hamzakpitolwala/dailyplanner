import { useState } from 'react';
import { Badge } from '../ui/Badge';
import { styles } from '../../utils/styles';
import { TASK_STATUSES } from '../../utils/constants';
import { TaskCheckinModal } from './TaskCheckinModal';

export const TaskItem = ({
  task,
  tasks,
  plannerDate,
  editTask,
  deleteTask,
  onCheckin,
  setMessage
}) => {
  const [activeCheckinStatus, setActiveCheckinStatus] = useState(null);

  const localToday = new Date().toLocaleDateString('en-CA');
  const taskDate = task.due_date ? task.due_date.split('T')[0] : '';
  const isPastDate = taskDate && taskDate < localToday;

  const isCompleted = task.status === 'completed';
  const isTerminalState = isPastDate || task.status === 'completed' || task.status === 'not_done' || task.status === 'pending_not_done' || task.status === 'partial_not_done';
  const isRescheduleDisabled = task.due_date && new Date(task.due_date) < new Date();

  let containerStyle = { ...styles.activityItem };
  if (isCompleted) containerStyle.opacity = 0.7;

  const handleStatusClick = (newStatus) => {
    if (isTerminalState) return;
    
    if (newStatus === 'rescheduled') {
      if (isRescheduleDisabled) return;
      setActiveCheckinStatus(newStatus);
    } else if (newStatus === 'not_done' && (task.requires_reason || task.allows_alternate)) {
      setActiveCheckinStatus(newStatus);
    } else {
      // Direct update
      onCheckin(task.id, { status: newStatus });
    }
  };

  const submitCheckinModal = (checkinData) => {
    onCheckin(task.id, checkinData);
    setActiveCheckinStatus(null);
  };

  return (
    <article style={containerStyle}>
      <div style={{ flex: 1, textDecoration: isCompleted ? 'line-through' : 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <strong>{task.title}</strong>
          <Badge status={task.status} />
          {task.priority && (
            <span style={{ fontSize: '0.8rem', color: '#b54708', background: '#ffead5', padding: '0.1rem 0.4rem', borderRadius: 4 }}>
              Priority: {task.priority}
            </span>
          )}
        </div>
        
        {task.due_date && (
          <p style={styles.muted}>
            Due: {task.due_date.split('T')[1]?.substring(0, 5)}
          </p>
        )}
        
        {task.description && <p>{task.description}</p>}

        {/* Status toggles */}
        {!isTerminalState && (
          <div style={{ ...styles.actions, marginTop: '0.5rem' }}>
            {TASK_STATUSES.map((s) => (
              <button
                key={s.value}
                style={{
                  ...styles.smallButton,
                  borderColor: (s.value === 'rescheduled' && isRescheduleDisabled) ? '#d1d5db' : s.color,
                  color: task.status === s.value ? '#fff' : ((s.value === 'rescheduled' && isRescheduleDisabled) ? '#9ca3af' : s.color),
                  background: task.status === s.value ? s.color : ((s.value === 'rescheduled' && isRescheduleDisabled) ? '#f3f4f6' : '#fff'),
                  cursor: (s.value === 'rescheduled' && isRescheduleDisabled) ? 'not-allowed' : 'pointer'
                }}
                disabled={s.value === 'rescheduled' && isRescheduleDisabled}
                onClick={() => handleStatusClick(s.value)}
              >
                {s.label}
              </button>
            ))}
          </div>
        )}
        
        {/* Render Checkin Reason if available */}
        {isTerminalState && task.checkins && task.checkins.length > 0 && (
          <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: '#f9fafb', borderRadius: '4px', fontSize: '0.875rem' }}>
            {task.checkins[task.checkins.length - 1].missed_reason && (
              <p style={{ margin: 0 }}><strong>Reason:</strong> {task.checkins[task.checkins.length - 1].missed_reason.name}</p>
            )}
            {task.checkins[task.checkins.length - 1].alternate_activity && (
              <p style={{ margin: 0 }}><strong>Alternate:</strong> {task.checkins[task.checkins.length - 1].alternate_activity.name}</p>
            )}
            {task.checkins[task.checkins.length - 1].notes && (
              <p style={{ margin: 0, marginTop: '0.25rem' }}><strong>Notes:</strong> {task.checkins[task.checkins.length - 1].notes}</p>
            )}
          </div>
        )}
      </div>

      {!isPastDate && (
        <div style={styles.actions}>
          <button style={styles.button} onClick={() => editTask(task)}>Edit</button>
          <button style={styles.dangerButton} onClick={() => deleteTask(task.id)}>Delete</button>
        </div>
      )}

      {activeCheckinStatus && (
        <TaskCheckinModal
          task={task}
          tasks={tasks}
          plannerDate={plannerDate}
          initialStatus={activeCheckinStatus}
          onSubmit={submitCheckinModal}
          onCancel={() => setActiveCheckinStatus(null)}
          setMessage={setMessage}
        />
      )}
    </article>
  );
};
