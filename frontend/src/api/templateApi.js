import { apiRequest } from './client';

/**
 * Fetch Templates.
 */
export const fetchTemplates = async (activeId = null) => {
  const query = activeId ? `?active_id=${activeId}` : '';
  return await apiRequest(`/templates${query}`);
};

/**
 * Fetch Template By Id.
 */
export const fetchTemplateById = async (templateId) => {
  return await apiRequest(`/templates/${templateId}`);
};


/**
 * Create Template.
 */
export const createTemplate = async (payload) => {
  return await apiRequest(`/templates`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

/**
 * Apply Template.
 */
export const applyTemplate = async (templateId, targetDate) => {
  const tzOffset = new Date().getTimezoneOffset();
  return await apiRequest(`/templates/${templateId}/apply?target_date=${targetDate}&tz_offset=${tzOffset}`, {
    method: 'POST',
  });
};

/**
 * Create Template Task.
 */
export const createTemplateTask = async (templateId, payload) => {
  return await apiRequest(`/templates/${templateId}/tasks`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

/**
 * Update Template Task.
 */
export const updateTemplateTask = async (templateId, taskId, updateData) => {
  return await apiRequest(`/templates/${templateId}/tasks/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(updateData),
  });
};

/**
 * Delete Template Task.
 */
export const deleteTemplateTask = async (templateId, taskId) => {
  return await apiRequest(`/templates/${templateId}/tasks/${taskId}`, {
    method: 'DELETE',
  });
};

/**
 * Delete Template.
 */
export const deleteTemplate = async (templateId) => {
  return await apiRequest(`/templates/${templateId}`, {
    method: 'DELETE',
  });
};
