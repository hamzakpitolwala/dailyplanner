import { useState, useEffect } from 'react';
import { styles } from '../../utils/styles';
import { fetchFixedBlocks, createFixedBlock, deleteFixedBlock } from '../../api/fixedBlockApi';

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
    days_of_week: [1, 2, 3, 4, 5] // Default Mon-Fri
  });

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

  const submitBlock = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    if (formData.start_time >= formData.end_time) {
      setMessage('End time must be after start time.');
      return;
    }
    try {
      await createFixedBlock(formData);
      setFormData({ ...formData, name: '' }); // reset name
      await loadBlocks();
      setMessage('Fixed block created.');
    } catch (error) {
      setMessage(error.message);
    }
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

        <button style={styles.primaryButton} type="submit">Create Block</button>
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
            </div>
            <button style={{ ...styles.button, backgroundColor: '#fee2e2', color: '#b91c1c' }} onClick={() => handleDelete(block.id)}>
              Delete
            </button>
          </div>
        ))}
      </div>
    </section>
  );
};
