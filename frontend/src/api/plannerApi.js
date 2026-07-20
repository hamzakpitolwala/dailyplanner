import { apiRequest } from './client';
import { PLANNER_BASE } from '../utils/constants';

export const fetchTodayPlanner = async (date) => {
  return await apiRequest(`${PLANNER_BASE}/today?planner_date=${date}`);
};

export const updatePlannerInfo = async (date, title, notes) => {
  return await apiRequest(`${PLANNER_BASE}/today?planner_date=${date}`, {
    method: 'PATCH',
    body: JSON.stringify({ title, notes: notes || null }),
  });
};

export const createActivity = async (plannerId, activityData) => {
  return await apiRequest(`${PLANNER_BASE}/${plannerId}/activities`, {
    method: 'POST',
    body: JSON.stringify(activityData),
  });
};

export const updateActivity = async (activityId, activityData) => {
  return await apiRequest(`${PLANNER_BASE}/activities/${activityId}`, {
    method: 'PATCH',
    body: JSON.stringify(activityData),
  });
};

export const deleteActivity = async (activityId) => {
  return await apiRequest(`${PLANNER_BASE}/activities/${activityId}`, {
    method: 'DELETE',
  });
};

export const fetchActivityHistory = async (activityId) => {
  return await apiRequest(`${PLANNER_BASE}/activities/${activityId}/history`);
};

export const submitActivityCheckin = async (activityId, status, notes, missedReason = null, alternate = null, tgtDate = null) => {
  const payload = { action_type: 'status_change', new_state: status, notes: notes || null };

  if (status === 'not_done' && missedReason) {
    payload.missed_reason = missedReason;
  }
  if (status === 'not_done' && alternate) {
    payload.alternate_activity = alternate;
  }
  if (status === 'rescheduled' && tgtDate) {
    payload.target_date = tgtDate;
  }

  return await apiRequest(`${PLANNER_BASE}/activities/${activityId}/history`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};
