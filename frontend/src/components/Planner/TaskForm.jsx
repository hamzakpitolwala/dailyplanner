import { Trash2, Plus, Clock, FileText, CheckCircle2, Calendar } from 'lucide-react';
import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

/**
 * @param {Object} props
 * @param {any} [props.initialTask]
 * @param {any} props.onSubmit
 * @param {any} props.onCancel
 * @param {boolean} [props.isTemplateMode]
 * @param {string|null} [props.error]
 */
export const TaskForm = ({ 
  initialTask, 
  onSubmit, 
  onCancel,
  isTemplateMode = false,
  error = null
}) => {
  const [formData, setFormData] = useState(initialTask || {});

  // Update internal state if initialTask changes (e.g. switching from Add to Edit)
  useEffect(() => {
    setFormData(initialTask || {});
  }, [initialTask]);

  /**
   * Handle Submit.
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="bg-card border border-border rounded-2xl shadow-lg p-6 w-full text-text relative"
    >
      <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
        {formData.id ? 'Edit Task' : 'Add New Task'}
      </h2>

      {!formData.id && (
        <div className="flex bg-zinc-100 dark:bg-zinc-800/80 p-1 rounded-xl mb-6">
          <button
            type="button"
            onClick={() => setFormData({ ...formData, source: 'manual' })}
            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${(!formData.source || formData.source === 'manual') ? 'bg-white dark:bg-zinc-700 shadow-sm text-text' : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'}`}
          >
            Standard Task
          </button>
          <button
            type="button"
            onClick={() => setFormData({ ...formData, source: 'calendar' })}
            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${formData.source === 'calendar' ? 'bg-white dark:bg-zinc-700 shadow-sm text-text' : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'}`}
          >
            Google Calendar Task
          </button>
        </div>
      )}
      
      {formData.source === 'calendar' && (
        <div className="mb-4 p-3 rounded-xl bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300 text-xs font-semibold flex items-center gap-2">
          <Calendar className="w-4 h-4 text-blue-600 flex-shrink-0" />
          <span>{formData.id ? 'Linked to Google Calendar — saving will sync changes to your Google Calendar event.' : 'This task will be automatically created as a new event in your Google Calendar.'}</span>
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm font-medium flex items-center gap-2">
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        
        {/* Title Input */}
        <div>
          <input
            className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium text-lg placeholder:font-normal"
            placeholder="What do you want to accomplish?"
            value={formData.title || ''}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            required
          />
        </div>

        {/* Grid for Times and Priority */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Start Time
            </label>
            <input
              className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              type="time"
              value={formData.start_time || ''}
              onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              End Time
            </label>
            <input
              className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              type="time"
              value={formData.end_time || ''}
              onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
              Priority (1-5)
            </label>
            <input
              className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              type="number"
              min="1"
              max="5"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value, 10) || 1 })}
            />
          </div>
        </div>
        
        {/* Checkboxes */}
        <div className="flex gap-6 p-4 bg-zinc-50 dark:bg-zinc-900/30 rounded-xl border border-border/50">
          <label className="flex items-center gap-3 cursor-pointer group">
            <input 
              type="checkbox"
              className="w-4 h-4 rounded text-primary focus:ring-primary accent-primary"
              checked={!!formData.requires_reason}
              onChange={(e) => setFormData({ ...formData, requires_reason: e.target.checked })}
            />
            <span className="text-sm font-medium group-hover:text-primary transition-colors">
              Require reason if missed
            </span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer group">
            <input 
              type="checkbox"
              className="w-4 h-4 rounded text-primary focus:ring-primary accent-primary"
              checked={!!formData.allows_alternate}
              onChange={(e) => setFormData({ ...formData, allows_alternate: e.target.checked })}
            />
            <span className="text-sm font-medium group-hover:text-primary transition-colors">
              Allow alternate activity
            </span>
          </label>
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 flex items-center gap-1">
            <FileText className="w-3 h-3" />
            Description / Notes
          </label>
          <textarea
            className="w-full bg-zinc-50 dark:bg-zinc-900/50 border border-border rounded-xl py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all min-h-[100px] resize-y"
            placeholder="Add any extra details here..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>

        {/* Sub-tasks Area */}
        <div className="p-4 bg-zinc-50 dark:bg-zinc-900/30 border border-border rounded-xl">
          <h4 className="text-sm font-bold flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-4 h-4 text-primary" />
            Sub-tasks
          </h4>
          
          <div className="space-y-2 mb-4">
            {(formData.subtasks || []).map((sub, index) => (
              <div key={sub.id || index} className="flex items-center gap-3 bg-card border border-border/50 p-2.5 rounded-lg shadow-sm group">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded text-primary focus:ring-primary accent-primary cursor-pointer"
                  checked={sub.is_completed}
                  onChange={async (e) => {
                    const checked = e.target.checked;
                    if (!isTemplateMode && formData.id && sub.id && !String(sub.id).startsWith('temp_')) {
                      const { updateSubtask } = await import('../../api/taskApi');
                      try {
                        await updateSubtask(formData.id, sub.id, { is_completed: checked });
                      } catch (err) {
                        console.error(err);
                        return;
                      }
                    }
                    setFormData({
                      ...formData,
                      subtasks: (formData.subtasks || []).map((s, i) => i === index ? { ...s, is_completed: checked } : s)
                    });
                  }}
                />
                <span className={`flex-1 text-sm transition-all ${sub.is_completed ? 'line-through text-zinc-400 dark:text-zinc-500' : 'text-text'}`}>
                  {sub.title}
                </span>
                <button
                  type="button"
                  onClick={async () => {
                    if (!window.confirm('Delete sub-task?')) return;
                    if (!isTemplateMode && formData.id && sub.id && !String(sub.id).startsWith('temp_')) {
                      const { deleteSubtask } = await import('../../api/taskApi');
                      try {
                        await deleteSubtask(formData.id, sub.id);
                      } catch (err) {
                        console.error(err);
                        return;
                      }
                    }
                    setFormData({
                      ...formData,
                      subtasks: (formData.subtasks || []).filter((s, i) => i !== index)
                    });
                  }}
                  className="p-1.5 text-zinc-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-md opacity-0 group-hover:opacity-100 transition-all"
                  title="Delete sub-task"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
            {(!formData.subtasks || formData.subtasks.length === 0) && (
              <p className="text-sm text-zinc-500 italic">No sub-tasks added yet.</p>
            )}
          </div>
          
          <div className="flex gap-2">
            <input
              id="new-subtask-title"
              className="flex-1 bg-card border border-border rounded-lg py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              placeholder="New sub-task title..."
              onKeyDown={async (e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  const title = e.target.value.trim();
                  if (!title) return;
                  e.target.value = '';
                  
                  let newSub = { id: `temp_${Date.now()}`, title, is_completed: false };
                  
                  if (!isTemplateMode && formData.id) {
                    const { createSubtask } = await import('../../api/taskApi');
                    try {
                      newSub = await createSubtask(formData.id, title);
                    } catch (err) {
                      console.error(err);
                      return;
                    }
                  }
                  setFormData({
                    ...formData,
                    subtasks: [...(formData.subtasks || []), newSub]
                  });
                }
              }}
            />
            <button
              type="button"
              className="px-3 py-2 bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 text-text text-sm font-medium rounded-lg transition-colors flex items-center justify-center"
              onClick={async () => {
                const input = document.getElementById('new-subtask-title');
                const title = input.value.trim();
                if (!title) return;
                input.value = '';
                
                let newSub = { id: `temp_${Date.now()}`, title, is_completed: false };
                
                if (!isTemplateMode && formData.id) {
                  const { createSubtask } = await import('../../api/taskApi');
                  try {
                    newSub = await createSubtask(formData.id, title);
                  } catch (err) {
                    console.error(err);
                    return;
                  }
                }
                setFormData({
                  ...formData,
                  subtasks: [...(formData.subtasks || []), newSub]
                });
              }}
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-border mt-4">
          <button
            className="px-5 py-2.5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-text text-sm font-semibold rounded-xl transition-colors"
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>
          <button 
            className="px-6 py-2.5 bg-primary hover:bg-primary-hover text-white text-sm font-semibold rounded-xl shadow-md shadow-primary/20 transition-all" 
            type="submit"
          >
            {formData.id ? 'Save Changes' : 'Add Task'}
          </button>
        </div>
      </form>
    </motion.div>
  );
};
