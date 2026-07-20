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

export const updateTemplateStatus = async (templateId, inUse) => {
  return await apiRequest(`/templates/${templateId}`, {
    method: 'PUT',
    body: JSON.stringify({ in_use: inUse }),
  });
};

export const createTemplateActivity = async (templateId, title = 'New Activity', category = 'General') => {
  return await apiRequest(`/templates/${templateId}/activities`, {
    method: 'POST',
    body: JSON.stringify({ title, category }),
  });
};
