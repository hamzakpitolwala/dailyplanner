import { useState, useEffect } from 'react';
import { styles } from '../../utils/styles';
import { fetchTemplates, createTemplate, updateTemplateStatus, createTemplateActivity } from '../../api/templateApi';

export const TemplateManager = ({ setMessage }) => {
  const [templates, setTemplates] = useState([]);
  const [templateName, setTemplateName] = useState('');

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

  const toggleTemplateInUse = async (template) => {
    try {
      await updateTemplateStatus(template.id, !template.in_use);
      await loadTemplates();
    } catch (error) {
      setMessage(error.message);
    }
  };

  const addTemplateActivity = async (templateId) => {
    try {
      await createTemplateActivity(templateId);
      await loadTemplates();
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <section style={styles.panel}>
      <h2>Planner Templates</h2>
      <p style={styles.muted}>Templates are blueprints. When marked 'Active', their activities will be copied into any empty day you open.</p>

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
          <div key={tmpl.id} style={styles.panel}>
            <div style={styles.header}>
              <h3>{tmpl.name} {tmpl.in_use && <span style={{ color: 'green' }}>(Active)</span>}</h3>
              <div>
                <button style={styles.smallButton} onClick={() => toggleTemplateInUse(tmpl)}>
                  {tmpl.in_use ? 'Deactivate' : 'Set Active'}
                </button>
              </div>
            </div>
            
            <ul style={{ paddingLeft: '1.2rem' }}>
              {tmpl.activities && tmpl.activities.length > 0 ? (
                tmpl.activities.map(a => (
                  <li key={a.id} style={{ marginBottom: '0.25rem' }}>
                    {a.title} {a.start_time ? `(${a.start_time})` : ''}
                  </li>
                ))
              ) : (
                <li style={styles.muted}>No activities in this template.</li>
              )}
            </ul>
            
            <button style={{ ...styles.smallButton, marginTop: '0.5rem' }} onClick={() => addTemplateActivity(tmpl.id)}>
              + Add Mock Activity
            </button>
          </div>
        ))}
      </div>
    </section>
  );
};
