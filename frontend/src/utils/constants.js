export const AUTH_BASE = '/auth';
export const PLANNER_BASE = '/planners';

export const CHECKIN_STATUSES = [
  { value: 'done', label: '✅ Done', color: '#276749' },
  { value: 'not_done', label: '❌ Not Done', color: '#b42318' },
  { value: 'partial', label: '🔶 Partial', color: '#b54708' },
  { value: 'rescheduled', label: '📅 Rescheduled', color: '#3538cd' },
];

export const REASON_CODES = [
  { value: 'too_busy', label: 'Too busy' },
  { value: 'forgot', label: 'Forgot' },
  { value: 'not_feeling_well', label: 'Not feeling well' },
  { value: 'schedule_conflict', label: 'Schedule conflict' },
  { value: 'low_priority', label: 'Low priority' },
  { value: 'other', label: 'Other' },
];

export const ALTERNATE_PRESETS = [
  'Doing some important work',
  'Attending an unscheduled meeting',
  'Helping a colleague',
  'Personal errand',
];

export const emptyActivity = {
  title: '',
  description: '',
  category: '',
  start_time: '',
  end_time: '',
};

export const todayIso = () => new Date().toISOString().slice(0, 10);
