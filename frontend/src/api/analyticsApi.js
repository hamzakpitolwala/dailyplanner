class AnalyticsApiClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async _fetchData(endpoint, token, filters = {}) {
    const query = new URLSearchParams(filters).toString();
    const res = await fetch(`${this.baseUrl}/analytics/${endpoint}?${query}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error(`Failed to fetch ${endpoint}`);
    return res.json();
  }

  async fetchOverview(token, filters = {}) {
    return this._fetchData('overview', token, filters);
  }

  async fetchTimePatterns(token, filters = {}) {
    return this._fetchData('time-patterns', token, filters);
  }

  async fetchCalendarConflicts(token, filters = {}) {
    return this._fetchData('calendar-conflicts', token, filters);
  }

  async fetchFocusMetrics(token, filters = {}) {
    return this._fetchData('focus', token, filters);
  }

  async fetchAiEffectiveness(token, filters = {}) {
    return this._fetchData('ai-effectiveness', token, filters);
  }

  async fetchOfficeHours(token, filters = {}) {
    return this._fetchData('office-hours', token, filters);
  }
}

export const analyticsApi = new AnalyticsApiClient();
