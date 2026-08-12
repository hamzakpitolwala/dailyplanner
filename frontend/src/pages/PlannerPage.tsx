import { useState, useEffect, useRef, type FC } from 'react';
import { todayIso, emptyTask } from '../utils/constants';
import {
  fetchTasks,
  createTask,
  updateTask,
  deleteTask,
  postTaskCheckin,
  fetchEarliestTaskDate
} from '../api/taskApi';
import { PlannerTimeline } from '../components/Planner/PlannerTimeline';
import { TaskForm } from '../components/Planner/TaskForm';
import { MissedCheckinsModal } from '../components/Planner/MissedCheckinsModal';
import { fetchFixedBlocks } from '../api/fixedBlockApi';
import { PlannerHeader } from '../components/Planner/PlannerHeader';
import { PastTemplateView } from '../components/Planner/PastTemplateView';

import { Task, PlannerTemplate, FixedBlock, UserProfile } from '../types';

interface PlannerPageProps {
  setMessage: (msg: string) => void;
  profile: UserProfile;
  setAppView: (view: string) => void;
}

const checkFixedBlockOverlap = (
  submittedTaskForm: { start_time: string, end_time: string },
  plannerDate: string,
  fixedBlocks: FixedBlock[]
) => {
  const parseTime = (str: string) => {
    const [h, m] = str.split(':').map(Number);
    return h * 60 + m;
  };

  const taskStart = parseTime(submittedTaskForm.start_time);
  const taskEnd = parseTime(submittedTaskForm.end_time);

  const dayOfWeek = new Date(plannerDate).getDay();
  const activeBlocks = fixedBlocks.filter((b) => b.days_of_week.includes(dayOfWeek));

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
};

