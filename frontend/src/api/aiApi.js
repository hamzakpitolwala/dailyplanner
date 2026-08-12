import { apiRequest } from './client';

export const aiApi = {
  generateStarterPlan: async (data = { day_type: 'generic', extra_prompt: '' }) => {
    const response = await apiRequest('/ai/generate-starter-plan', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response;
  },

  generateSummary: async (data) => {
    // data = { period_type: 'day' | 'week', period_start, period_end, extra_prompt }
    const response = await apiRequest('/ai/daily-summary', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response;
  },

  getRecommendations: async (status = 'pending') => {
    const response = await apiRequest(`/ai/recommendations?status=${status}`, {
      method: 'GET',
    });
    return response;
  },

  generateRecommendations: async (periodDays = 7) => {
    const response = await apiRequest(`/ai/recommendations/generate?period_days=${periodDays}`, {
      method: 'POST',
    });
    return response;
  },

  processRecommendationDecision: async (recId, decisionData) => {
    const response = await apiRequest(`/ai/recommendations/${recId}/decision`, {
      method: 'POST',
      body: JSON.stringify(decisionData),
    });
    return response;
  },

  chat: async (messages) => {
    const response = await apiRequest('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ messages }),
    });
    return response;
  },
};
