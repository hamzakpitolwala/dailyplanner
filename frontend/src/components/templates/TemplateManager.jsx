import { useState, useEffect } from 'react';
import { styles } from '../../utils/styles';
import { fetchTemplates, createTemplate, deleteTemplate, deleteTemplateTask, updateTemplateTask, createTemplateTask } from '../../api/templateApi';
import { userApi } from '../../api/userApi';
import { TaskForm } from '../Planner/TaskForm';
import { emptyTask } from '../../utils/constants';
import { Edit2, Trash2 } from 'lucide-react';

export const TemplateManager = ({ setMessage, profile, setProfile, setAppView }) => {
  const [templates, setTemplates] = useState([]);
  const [templateName, setTemplateName] = useState('');
  
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [taskForm, setTaskForm] = useState(emptyTask);
  const [activeTemplateId, setActiveTemplateId] = useState(null);
  const [editingTaskId, setEditingTaskId] = useState(null);

  const loadTemplates = async () => {
    try {
      const data = await fetchTemplates();
      setTemplates(data || []);
    } catch (error) {
      setMessage(error.message);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  const submitTemplate = async (e) => {
    e.preventDefault();
    if (!templateName.trim()) return;
    try {
      await createTemplate(templateName);
      setTemplateName('');
      await loadTemplates();
      setMessage('Template created.');
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleApplyPlanner = async (templateId) => {
    try {
      await userApi.updateUserProfile({
        ...profile,
        active_planner_id: templateId
      });
      setProfile({ ...profile, active_planner_id: templateId });
      setAppView('planner');
      setMessage('Planner applied successfully.');
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm("Are you sure you want to delete this template?")) return;
    try {
      await deleteTemplate(templateId);
      await loadTemplates();
      if (profile?.active_planner_id === templateId) {
        await userApi.updateUserProfile({ ...profile, active_planner_id: null });
        setProfile({ ...profile, active_planner_id: null });
      }
      setMessage('Template deleted.');
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleDeleteTaskFromTemplate = async (templateId, taskId) => {
    if (!window.confirm("Delete this task from the template?")) return;
    try {
      await deleteTemplateTask(templateId, taskId);
      await loadTemplates();
      setMessage('Task removed from template.');
    } catch (error) {
      setMessage(error.message);
    }
  };

  const startAddTask = (templateId) => {
    setTaskForm(emptyTask);
    setActiveTemplateId(templateId);
    setEditingTaskId(null);
    setShowTaskForm(true);
  };

  const startEditTask = (templateId, task) => {
    const formatTime = (timeStr) => timeStr ? timeStr.substring(0, 5) : '';
    let endTime = '';
    if (task.target_time && task.duration_minutes) {
      const [h, m] = task.target_time.split(':').map(Number);
      const endMins = h * 60 + m + task.duration_minutes;
      endTime = `${String(Math.floor(endMins / 60)).padStart(2, '0')}:${String(endMins % 60).padStart(2, '0')}`;
    }

    setTaskForm({
      ...emptyTask,
      title: task.title,
      description: task.description || '',
      start_time: formatTime(task.target_time),
      end_time: endTime,
      priority: task.priority || 1,
      requires_reason: task.requires_reason || false,
      allows_alternate: task.allows_alternate || false,
      subtasks: task.subtasks || []
    });
    setActiveTemplateId(templateId);
    setEditingTaskId(task.id);
    setShowTaskForm(true);
  };

  const submitTask = async (event) => {
    event.preventDefault();
    try {
      const parseTime = (str) => {
        if (!str) return 0;
        const [h, m] = str.split(':').map(Number);
        return h * 60 + m;
      };
      
      const duration = taskForm.start_time && taskForm.end_time 
        ? (parseTime(taskForm.end_time) - parseTime(taskForm.start_time)) 
        : 60;

      const payload = {
        title: taskForm.title,
        description: taskForm.description,
        target_time: taskForm.start_time ? `${taskForm.start_time}:00` : null,
        duration_minutes: duration,
        priority: taskForm.priority || 1,
        subtasks: taskForm.subtasks || []
      };

      if (editingTaskId) {
        await updateTemplateTask(activeTemplateId, editingTaskId, payload);
        setMessage('Task updated.');
      } else {
        await createTemplateTask(activeTemplateId, payload);
        setMessage('Task added to template.');
      }
      
      setShowTaskForm(false);
      await loadTemplates();
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <section style={styles.panel}>
      <h2>Planner Templates</h2>
      <p style={styles.muted}>Templates are blueprints. Applying a template sets it as your daily planner.</p>

      <form onSubmit={submitTemplate} style={{ ...styles.form, marginBottom: '2rem' }}>
        <input 
          style={styles.input} 
          placeholder="New Template Name..." 
          value={templateName}
          onChange={(e) => setTemplateName(e.target.value)}
        />
        <button style={styles.primaryButton} type="submit">Create Template</button>
      </form>

      <div style={styles.activityList}>
        {templates.map(tmpl => (
          <div key={tmpl.id} style={{ ...styles.panel, border: profile?.active_planner_id === tmpl.id ? '2px solid var(--primary)' : '1px solid var(--border)' }}>
            <div style={styles.header}>
              <h3>{tmpl.name} {profile?.active_planner_id === tmpl.id && <span style={{ color: 'var(--primary)', fontSize: '0.875rem' }}>(Active)</span>}</h3>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button style={styles.button} onClick={() => handleApplyPlanner(tmpl.id)}>
                  {profile?.active_planner_id === tmpl.id ? 'Applied' : 'Apply Planner'}
                </button>
                <button style={{ ...styles.button, backgroundColor: '#fee2e2', color: '#b91c1c' }} onClick={() => handleDeleteTemplate(tmpl.id)}>
                  Delete
                </button>
              </div>
            </div>
            
            <ul style={{ paddingLeft: '1.2rem' }}>
              {tmpl.template_tasks && tmpl.template_tasks.length > 0 ? (
                tmpl.template_tasks.map(t => (
                  <li key={t.id} style={{ marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span>{t.title} {t.target_time ? `(${t.target_time.substring(0, 5)})` : ''}</span>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button 
                          style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', padding: '0.2rem' }} 
                          onClick={() => startEditTask(tmpl.id, t)}
                          title="Edit task"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button 
                          style={{ background: 'none', border: 'none', color: '#b91c1c', cursor: 'pointer', padding: '0.2rem' }} 
                          onClick={() => handleDeleteTaskFromTemplate(tmpl.id, t.id)}
                          title="Delete task"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    {t.subtasks && t.subtasks.length > 0 && (
                      <ul style={{ paddingLeft: '1.5rem', marginTop: '0.25rem', fontSize: '0.875rem', color: 'var(--text)', opacity: 0.8 }}>
                        {t.subtasks.map((sub, idx) => (
                          <li key={idx} style={{ listStyleType: 'disc' }}>
                            {sub.title}
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))
              ) : (
                <li style={styles.muted}>No tasks in this template.</li>
              )}
            </ul>
            
            <button style={{ ...styles.smallButton, marginTop: '0.5rem' }} onClick={() => startAddTask(tmpl.id)}>
              + Add Task
            </button>
          </div>
        ))}
      </div>

      {showTaskForm && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h3 style={{ marginTop: 0 }}>Add Task to Template</h3>
              <TaskForm
                taskForm={taskForm}
                setTaskForm={setTaskForm}
                editingTaskId={editingTaskId}
                onSubmit={submitTask}
                onCancel={() => setShowTaskForm(false)}
                isTemplateMode={true}
              />
          </div>
        </div>
      )}
    </section>
  );
};