export const PlannerPage: FC<PlannerPageProps> = ({ setMessage, profile, setAppView }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [plannerDate, setPlannerDate] = useState(todayIso());

  const [editingTaskData, setEditingTaskData] = useState<any>(emptyTask);
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [activePlanner, setActivePlanner] = useState<PlannerTemplate | null>(null);

  const [missedTasks, setMissedTasks] = useState<Task[]>([]);
  const [fixedBlocks, setFixedBlocks] = useState<FixedBlock[]>([]);
  const [earliestDate, setEarliestDate] = useState<string>(todayIso());
  const [templates, setTemplates] = useState<PlannerTemplate[]>([]);
  
  const isSyncing = useRef(false);
  const [taskFormError, setTaskFormError] = useState<string | null>(null);

  const loadTasks = async () => {
    try {
      let allTasks = await fetchTasks(plannerDate);
      console.log('Fetched tasks for', plannerDate, ':', allTasks);
      setTasks(allTasks);
    } catch (error: any) {
      console.error(error.message);
      setMessage(error.message);
    }
  };

  const loadFixedBlocks = async () => {
    try {
      const blocks = await fetchFixedBlocks();
      setFixedBlocks(blocks);
    } catch (error: any) {
      console.error("Failed to load fixed blocks", error);
    }
  };

  const loadPlanner = async () => {
    try {
      const { fetchTemplates } = await import('../api/templateApi');
      const data = await fetchTemplates();
      setTemplates(data);
    } catch (err) {
      console.error(err);
    }

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
    const syncAndLoad = async () => {
      // Auto-apply active template to today to sync changes immediately on mount or date change
      if (profile?.active_planner_id && plannerDate === todayIso() && !isSyncing.current) {
        isSyncing.current = true;
        try {
          const { applyTemplate } = await import('../api/templateApi');
          await applyTemplate(profile.active_planner_id, plannerDate);
        } catch (syncErr) {
          console.error("Failed to sync template to planner:", syncErr);
        } finally {
          isSyncing.current = false;
        }
      }
      await loadTasks();

      // Trigger background Google Calendar sync
      try {
        const token = localStorage.getItem('token');
        if (token) {
          const tzOffset = new Date().getTimezoneOffset();
          fetch(`/integrations/google/calendar/sync?target_date=${plannerDate}&tz_offset=${tzOffset}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
          }).then(res => {
            if (res.ok) {
              res.json().then(syncedTasks => {
                setTasks(syncedTasks);
              });
            }
          });
        }
      } catch (err) {
        console.error("Background calendar sync failed:", err);
      }
    };

    syncAndLoad();
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
        const tzOffset = new Date().getTimezoneOffset();
        const res = await fetch(`/tasks/missed-checkins?tz_offset=${tzOffset}`, {
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

    const loadEarliestDate = async () => {
      try {
        const res = await fetchEarliestTaskDate();
        if (res && res.earliest_date) {
          setEarliestDate(res.earliest_date);
        }
      } catch (err) {
        console.error(err);
      }
    };
    loadEarliestDate();
  }, []);

  const handleTaskSubmit = async (submittedTaskForm: any) => {
    setTaskFormError(null);
    try {
      if (!submittedTaskForm.title) return;
      if (submittedTaskForm.start_time >= submittedTaskForm.end_time) {
        throw new Error("End time must be after start time");
      }

      checkFixedBlockOverlap(submittedTaskForm, plannerDate, fixedBlocks);

      let start_time = submittedTaskForm.start_time ? new Date(`${plannerDate}T${submittedTaskForm.start_time}:00`).toISOString() : null;
      let due_date = submittedTaskForm.end_time ? new Date(`${plannerDate}T${submittedTaskForm.end_time}:00`).toISOString() : new Date(`${plannerDate}T23:59:59`).toISOString();

      const payload: any = { ...submittedTaskForm, start_time, due_date };
      if (payload.category_id === '') {
        payload.category_id = null;
      }

      if (editingTaskId) {
        await updateTask(editingTaskId, payload);
        setMessage('Task updated');
      } else {
        // Assign the active template id as the source for manual grouping, 
        // but no source_template_task_id so it's treated as a manual task under that template.
        if (activePlanner?.id && !payload.source_template_id) {
          payload.source_template_id = activePlanner.id;
        }
        await createTask(payload);
        setMessage('Task added');
      }
      setEditingTaskData(emptyTask);
      setEditingTaskId(null);
      setShowTaskForm(false);
      await loadTasks();
    } catch (error: any) {
      setTaskFormError(error.message);
    }
  };

  const [deleteTargetTask, setDeleteTargetTask] = useState<Task | null>(null);

  const handleDeleteTask = async (taskId: string) => {
    const taskToDelete = tasks.find((t) => t.id === taskId);
    if (taskToDelete && taskToDelete.source === 'calendar') {
      setDeleteTargetTask(taskToDelete);
      return;
    }

    try {
      await deleteTask(taskId, false);
      setMessage('Task deleted');
      await loadTasks();
    } catch (error: any) {
      setMessage(error.message);
    }
  };

  const confirmDeleteExternalTask = async (deleteInCalendar: boolean) => {
    if (!deleteTargetTask) return;
    try {
      await deleteTask(deleteTargetTask.id, deleteInCalendar);
      setMessage(deleteInCalendar ? 'Task deleted locally and from Google Calendar' : 'Task removed from planner');
      setDeleteTargetTask(null);
      await loadTasks();
    } catch (error: any) {
      setMessage(error.message || 'Failed to delete task');
      setDeleteTargetTask(null);
    }
  };

  const startEditTask = (task: Task) => {
    let start_time = '';
    let end_time = '';
    if (task.start_time) {
      start_time = new Date(task.start_time).toTimeString().substring(0, 5);
    }
    if (task.due_date) {
      end_time = new Date(task.due_date).toTimeString().substring(0, 5);
    }
    setEditingTaskData({ ...task, start_time, end_time });
    setEditingTaskId(task.id);
    setShowTaskForm(true);
  };

  const cancelEditTask = () => {
    setEditingTaskData(emptyTask);
    setEditingTaskId(null);
    setShowTaskForm(false);
  };

  const handleCheckin = async (taskId: string, checkinData: any) => {
    try {
      const { start_time, due_date, ...restCheckin } = checkinData;
      const updates: any = {};

      if (start_time) updates.start_time = start_time;
      if (due_date) updates.due_date = due_date;

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

  const handleAddToTemplate = async (task: Task) => {
    if (!activePlanner) {
      setMessage("No active template selected.");
      return;
    }
    try {
      const { createTemplateTask } = await import('../api/templateApi');

      const formatTimeLocal = (isoString?: string) => {
        if (!isoString) return null;
        return new Date(isoString).toTimeString().substring(0, 8);
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
        source_template_id: activePlanner.id,
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
        minDate={earliestDate}
        onAddTask={() => { setEditingTaskData(emptyTask); setShowTaskForm(true); }}
        activePlannerName={activePlanner?.name || null}
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
              initialTask={editingTaskData}
              onSubmit={handleTaskSubmit}
              onCancel={cancelEditTask}
              error={taskFormError || undefined}
            />
            </div>
          </div>
        </div>
      )}

      {/* Delete External Task Modal */}
      {deleteTargetTask && (
        <div className="fixed inset-0 bg-zinc-900/40 backdrop-blur-sm flex items-center justify-center z-[110] p-4">
          <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-xl w-full max-w-md p-6 space-y-5 border border-zinc-200 dark:border-zinc-700">
            <h3 className="text-lg font-bold text-zinc-900 dark:text-white">Delete Google Calendar Task</h3>
            <p className="text-sm text-zinc-600 dark:text-zinc-300">
              "<span className="font-semibold text-zinc-800 dark:text-zinc-100">{deleteTargetTask.title}</span>" is linked to Google Calendar. How would you like to delete it?
            </p>
            <div className="flex flex-col gap-2.5 pt-2">
              <button
                onClick={() => confirmDeleteExternalTask(false)}
                className="w-full py-2.5 px-4 text-sm font-medium text-zinc-700 dark:text-zinc-200 bg-zinc-100 dark:bg-zinc-700/60 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-xl transition-colors text-left flex items-center justify-between"
              >
                <span>Remove from planner only</span>
                <span className="text-xs text-zinc-400">&rarr;</span>
              </button>
              <button
                onClick={() => confirmDeleteExternalTask(true)}
                className="w-full py-2.5 px-4 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 hover:bg-red-100 border border-red-200 dark:border-red-800/40 rounded-xl transition-colors text-left flex items-center justify-between"
              >
                <span>Delete in Google Calendar too</span>
                <span className="text-xs text-red-400">&rarr;</span>
              </button>
              <button
                onClick={() => setDeleteTargetTask(null)}
                className="w-full py-2 px-4 text-sm font-medium text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 transition-colors text-center mt-1"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Timeline Workspace */}
      <section className="flex-1 overflow-hidden relative px-6 pb-6">
        <div className="absolute inset-0 bg-card shadow-sm border border-border m-6 mt-0 rounded-2xl overflow-hidden flex flex-col">
          {plannerDate < todayIso() ? (
            <PastTemplateView tasks={tasks} templates={templates} />
          ) : (
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
          )}
        </div>
      </section>
    </div>
  );
};
