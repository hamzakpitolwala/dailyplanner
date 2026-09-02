import React, { useEffect, useState, useMemo } from 'react';
import { fetchTasks, deleteTask } from '../api/taskApi';
import { PastTaskCard } from '../components/Planner/PastTaskCard';
import { Task } from '../types';
import { Calendar } from 'lucide-react';

export const HistoryPage = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const allTasks = await fetchTasks();
      
      // Filter for past tasks only (tasks with a date before today)
      const localToday = new Date().toLocaleDateString('en-CA');
      const pastTasks = allTasks.filter((task: Task) => {
        if (!task.due_date) return false;
        const taskDate = task.due_date.split('T')[0];
        return taskDate < localToday;
      });
      
      setTasks(pastTasks);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDeleteTask = async (taskId: string) => {
    if (!window.confirm('Deleting a task can impact AI suggestions and recommendations, and accuracy in analytics.\n\nAre you sure you want to delete this task?')) {
      return;
    }
    try {
      await deleteTask(taskId, false);
      setTasks(prev => prev.filter(t => t.id !== taskId));
    } catch (err: any) {
      alert(err.message || 'Failed to delete task');
    }
  };

  // Group tasks by Date
  const groupedTasks = useMemo(() => {
    const groups: Record<string, Task[]> = {};
    tasks.forEach(task => {
      const dateKey = task.due_date ? task.due_date.split('T')[0] : 'Unknown Date';
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(task);
    });
    
    // Sort dates descending
    const sortedDates = Object.keys(groups).sort((a, b) => b.localeCompare(a));
    
    return sortedDates.map(date => ({
      date,
      tasks: groups[date].sort((a, b) => {
        const timeA = a.start_time ? new Date(a.start_time).getTime() : 0;
        const timeB = b.start_time ? new Date(b.start_time).getTime() : 0;
        return timeA - timeB;
      })
    }));
  }, [tasks]);

  return (
    <div className="w-full h-full flex flex-col p-6 overflow-y-auto bg-zinc-50/50">
      <div className="max-w-4xl w-full mx-auto">
        <h1 className="text-3xl font-bold text-zinc-800 mb-8 flex items-center gap-3">
          <Calendar className="w-8 h-8 text-primary" />
          Task History
        </h1>

        {loading ? (
          <div className="flex justify-center items-center py-20 text-zinc-500">Loading history...</div>
        ) : error ? (
          <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-100">{error}</div>
        ) : groupedTasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-zinc-500 bg-white/50 backdrop-blur rounded-2xl border border-zinc-200/50">
            <Calendar className="w-12 h-12 mb-4 opacity-20" />
            <p className="text-lg font-medium">No historical tasks found.</p>
            <p className="text-sm mt-1">Tasks from previous days will appear here.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-10">
            {groupedTasks.map(({ date, tasks }) => (
              <div key={date} className="flex flex-col gap-4">
                <div className="flex items-center gap-4">
                  <h2 className="text-xl font-bold text-zinc-800">{new Date(date + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</h2>
                  <div className="h-px flex-1 bg-zinc-200"></div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {tasks.map(task => (
                    <PastTaskCard key={task.id} task={task} onDelete={handleDeleteTask} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
