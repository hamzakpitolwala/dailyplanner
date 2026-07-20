import { styles } from '../../utils/styles';

export const ActivityForm = ({ 
  activityForm, 
  setActivityForm, 
  editingActivityId, 
  onSubmit, 
  onCancel 
}) => {
  return (
    <div style={styles.panel}>
      <h2>{editingActivityId ? 'Edit Activity' : 'Add Activity'}</h2>
      <form onSubmit={onSubmit} style={styles.form}>
        <input
          style={styles.input}
          placeholder="Title"
          value={activityForm.title}
          onChange={(e) => setActivityForm({ ...activityForm, title: e.target.value })}
          required
        />
        <input
          style={styles.input}
          placeholder="Category (e.g. work, health, learning)"
          value={activityForm.category}
          onChange={(e) => setActivityForm({ ...activityForm, category: e.target.value })}
        />
        <div style={styles.timeGrid}>
          <label style={styles.label}>
            Start Time
            <input
              style={styles.input}
              type="time"
              value={activityForm.start_time}
              onChange={(e) => setActivityForm({ ...activityForm, start_time: e.target.value })}
            />
          </label>
          <label style={styles.label}>
            End Time
            <input
              style={styles.input}
              type="time"
              value={activityForm.end_time}
              onChange={(e) => setActivityForm({ ...activityForm, end_time: e.target.value })}
            />
          </label>
        </div>
        <textarea
          style={styles.textarea}
          placeholder="Description / Notes"
          value={activityForm.description}
          onChange={(e) => setActivityForm({ ...activityForm, description: e.target.value })}
        />
        <div style={styles.actions}>
          <button style={styles.primaryButton} type="submit">
            {editingActivityId ? 'Save Changes' : 'Add'}
          </button>
          <button
            style={styles.button}
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};
