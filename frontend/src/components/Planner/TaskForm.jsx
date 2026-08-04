import { styles } from '../../utils/styles';
import { Trash2 } from 'lucide-react';

export const TaskForm = ({ 
  taskForm, 
  setTaskForm, 
  editingTaskId, 
  onSubmit, 
  onCancel,
  isTemplateMode = false
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

        <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <h4 style={{ margin: '0 0 0.5rem 0', color: '#334155' }}>Sub-tasks</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
            {(taskForm.subtasks || []).map((sub, index) => (
              <div key={sub.id || index} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="checkbox"
                  checked={sub.is_completed}
                  onChange={async (e) => {
                    const checked = e.target.checked;
                    if (!isTemplateMode && editingTaskId && sub.id && !String(sub.id).startsWith('temp_')) {
                      const { updateSubtask } = await import('../../api/taskApi');
                      try {
                        await updateSubtask(editingTaskId, sub.id, { is_completed: checked });
                      } catch (err) {
                        console.error(err);
                        return;
                      }
                    }
                    setTaskForm({
                      ...taskForm,
                      subtasks: (taskForm.subtasks || []).map((s, i) => i === index ? { ...s, is_completed: checked } : s)
                    });
                  }}
                  style={{ width: '16px', height: '16px' }}
                />
                <span style={{ flex: 1, textDecoration: sub.is_completed ? 'line-through' : 'none', color: sub.is_completed ? '#94a3b8' : '#0f172a' }}>
                  {sub.title}
                </span>
                <button
                  type="button"
                  onClick={async () => {
                    if (!window.confirm('Delete sub-task?')) return;
                    if (!isTemplateMode && editingTaskId && sub.id && !String(sub.id).startsWith('temp_')) {
                      const { deleteSubtask } = await import('../../api/taskApi');
                      try {
                        await deleteSubtask(editingTaskId, sub.id);
                      } catch (err) {
                        console.error(err);
                        return;
                      }
                    }
                    setTaskForm({
                      ...taskForm,
                      subtasks: (taskForm.subtasks || []).filter((s, i) => i !== index)
                    });
                  }}
                  style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  title="Delete sub-task"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
            {(!taskForm.subtasks || taskForm.subtasks.length === 0) && (
              <span style={{ fontSize: '0.85rem', color: '#64748b' }}>No sub-tasks added yet.</span>
            )}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              id="new-subtask-title"
              style={{ ...styles.input, marginBottom: 0, flex: 1 }}
              placeholder="New sub-task title..."
              onKeyDown={async (e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  const title = e.target.value.trim();
                  if (!title) return;
                  e.target.value = '';
                  
                  let newSub = { id: `temp_${Date.now()}`, title, is_completed: false };
                  
                  if (!isTemplateMode && editingTaskId) {
                    const { createSubtask } = await import('../../api/taskApi');
                    try {
                      newSub = await createSubtask(editingTaskId, title);
                    } catch (err) {
                      console.error(err);
                      return;
                    }
                  }
                  setTaskForm({
                    ...taskForm,
                    subtasks: [...(taskForm.subtasks || []), newSub]
                  });
                }
              }}
            />
            <button
              type="button"
              style={styles.button}
              onClick={async () => {
                const input = document.getElementById('new-subtask-title');
                const title = input.value.trim();
                if (!title) return;
                input.value = '';
                
                let newSub = { id: `temp_${Date.now()}`, title, is_completed: false };
                
                if (!isTemplateMode && editingTaskId) {
                  const { createSubtask } = await import('../../api/taskApi');
                  try {
                    newSub = await createSubtask(editingTaskId, title);
                  } catch (err) {
                    console.error(err);
                    return;
                  }
                }
                setTaskForm({
                  ...taskForm,
                  subtasks: [...(taskForm.subtasks || []), newSub]
                });
              }}
            >
              Add
            </button>
          </div>
        </div>

        <div style={{ ...styles.actions, marginTop: '1rem' }}>
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
