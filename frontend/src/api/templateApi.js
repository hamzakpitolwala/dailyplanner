import { apiRequest } from './client';

export const fetchTemplates = async () => {
  return await apiRequest(`/templates`);
};

export const createTemplate = async (name, description = '') => {
  return await apiRequest(`/templates`, {
    method: 'POST',
    body: JSON.stringify({ name, description }),
  });
};

export const applyTemplate = async (templateId, targetDate) => {
  return await apiRequest(`/templates/${templateId}/apply?target_date=${targetDate}`, {
    method: 'POST',
  });
};

export const createTemplateTask = async (templateId, payload) => {
  return await apiRequest(`/templates/${templateId}/tasks`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

export const updateTemplateTask = async (templateId, taskId, updateData) => {
  return await apiRequest(`/templates/${templateId}/tasks/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(updateData),
  });
};

export const deleteTemplateTask = async (templateId, taskId) => {
  return await apiRequest(`/templates/${templateId}/tasks/${taskId}`, {
    method: 'DELETE',
  });
};

export const deleteTemplate = async (templateId) => {
  return await apiRequest(`/templates/${templateId}`, {
    method: 'DELETE',
  });
};
