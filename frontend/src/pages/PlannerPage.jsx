import { useState, useEffect } from 'react';
import { styles } from '../utils/styles';
import { todayIso, emptyTask } from '../utils/constants';
import {
  fetchTasks,
  createTask,
  updateTask,
  deleteTask,
  postTaskCheckin
} from '../api/taskApi';
import { PlannerGrid } from '../components/planner/PlannerGrid';
import { TaskForm } from '../components/planner/TaskForm';
import { MissedCheckinsModal } from '../components/planner/MissedCheckinsModal';
import { fetchFixedBlocks } from '../api/fixedBlockApi';

export const PlannerPage = ({ setMessage, profile, setAppView }) => {
  const [tasks, setTasks] = useState([]);
  const [plannerDate, setPlannerDate] = useState(todayIso());
  
  const [taskForm, setTaskForm] = useState(emptyTask);
  const [editingTaskId, setEditingTaskId] = useState(null);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [activePlanner, setActivePlanner] = useState(null);
  
  const [missedTasks, setMissedTasks] = useState([]);
  const [fixedBlocks, setFixedBlocks] = useState([]);

  const loadTasks = async () => {
    try {
      const allTasks = await fetchTasks();
      const dateTasks = allTasks.filter(t => t.due_date && t.due_date.startsWith(plannerDate));
      setTasks(dateTasks);
    } catch (error) {
      console.error(error.message);
      setMessage(error.message);
    }
  };

  const loadFixedBlocks = async () => {
    try {
      const data = await fetchFixedBlocks();
      setFixedBlocks(data);
    } catch (error) {
      console.error(error.message);
    }
  };

  const loadPlanner = async () => {
    if (!profile?.active_planner_id) return;
    try {
      const res = await fetch(`/templates/${profile.active_planner_id}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (res.ok) {
        const data = await res.json();
        setActivePlanner(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadTasks();
    loadFixedBlocks();
  }, [plannerDate]);

  useEffect(() => {
    loadPlanner();
  }, [profile?.active_planner_id]);

  useEffect(() => {
    const checkMissed = async () => {
      try {
        const res = await fetch('/tasks/missed-checkins', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (res.ok) {
          const data = await res.json();
          if (data && data.length > 0) {
            setMissedTasks(data);
          }
        }
      } catch (err) {
        console.error(err);
      }
    };
    checkMissed();
  }, []);

  const submitTask = async (event) => {
    event.preventDefault();
    try {
      if (taskForm.start_time >= taskForm.end_time) {
        throw new Error("End time must be after start time");
      }

      const parseTime = (str) => {
        const [h, m] = str.split(':').map(Number);
        return h * 60 + m;
      };

      const taskStart = parseTime(taskForm.start_time);
      const taskEnd = parseTime(taskForm.end_time);

      const dayOfWeek = new Date(plannerDate).getDay();
      const activeBlocks = fixedBlocks.filter(b => b.days_of_week.includes(dayOfWeek));

      for (let block of activeBlocks) {
        const blockStart = parseTime(block.start_time);
        const blockEnd = parseTime(block.end_time);

        // Check if task overlaps with block
        const overlaps = taskStart < blockEnd && taskEnd > blockStart;
        if (overlaps) {
          // It must be entirely inside the block
          const completelyInside = taskStart >= blockStart && taskEnd <= blockEnd;
          if (!completelyInside) {
            throw new Error(`Task partially overlaps with unavailable block "${block.name}". Please schedule completely inside or outside.`);
          }
        }
      }

      let start_time = `${plannerDate}T${taskForm.start_time}:00`;
      let due_date = `${plannerDate}T${taskForm.end_time}:00`;
      
      const payload = { ...taskForm, start_time, due_date };
      if (payload.category_id === '') {
        payload.category_id = null;
      }
      
      if (editingTaskId) {
        await updateTask(editingTaskId, payload);
        setMessage('Task updated');
      } else {
        // Create the task in the active template so it persists permanently!
        if (activePlanner) {
           await fetch(`/templates/${activePlanner.id}/tasks`, {
             method: 'POST',
             headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' },
             body: JSON.stringify({
               title: payload.title,
               description: payload.description,
               target_time: taskForm.due_time ? `${taskForm.due_time}:00` : null
             })
           });
        }
        await createTask(payload);
        setMessage('Task added');
      }
      setTaskForm(emptyTask);
      setEditingTaskId(null);
      setShowTaskForm(false);
      await loadTasks();
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      await deleteTask(taskId);
      setMessage('Task deleted');
      await loadTasks();
    } catch (error) {
      setMessage(error.message);
    }
  };

  const startEditTask = (task) => {
    let start_time = '';
    let end_time = '';
    if (task.start_time) {
      start_time = task.start_time.split('T')[1]?.substring(0, 5) || '';
    }
    if (task.due_date) {
      end_time = task.due_date.split('T')[1]?.substring(0, 5) || '';
    }
    setTaskForm({ ...task, start_time, end_time });
    setEditingTaskId(task.id);
    setShowTaskForm(true);
  };

  const cancelEditTask = () => {
    setTaskForm(emptyTask);
    setEditingTaskId(null);
    setShowTaskForm(false);
  };

  const handleCheckin = async (taskId, checkinData) => {
    try {
      const { new_start_time, new_due_date, ...restCheckin } = checkinData;
      const updates = {};
      if (new_start_time) updates.start_time = new_start_time;
      if (new_due_date) updates.due_date = new_due_date;
      
      if (Object.keys(updates).length > 0) {
        await updateTask(taskId, updates);
      }
      await postTaskCheckin(taskId, restCheckin);
      setMessage(`Task status: ${restCheckin.status.replace('_', ' ')}`);
      await loadTasks();
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <>
      {missedTasks.length > 0 && (
        <MissedCheckinsModal
          tasks={missedTasks}
          onComplete={() => setMissedTasks([])}
          setMessage={setMessage}
        />
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', backgroundColor: '#fff', padding: '1rem', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.25rem', color: '#111827' }}>
            {activePlanner ? activePlanner.name : 'Daily Planner'}
          </h2>
          <p style={{ margin: 0, color: '#6b7280', fontSize: '0.875rem' }}>Active Template</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            style={{ ...styles.input, width: '140px', marginBottom: 0 }}
            type="date"
            value={plannerDate}
            onChange={(e) => setPlannerDate(e.target.value)}
          />
          <button style={{ ...styles.button, backgroundColor: '#f3f4f6', color: '#374151' }} onClick={() => setAppView('templates')}>
            Manage Template
          </button>
          <button style={styles.button} onClick={() => { setTaskForm(emptyTask); setShowTaskForm(true); }}>
            + Add Task
          </button>
        </div>
      </div>

      {showTaskForm && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ ...styles.card, width: '100%', maxWidth: 500 }}>
            <h3 style={{ marginTop: 0 }}>{editingTaskId ? 'Edit Task' : 'Add Task'}</h3>
            <TaskForm
              taskForm={taskForm}
              setTaskForm={setTaskForm}
              editingTaskId={editingTaskId}
              onSubmit={submitTask}
              onCancel={cancelEditTask}
            />
          </div>
        </div>
      )}

      {/* Tasks List / Timeline */}
      <section className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <PlannerGrid
          tasks={tasks}
          fixedBlocks={fixedBlocks}
          plannerDate={plannerDate}
          editTask={startEditTask}
          deleteTask={handleDeleteTask}
          onCheckin={handleCheckin}
          setMessage={setMessage}
        />
      </section>
    </>
  );
};
