import { apiRequest } from './client';

/**
 * Get Google Calendar Auth Url.
 */
export const getGoogleCalendarAuthUrl = async () => {
  return await apiRequest('/integrations/google/calendar/auth-url');
};

/**
 * Get Google Calendar Status.
 */
export const getGoogleCalendarStatus = async () => {
  return await apiRequest('/integrations/google/calendar/status');
};

/**
 * Disconnect Google Calendar.
 */
export const disconnectGoogleCalendar = async () => {
  return await apiRequest('/integrations/google/calendar/disconnect', {
    method: 'DELETE',
  });
};

/**
 * Sync Google Calendar.
 */
export const syncGoogleCalendar = async (targetDate) => {
  const tzOffset = new Date().getTimezoneOffset();
  return await apiRequest(
    `/integrations/google/calendar/sync?target_date=${targetDate}&tz_offset=${tzOffset}`,
    { method: 'POST' }
  );
};

