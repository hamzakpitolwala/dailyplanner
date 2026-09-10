import { useState, useEffect } from 'react';
import { styles } from '../../utils/styles';
import { fetchFixedBlocks, createFixedBlock, updateFixedBlock, deleteFixedBlock } from '../../api/fixedBlockApi';
import { useTemplates } from '../../contexts/TemplateContext';

const DAYS_OF_WEEK = [
  { value: 1, label: 'Mon' },
  { value: 2, label: 'Tue' },
  { value: 3, label: 'Wed' },
  { value: 4, label: 'Thu' },
  { value: 5, label: 'Fri' },
  { value: 6, label: 'Sat' },
  { value: 0, label: 'Sun' }
];

export const FixedBlockManager = ({ setMessage }) => {
  const [blocks, setBlocks] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    start_time: '08:00',
    end_time: '17:00',
    days_of_week: [1, 2, 3, 4, 5],
    apply_all: true,
    template_ids: []
  });
  const [editingId, setEditingId] = useState(null);
  const { templates } = useTemplates();

  const loadBlocks = async () => {
    try {
      const data = await fetchFixedBlocks();
      setBlocks(data || []);
    } catch (error) {
      setMessage(error.message);
    }
  };

  useEffect(() => {
    loadBlocks();
  }, []);

  const handleDayToggle = (dayValue) => {
    setFormData(prev => {
      const days = [...prev.days_of_week];
      if (days.includes(dayValue)) {
        return { ...prev, days_of_week: days.filter(d => d !== dayValue) };
      } else {
        return { ...prev, days_of_week: [...days, dayValue] };
      }
    });
  };

  const handleTemplateToggle = (templateId) => {
    setFormData(prev => {
      const ids = [...prev.template_ids];
      if (ids.includes(templateId)) {
        return { ...prev, template_ids: ids.filter(id => id !== templateId) };
      } else {
        return { ...prev, template_ids: [...ids, templateId] };
      }
    });
  };

  const submitBlock = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    if (formData.start_time >= formData.end_time) {
      setMessage('End time must be after start time.');
      return;
    }
    try {
      if (editingId) {
        await updateFixedBlock(editingId, formData);
        setMessage('Fixed block updated.');
      } else {
        await createFixedBlock(formData);
        setMessage('Fixed block created.');
      }
      setFormData({
        name: '',
        start_time: '08:00',
        end_time: '17:00',
        days_of_week: [1, 2, 3, 4, 5],
        apply_all: true,
        template_ids: []
      });
      setEditingId(null);
      await loadBlocks();
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleEdit = (block) => {
    setEditingId(block.id);
    setFormData({
      name: block.name,
      start_time: block.start_time,
      end_time: block.end_time,
      days_of_week: block.days_of_week,
      apply_all: block.apply_all,
      template_ids: block.template_ids || []
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setFormData({
      name: '',
      start_time: '08:00',
      end_time: '17:00',
      days_of_week: [1, 2, 3, 4, 5],
      apply_all: true,
      template_ids: []
    });
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this fixed block?")) return;
    try {
      await deleteFixedBlock(id);
      await loadBlocks();
      setMessage('Fixed block deleted.');
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <section style={styles.panel}>
      <h2>Fixed Schedule Blocks</h2>
      <p style={styles.muted}>
        Define fixed unavailable boundaries (e.g. Office Hours, Sleep). Tasks will be scheduled around these blocks.
      </p>

      <form onSubmit={submitBlock} style={{ ...styles.form, marginBottom: '2rem' }}>
        <input 
          style={styles.input} 
          placeholder="Block Name (e.g. Office Hours)" 
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
        />
        <div style={{ display: 'flex', gap: '1rem' }}>
          <div style={{ flex: 1 }}>
            <label style={styles.label}>Start Time</label>
            <input 
              type="time"
              style={styles.input} 
              value={formData.start_time}
              onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
              required
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={styles.label}>End Time</label>
            <input 
              type="time"
              style={styles.input} 
              value={formData.end_time}
              onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
              required
            />
          </div>
        </div>

        <div>
          <label style={styles.label}>Days of Week</label>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {DAYS_OF_WEEK.map(day => (
              <label key={day.value} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <input 
                  type="checkbox" 
                  checked={formData.days_of_week.includes(day.value)}
                  onChange={() => handleDayToggle(day.value)}
                />
                {day.label}
              </label>
            ))}
          </div>
        </div>

        <div style={{ marginTop: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'bold' }}>
            <input
              type="checkbox"
              checked={formData.apply_all}
              onChange={(e) => setFormData(prev => ({ ...prev, apply_all: e.target.checked }))}
            />
            Apply to All Templates
          </label>
        </div>

        {!formData.apply_all && (
          <div style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
            <label style={styles.label}>Select Templates</label>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {templates.map(t => (
                <label key={t.id} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <input
                    type="checkbox"
                    checked={formData.template_ids.includes(t.id)}
                    onChange={() => handleTemplateToggle(t.id)}
                  />
                  {t.name}
                </label>
              ))}
              {templates.length === 0 && <span style={styles.muted}>No templates available</span>}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button style={styles.primaryButton} type="submit">
            {editingId ? 'Update Block' : 'Create Block'}
          </button>
          {editingId && (
            <button 
              type="button" 
              style={{ ...styles.button, backgroundColor: '#f3f4f6', color: '#374151' }} 
              onClick={cancelEdit}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      <div style={styles.activityList}>
        {blocks.map(block => (
          <div key={block.id} style={{ ...styles.panel, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: '0 0 0.5rem 0' }}>{block.name}</h3>
              <p style={{ margin: 0, color: '#4b5563' }}>
                {block.start_time} - {block.end_time}
              </p>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#6b7280' }}>
                Days: {block.days_of_week.map(d => DAYS_OF_WEEK.find(x => x.value === d)?.label).join(', ')}
              </p>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#6b7280' }}>
                Templates: {block.apply_all ? 'All Templates' : (block.template_ids && block.template_ids.length > 0 ? block.template_ids.map(id => templates.find(t => t.id === id)?.name || 'Unknown').join(', ') : 'None')}
              </p>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button style={{ ...styles.button, backgroundColor: '#f3f4f6', color: '#374151' }} onClick={() => handleEdit(block)}>
                Edit
              </button>
              <button style={{ ...styles.button, backgroundColor: '#fee2e2', color: '#b91c1c' }} onClick={() => handleDelete(block.id)}>
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
