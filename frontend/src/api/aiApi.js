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

  /**
   * @param {string} message
   * @param {string | null} [conversationId]
   */
  agentChat: async (message, conversationId = null) => {
    const payload = { message };
    if (conversationId) payload.conversation_id = conversationId;
    
    const response = await apiRequest('/ai/agent/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return response;
  },

  /**
   * @param {string} workflowId
   * @param {boolean} approved
   * @param {any} [overrides]
   */
  agentApprove: async (workflowId, approved, overrides = null) => {
    const payload = { workflow_id: workflowId, approved };
    if (overrides) payload.overrides = overrides;
    
    const response = await apiRequest(`/ai/agent/approve/${workflowId}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return response;
  },

  getRecentConversation: async () => {
    const response = await apiRequest('/ai/agent/conversations/recent', {
      method: 'GET',
    });
    return response;
  },

  getConversationMessages: async (sessionId) => {
    const response = await apiRequest(`/ai/agent/conversations/${sessionId}/messages`, {
      method: 'GET',
    });
    return response;
  },

  searchChatHistory: async (query, limit = 10) => {
    const response = await apiRequest(`/ai/agent/chat/search?q=${encodeURIComponent(query)}&limit=${limit}`, {
      method: 'GET',
    });
    return response;
  },

};
