export const AUTH_BASE = '/auth';
export const TASKS_BASE = '/tasks';

export const TASK_STATUSES = [
  { value: 'pending', label: '⏳ Pending', color: '#b54708' },
  { value: 'in_progress', label: '🔄 In Progress', color: '#3538cd' },
  { value: 'partial', label: '🌓 Partial', color: '#9c27b0' },
  { value: 'completed', label: '✅ Done', color: '#276749' },
  { value: 'not_done', label: '❌ Not Done', color: '#c62828' },
  { value: 'rescheduled', label: '📅 Rescheduled', color: '#ed6c02' },
];

export const emptyTask = {
  title: '',
  description: '',
  category_id: '',
  priority: 1,
  start_time: '',
  end_time: '',
  requires_reason: false,
  allows_alternate: false,
  subtasks: [],
};

export const todayIso = () => {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};
