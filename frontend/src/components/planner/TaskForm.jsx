import { styles } from '../../utils/styles';

export const TaskForm = ({ 
  taskForm, 
  setTaskForm, 
  editingTaskId, 
  onSubmit, 
  onCancel 
}) => {
  return (
    <div style={styles.panel}>
      <h2>{editingTaskId ? 'Edit Task' : 'Add Task'}</h2>
      <form onSubmit={onSubmit} style={styles.form}>
        <input
          style={styles.input}
          placeholder="Title"
          value={taskForm.title}
          onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
          required
        />
        {/* Simplified category as we might need a dropdown for actual category_ids, but for now we can leave it empty or handled by a text field if we had a category name. Since backend requires category_id, we will leave it as an advanced feature or use a placeholder dropdown if we fetched categories. For now, omit or keep simple. */}
        <div style={styles.timeGrid}>
          <label style={styles.label}>
            Start Time
            <input
              style={styles.input}
              type="time"
              value={taskForm.start_time || ''}
              onChange={(e) => setTaskForm({ ...taskForm, start_time: e.target.value })}
              required
            />
          </label>
          <label style={styles.label}>
            End Time
            <input
              style={styles.input}
              type="time"
              value={taskForm.end_time || ''}
              onChange={(e) => setTaskForm({ ...taskForm, end_time: e.target.value })}
              required
            />
          </label>
          <label style={styles.label}>
            Priority (1-5)
            <input
              style={styles.input}
              type="number"
              min="1"
              max="5"
              value={taskForm.priority}
              onChange={(e) => setTaskForm({ ...taskForm, priority: parseInt(e.target.value, 10) || 1 })}
            />
          </label>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input 
              type="checkbox"
              checked={!!taskForm.requires_reason}
              onChange={(e) => setTaskForm({ ...taskForm, requires_reason: e.target.checked })}
            />
            Require reason if missed
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input 
              type="checkbox"
              checked={!!taskForm.allows_alternate}
              onChange={(e) => setTaskForm({ ...taskForm, allows_alternate: e.target.checked })}
            />
            Allow alternate activity
          </label>
        </div>
        <textarea
          style={styles.textarea}
          placeholder="Description / Notes"
          value={taskForm.description}
          onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })}
        />
        <div style={styles.actions}>
          <button style={styles.primaryButton} type="submit">
            {editingTaskId ? 'Save Changes' : 'Add'}
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
