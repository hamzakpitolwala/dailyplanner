import { useState, useEffect, useRef, type FC } from 'react';
import { todayIso, emptyTask } from '../utils/constants';
import {
  fetchTasks,
  createTask,
  updateTask,
  deleteTask,
  postTaskCheckin
} from '../api/taskApi';
import { PlannerTimeline } from '../components/Planner/PlannerTimeline';
import { TaskForm } from '../components/Planner/TaskForm';
import { MissedCheckinsModal } from '../components/Planner/MissedCheckinsModal';
import { fetchFixedBlocks } from '../api/fixedBlockApi';
import { PlannerHeader } from '../components/Planner/PlannerHeader';

interface PlannerPageProps {
  setMessage: (msg: string) => void;
  profile: any;
  setAppView: (view: string) => void;
}

let isSyncing = false;

export const PlannerPage: FC<PlannerPageProps> = ({ setMessage, profile, setAppView }) => {
  const [tasks, setTasks] = useState<any[]>([]);
  const [plannerDate, setPlannerDate] = useState(todayIso());
  
  const [taskForm, setTaskForm] = useState(emptyTask);
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [activePlanner, setActivePlanner] = useState<any>(null);
  
  const [missedTasks, setMissedTasks] = useState<any[]>([]);
  const [fixedBlocks, setFixedBlocks] = useState<any[]>([]);

  const loadTasks = async () => {
    try {
      let allTasks = await fetchTasks();
      
      // Auto-apply active template to today to sync changes immediately
      if (profile?.active_planner_id && plannerDate === todayIso() && !isSyncing) {
        isSyncing = true;
        try {
          const { applyTemplate } = await import('../api/templateApi');
          await applyTemplate(profile.active_planner_id, plannerDate);
          // Refetch tasks after sync
          allTasks = await fetchTasks();
        } catch (syncErr) {
          console.error("Failed to sync template to planner:", syncErr);
        } finally {
          isSyncing = false;
        }
      }

      const dateTasks = allTasks.filter((t: any) => t.due_date && t.due_date.startsWith(plannerDate));
      setTasks(dateTasks);
    } catch (error: any) {
      console.error(error.message);
      setMessage(error.message);
    }
  };

  const loadFixedBlocks = async () => {
    try {
      const data = await fetchFixedBlocks();
      setFixedBlocks(data);
    } catch (error: any) {
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
    
    const handleRefresh = () => loadTasks();
    window.addEventListener('refresh-tasks', handleRefresh);
    return () => window.removeEventListener('refresh-tasks', handleRefresh);
  }, [plannerDate, profile?.active_planner_id]);

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

  const submitTask = async (event: any) => {
    event.preventDefault();
    try {
      if (taskForm.start_time >= taskForm.end_time) {
        throw new Error("End time must be after start time");
      }

      const parseTime = (str: string) => {
        const [h, m] = str.split(':').map(Number);
        return h * 60 + m;
      };

      const taskStart = parseTime(taskForm.start_time);
      const taskEnd = parseTime(taskForm.end_time);

      const dayOfWeek = new Date(plannerDate).getDay();
      const activeBlocks = fixedBlocks.filter((b: any) => b.days_of_week.includes(dayOfWeek));

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
      
      const payload: any = { ...taskForm, start_time, due_date };
      if (payload.category_id === '') {
        payload.category_id = null;
      }
      
      if (editingTaskId) {
        await updateTask(editingTaskId, payload);
        setMessage('Task updated');
      } else {
        await createTask(payload);
        setMessage('Task added');
      }
      setTaskForm(emptyTask);
      setEditingTaskId(null);
      setShowTaskForm(false);
      await loadTasks();
    } catch (error: any) {
      setMessage(error.message);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    try {
      await deleteTask(taskId);
      setMessage('Task deleted');
      await loadTasks();
    } catch (error: any) {
      setMessage(error.message);
    }
  };

  const startEditTask = (task: any) => {
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

  const handleCheckin = async (taskId: string, checkinData: any) => {
    try {
      const { new_start_time, new_due_date, ...restCheckin } = checkinData;
      const updates: any = {};
      if (new_start_time) updates.start_time = new_start_time;
      if (new_due_date) updates.due_date = new_due_date;
      
      if (Object.keys(updates).length > 0) {
        await updateTask(taskId, updates);
      }
      await postTaskCheckin(taskId, restCheckin);
      setMessage(`Task status: ${restCheckin.status.replace('_', ' ')}`);
      await loadTasks();
    } catch (error: any) {
      setMessage(error.message);
    }
  };

  const handleAddToTemplate = async (task: any) => {
    if (!activePlanner) {
      setMessage("No active template selected.");
      return;
    }
    try {
      const { createTemplateTask } = await import('../api/templateApi');
      
      const formatTimeLocal = (isoString: string) => {
        if (!isoString) return null;
        return isoString.split('T')[1].substring(0, 8);
      };
      
      const taskStart = formatTimeLocal(task.start_time);
      const taskEnd = formatTimeLocal(task.due_date);
      
      const parseTime = (str: string) => {
        if (!str) return 0;
        const [h, m] = str.split(':').map(Number);
        return h * 60 + m;
      };
      
      const duration = taskStart && taskEnd ? (parseTime(taskEnd) - parseTime(taskStart)) : 60;
      
      const payload = {
        title: task.title,
        description: task.description,
        target_time: taskStart,
        duration_minutes: duration,
        priority: task.priority || 1,
        subtasks: task.subtasks || []
      };
      
      const newTemplateTask = await createTemplateTask(activePlanner.id, payload);
      
      await updateTask(task.id, {
        source_template_name: activePlanner.name,
        source_template_task_id: newTemplateTask.id
      });
      
      setMessage(`Task added to template "${activePlanner.name}"!`);
      await loadTasks();
    } catch (err: any) {
      setMessage(err.message);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden relative">
      {missedTasks.length > 0 && (
        <MissedCheckinsModal
          tasks={missedTasks}
          onComplete={() => setMissedTasks([])}
          setMessage={setMessage}
        />
      )}

      {/* Modern Header Section */}
      <PlannerHeader 
        plannerDate={plannerDate}
        setPlannerDate={setPlannerDate}
        onAddTask={() => { setTaskForm(emptyTask); setShowTaskForm(true); }}
        activePlannerName={activePlanner?.name}
      />

      {/* Task Form Modal */}
      {showTaskForm && (
        <div className="fixed inset-0 bg-zinc-900/40 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-6 border-b border-zinc-100 flex items-center justify-between">
              <h3 className="text-xl font-bold text-zinc-800">
                {editingTaskId ? 'Edit Task' : 'Add Task'}
              </h3>
            </div>
            <div className="p-6 overflow-y-auto">
              <TaskForm
                taskForm={taskForm}
                setTaskForm={setTaskForm}
                editingTaskId={editingTaskId}
                onSubmit={submitTask}
                onCancel={cancelEditTask}
              />
            </div>
          </div>
        </div>
      )}

      {/* Timeline Workspace */}
      <section className="flex-1 overflow-hidden relative px-6 pb-6">
        <div className="absolute inset-0 bg-card shadow-sm border border-border m-6 mt-0 rounded-2xl overflow-hidden flex flex-col">
          <PlannerTimeline
            tasks={tasks}
            fixedBlocks={fixedBlocks}
            plannerDate={plannerDate}
            editTask={startEditTask}
            deleteTask={handleDeleteTask}
            onCheckin={handleCheckin}
            onAddToTemplate={handleAddToTemplate}
            setMessage={setMessage}
          />
        </div>
      </section>
    </div>
  );
};
