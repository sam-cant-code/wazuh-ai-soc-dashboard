import { create } from 'zustand';
import { alertService } from '../alertService';

export const useAlertsStore = create((set, get) => ({
  // State
  alerts: [],
  total: 0,
  isLoading: false,
  error: null,
  selectedAlert: null,
  
  // Filters & Pagination State
  filters: {
    severity_min: null,
    agent_id: null,
    search: '',
  },
  pagination: {
    limit: 50,
    offset: 0,
  },

  // Actions
  fetchAlerts: async () => {
    set({ isLoading: true, error: null });
    const { filters, pagination } = get();
    
    try {
      const response = await alertService.getAlerts({
        ...filters,
        ...pagination
      });
      set({ 
        alerts: response.alerts, 
        total: response.total, 
        isLoading: false 
      });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  setFilter: (key, value) => {
    set((state) => ({
      filters: { ...state.filters, [key]: value },
      pagination: { ...state.pagination, offset: 0 } // Reset page on filter change
    }));
    get().fetchAlerts();
  },

  setPage: (newOffset) => {
    set((state) => ({
      pagination: { ...state.pagination, offset: newOffset }
    }));
    get().fetchAlerts();
  },

  selectAlert: async (alertId) => {
    if (!alertId) {
      set({ selectedAlert: null });
      return;
    }
    
    // Optimistic lookup from current list
    const existing = get().alerts.find(a => a.id === alertId);
    if (existing) {
      set({ selectedAlert: existing });
    } else {
      // Fallback fetch if deep-linked
      try {
        const alert = await alertService.getAlertById(alertId);
        set({ selectedAlert: alert });
      } catch (err) {
        console.error("Failed to load alert detail", err);
      }
    }
  }
}));