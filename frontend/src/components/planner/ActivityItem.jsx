import { Badge } from '../ui/Badge';
import { styles } from '../../utils/styles';
import { CHECKIN_STATUSES } from '../../utils/constants';

export const ActivityItem = ({
  activity,
  plannerDate,
  openCheckinModal,
  editActivity,
  deleteActivity,
  historyActivityId,
  checkinHistory,
  loadCheckinHistory
}) => {
  const isDone = activity.status === 'done';
  const isNotDone = activity.status === 'not_done';
  const isTerminal = ['done', 'not_done', 'rescheduled', 'cancelled'].includes(activity.status);

  let containerStyle = { ...styles.activityItem };
  if (isDone) containerStyle.opacity = 0.7;
  if (isNotDone) containerStyle.background = '#fdeded';

  return (
    <article style={containerStyle}>
      <div style={{ flex: 1, textDecoration: isDone ? 'line-through' : 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <strong style={{ color: isNotDone ? '#b42318' : 'inherit' }}>{activity.title}</strong>
          <Badge status={activity.status} />
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
            const allowedStates = {
              planned: ['in_progress', 'partial', 'done', 'not_done', 'rescheduled', 'cancelled'],
              in_progress: ['partial', 'done', 'not_done', 'rescheduled', 'cancelled'],
              partial: ['done', 'not_done', 'rescheduled', 'cancelled'],
              done: [],
              not_done: [],
              rescheduled: [],
              cancelled: [],
            };
            const isAllowed = (allowedStates[activity.status] || []).includes(s.value);

            let isPastEndTime = false;
            if (activity.end_time && plannerDate) {
              const now = new Date();
              const todayStr = now.toISOString().slice(0, 10);
              if (plannerDate < todayStr) {
                isPastEndTime = true;
              } else if (plannerDate === todayStr) {
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
                <span><Badge status={ci.new_state} /></span>
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
};
