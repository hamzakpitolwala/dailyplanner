import { useState, useEffect } from 'react';
import { userApi } from '../../api/userApi';
import { apiRequest } from '../../api/client';
import { styles } from '../../utils/styles';

export const PlannerSelection = ({ profile, onComplete }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const data = await apiRequest('/templates');
        setTemplates(data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchTemplates();
  }, []);

  const handleSelect = async (templateId) => {
    setSaving(true);
    try {
      await userApi.updateUserProfile({
        ...profile,
        active_planner_id: templateId
      });
      onComplete(templateId);
    } catch (err) {
      console.error(err);
      setSaving(false);
    }
  };

  const handleCreateNew = async () => {
    setSaving(true);
    try {
      // Create empty template
      const template = await apiRequest('/templates', {
        method: 'POST',
        body: JSON.stringify({ name: 'My New Planner', description: 'Custom manually created planner', template_tasks: [] })
      });
      await userApi.updateUserProfile({
        ...profile,
        active_planner_id: template.id
      });
      onComplete(template.id);
    } catch (err) {
      console.error(err);
      setSaving(false);
    }
  };

  if (loading) return <div>Loading AI generated planners...</div>;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      backgroundColor: '#f9fafb'
    }}>
      <div style={{ ...styles.card, width: '100%', maxWidth: 500, textAlign: 'center', padding: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.5rem', color: '#111827' }}>
          Select a Daily Planner
        </h2>
        <p style={{ color: '#4b5563', marginBottom: '2rem' }}>
          We generated a few routines based on your preferences. You can pick one or create your own from scratch!
        </p>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
          {templates.map(t => (
            <div key={t.id} style={{ ...styles.panel, textAlign: 'left', cursor: 'pointer' }} onClick={() => handleSelect(t.id)}>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#111827' }}>{t.name}</h3>
              <p style={{ margin: 0, color: '#6b7280', fontSize: '0.875rem' }}>{t.description}</p>
            </div>
          ))}
        </div>

        <button
          style={{ ...styles.button, backgroundColor: '#f3f4f6', color: '#374151', width: '100%' }}
          onClick={handleCreateNew}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Create New Manually'}
        </button>
      </div>
    </div>
  );
};
