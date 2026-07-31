import { apiRequest } from './client';
import { TASKS_BASE } from '../utils/constants';

export const fetchTasks = async () => {
  return await apiRequest(`${TASKS_BASE}`);
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

export const deleteTask = async (taskId) => {
  return await apiRequest(`${TASKS_BASE}/${taskId}`, {
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

