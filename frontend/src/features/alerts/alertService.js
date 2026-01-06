import { api } from '../../lib/api';

export const alertService = {
  // Fetch paginated alerts with filters
  getAlerts: async (params = {}) => {
    // params: { limit, offset, severity_min, agent_id, search, etc. }
    return api.get('/alerts', { params });
  },

  // Get single alert detail
  getAlertById: async (id) => {
    return api.get(`/alerts/${id}`);
  },

  // Fetch metrics for the overview or analysis
  getSeverityMetrics: async (timeRange) => {
    return api.get('/metrics/severity', { params: timeRange });
  },

  getTimeline: async (interval = '1h') => {
    return api.get('/metrics/timeline', { params: { interval } });
  }
};