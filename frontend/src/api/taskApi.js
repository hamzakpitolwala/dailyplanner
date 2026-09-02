import { apiRequest } from './client';
import { TASKS_BASE } from '../utils/constants';

export const fetchTasks = async (targetDate) => {
  let url = `${TASKS_BASE}`;
  if (targetDate) {
    const tzOffset = new Date().getTimezoneOffset();
    url += `?target_date=${targetDate}&tz_offset=${tzOffset}`;
  }
  return await apiRequest(url);
};


export const fetchEarliestTaskDate = async () => {
  return await apiRequest(`${TASKS_BASE}/earliest-date`);
};

export const createTask = async (taskData) => {
  return await apiRequest(`${TASKS_BASE}`, {
    method: 'POST',
    body: JSON.stringify(taskData),
  });
};

export const updateTask = async (taskId, taskData) => {
  return await apiRequest(`${TASKS_BASE}/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(taskData),
  });
};

export const deleteTask = async (taskId, deleteInCalendar = false) => {
  const query = deleteInCalendar ? '?delete_in_calendar=true' : '';
  return await apiRequest(`${TASKS_BASE}/${taskId}${query}`, {
    method: 'DELETE',
  });
};

export const fetchMissedReasons = async () => {
  return await apiRequest(`${TASKS_BASE}/missed-reasons`);
};

export const fetchAlternateActivities = async () => {
  return await apiRequest(`${TASKS_BASE}/alternate-activities`);
};

export const postTaskCheckin = async (taskId, checkinData) => {
  return await apiRequest(`${TASKS_BASE}/${taskId}/checkin`, {
    method: 'POST',
    body: JSON.stringify(checkinData),
  });
};


export const createSubtask = async (taskId, title) => {
  return await apiRequest(`${TASKS_BASE}/${taskId}/subtasks`, {
    method: 'POST',
    body: JSON.stringify({ title, is_completed: false }),
  });
};

export const updateSubtask = async (taskId, subtaskId, updateData) => {
  return await apiRequest(`${TASKS_BASE}/${taskId}/subtasks/${subtaskId}`, {
    method: 'PATCH',
    body: JSON.stringify(updateData),
  });
};

export const deleteSubtask = async (taskId, subtaskId) => {
  return await apiRequest(`${TASKS_BASE}/${taskId}/subtasks/${subtaskId}`, {
    method: 'DELETE',
  });
};

export const fetchMissedCheckins = async () => {
  const tzOffset = new Date().getTimezoneOffset();
  return await apiRequest(`${TASKS_BASE}/missed-checkins?tz_offset=${tzOffset}`);
};

