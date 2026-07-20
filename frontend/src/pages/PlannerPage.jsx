import { useState, useEffect } from 'react';
import { styles } from '../utils/styles';
import { todayIso, emptyActivity } from '../utils/constants';
import { 
  fetchTodayPlanner, 
  updatePlannerInfo, 
  createActivity, 
  updateActivity, 
  deleteActivity, 
  fetchActivityHistory, 
  submitActivityCheckin 
} from '../api/plannerApi';
import { ActivityList } from '../components/planner/ActivityList';
import { ActivityForm } from '../components/planner/ActivityForm';
import { CheckinModal } from '../components/planner/CheckinModal';

export const PlannerPage = ({ setMessage }) => {
  const [planner, setPlanner] = useState(null);
  const [plannerDate, setPlannerDate] = useState(todayIso());
  const [plannerTitle, setPlannerTitle] = useState('');
  const [plannerNotes, setPlannerNotes] = useState('');
  
  const [activityForm, setActivityForm] = useState(emptyActivity);
  const [editingActivityId, setEditingActivityId] = useState(null);

  // Check-in modal state
  const [checkinModal, setCheckinModal] = useState(null);
  const [checkinNotes, setCheckinNotes] = useState('');
  const [reasonCode, setReasonCode] = useState('');
  const [reasonText, setReasonText] = useState('');
  const [altDescription, setAltDescription] = useState('');
  const [altCategory, setAltCategory] = useState('');
  const [targetDate, setTargetDate] = useState('');

  // History state
  const [historyActivityId, setHistoryActivityId] = useState(null);
  const [checkinHistory, setCheckinHistory] = useState([]);

  const loadPlanner = async (date) => {
    try {
      const data = await fetchTodayPlanner(date);
      setPlanner(data);
      setPlannerTitle(data.title);
      setPlannerNotes(data.notes || '');
    } catch (error) {
      setMessage(error.message);
    }
  };

  useEffect(() => {
    loadPlanner(plannerDate);
  }, [plannerDate]);

  const handleUpdatePlannerInfo = async () => {
    try {
      const data = await updatePlannerInfo(plannerDate, plannerTitle, plannerNotes);
      setPlanner(data);
      setMessage('Planner updated');
    } catch (error) {
      setMessage(error.message);
    }
  };

  const submitActivity = async (event) => {
    event.preventDefault();
    try {
      if (editingActivityId) {
        await updateActivity(editingActivityId, activityForm);
        setMessage('Activity updated');
      } else {
        await createActivity(planner.id, activityForm);
        setMessage('Activity added');
      }
      setActivityForm(emptyActivity);
      setEditingActivityId(null);
      await loadPlanner(plannerDate);
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleDeleteActivity = async (activityId) => {
    try {
      await deleteActivity(activityId);
      setMessage('Activity deleted');
      await loadPlanner(plannerDate);
    } catch (error) {
      setMessage(error.message);
    }
  };

  const startEditActivity = (activity) => {
    setActivityForm({ ...activity });
    setEditingActivityId(activity.id);
  };

  const cancelEditActivity = () => {
    setActivityForm(emptyActivity);
    setEditingActivityId(null);
  };

  const openCheckinModal = (activity, statusValue) => {
    if (statusValue === 'not_done' || statusValue === 'rescheduled') {
      setCheckinModal({ activity, status: statusValue });
      setCheckinNotes('');
      setReasonCode('');
      setReasonText('');
      setAltDescription('');
      setAltCategory('');
      
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      setTargetDate(tomorrow.toISOString().slice(0, 10));
    } else {
      executeCheckin(activity.id, statusValue, '');
    }
  };

  const executeCheckin = async (activityId, status, notes, missedReason = null, alternate = null, tgtDate = null) => {
    try {
      await submitActivityCheckin(activityId, status, notes, missedReason, alternate, tgtDate);
      setMessage(`Checked in: ${status.replace('_', ' ')}`);
      setCheckinModal(null);
      await loadPlanner(plannerDate);
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleCheckinModalSubmit = (event) => {
    event.preventDefault();
    const { activity, status } = checkinModal;

    const missedReason = reasonCode
      ? { reason_code: reasonCode, free_text: reasonText || null }
      : null;

    const alternate = altDescription
      ? { description: altDescription, category: altCategory || null }
      : null;

    executeCheckin(activity.id, status, checkinNotes, missedReason, alternate, targetDate);
  };

  const loadCheckinHistory = async (activityId) => {
    if (historyActivityId === activityId) {
      setHistoryActivityId(null);
      setCheckinHistory([]);
      return;
    }
    try {
      const data = await fetchActivityHistory(activityId);
      setCheckinHistory(data);
      setHistoryActivityId(activityId);
    } catch (error) {
      setMessage(error.message);
    }
  };

  if (!planner) {
    return <p>Loading planner...</p>;
  }

  return (
    <>
      <section style={styles.workspace}>
        {/* Planner Info */}
        <div style={styles.panel}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0 }}>Planner</h2>
            <input
              style={{ ...styles.input, width: '150px' }}
              type="date"
              value={plannerDate}
              onChange={(e) => setPlannerDate(e.target.value)}
            />
          </div>
          <div style={styles.form}>
            <input
              style={styles.input}
              placeholder="Daily Objective / Title"
              value={plannerTitle}
              onChange={(e) => setPlannerTitle(e.target.value)}
            />
            <textarea
              style={styles.textarea}
              placeholder="Overall daily notes..."
              value={plannerNotes}
              onChange={(e) => setPlannerNotes(e.target.value)}
            />
            <button style={styles.button} onClick={handleUpdatePlannerInfo}>
              Save Planner Info
            </button>
          </div>
        </div>

        {/* Add/Edit Activity Form */}
        <ActivityForm 
          activityForm={activityForm}
          setActivityForm={setActivityForm}
          editingActivityId={editingActivityId}
          onSubmit={submitActivity}
          onCancel={cancelEditActivity}
        />
      </section>

      {/* Activities List */}
      <section style={styles.panel}>
        <h2 style={styles.subheading}>Planned Activities</h2>
        <ActivityList 
          activities={planner.activities}
          plannerDate={plannerDate}
          openCheckinModal={openCheckinModal}
          editActivity={startEditActivity}
          deleteActivity={handleDeleteActivity}
          historyActivityId={historyActivityId}
          checkinHistory={checkinHistory}
          loadCheckinHistory={loadCheckinHistory}
        />
      </section>

      <CheckinModal 
        checkinModal={checkinModal}
        setCheckinModal={setCheckinModal}
        checkinNotes={checkinNotes}
        setCheckinNotes={setCheckinNotes}
        reasonCode={reasonCode}
        setReasonCode={setReasonCode}
        reasonText={reasonText}
        setReasonText={setReasonText}
        altDescription={altDescription}
        setAltDescription={setAltDescription}
        altCategory={altCategory}
        setAltCategory={setAltCategory}
        targetDate={targetDate}
        setTargetDate={setTargetDate}
        handleCheckinModalSubmit={handleCheckinModalSubmit}
      />
    </>
  );
};
