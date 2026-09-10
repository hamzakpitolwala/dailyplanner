import { apiRequest } from './client';
import { TASKS_BASE } from '../utils/constants';

/**
 * Fetch Tasks.
 */
export const fetchTasks = async (targetDate) => {
  let url = `${TASKS_BASE}`;
  if (targetDate) {
    const tzOffset = new Date().getTimezoneOffset();
    url += `?target_date=${targetDate}&tz_offset=${tzOffset}`;
  }
  return await apiRequest(url);
};

/**
 * Fetch Task History.
 */
export const fetchTaskHistory = async (skip = 0, limit = 1000) => {
  const tzOffset = new Date().getTimezoneOffset();
  return await apiRequest(`${TASKS_BASE}/history?tz_offset=${tzOffset}&skip=${skip}&limit=${limit}`);
};


/**
 * Fetch Earliest Task Date.
 */
export const fetchEarliestTaskDate = async () => {
  return await apiRequest(`${TASKS_BASE}/earliest-date`);
};

/**
 * Create Task.
 */
export const createTask = async (taskData) => {
  return await apiRequest(`${TASKS_BASE}`, {
    method: 'POST',
    body: JSON.stringify(taskData),
  });
};

/**
 * Update Task.
 */
export const updateTask = async (taskId, taskData) => {
  return await apiRequest(`${TASKS_BASE}/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(taskData),
  });
};

/**
 * Delete Task.
 */
export const deleteTask = async (taskId, deleteInCalendar = false) => {
  const query = deleteInCalendar ? '?delete_in_calendar=true' : '';
  return await apiRequest(`${TASKS_BASE}/${taskId}${query}`, {
    method: 'DELETE',
  });
};

/**
 * Fetch Missed Reasons.
 */
export const fetchMissedReasons = async () => {
  return await apiRequest(`${TASKS_BASE}/missed-reasons`);
};

/**
 * Fetch Alternate Activities.
 */
export const fetchAlternateActivities = async () => {
  return await apiRequest(`${TASKS_BASE}/alternate-activities`);
};

/**
 * Post Task Checkin.
 */
export const postTaskCheckin = async (taskId, checkinData) => {
  return await apiRequest(`${TASKS_BASE}/${taskId}/checkin`, {
    method: 'POST',
    body: JSON.stringify(checkinData),
  });
};


/**
 * Create Subtask.
 */
export const createSubtask = async (taskId, title) => {
  return await apiRequest(`${TASKS_BASE}/${taskId}/subtasks`, {
    method: 'POST',
    body: JSON.stringify({ title, is_completed: false }),
  });
};

/**
 * Update Subtask.
 */
export const updateSubtask = async (taskId, subtaskId, updateData) => {
  return await apiRequest(`${TASKS_BASE}/${taskId}/subtasks/${subtaskId}`, {
    method: 'PATCH',
    body: JSON.stringify(updateData),
  });
};

/**
 * Delete Subtask.
 */
export const deleteSubtask = async (taskId, subtaskId) => {
  return await apiRequest(`${TASKS_BASE}/${taskId}/subtasks/${subtaskId}`, {
    method: 'DELETE',
  });
};

/**
 * Fetch Missed Checkins.
 */
export const fetchMissedCheckins = async () => {
  const tzOffset = new Date().getTimezoneOffset();
  return await apiRequest(`${TASKS_BASE}/missed-checkins?tz_offset=${tzOffset}`);
};

