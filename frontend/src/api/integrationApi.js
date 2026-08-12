import { apiRequest } from './client';

export const getGoogleCalendarAuthUrl = async () => {
  return await apiRequest('/integrations/google/calendar/auth-url');
};

export const getGoogleCalendarStatus = async () => {
  return await apiRequest('/integrations/google/calendar/status');
};

export const disconnectGoogleCalendar = async () => {
  return await apiRequest('/integrations/google/calendar/disconnect', {
    method: 'DELETE',
  });
};
