import React, { useEffect } from 'react';
import { useAlertsStore } from '../stores/useAlertsStore';
import { AlertTriangle, Search, Filter } from 'lucide-react';
import { format } from 'date-fns';

const SeverityBadge = ({ level }) => {
  const colors = {
    low: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    critical: 'bg-red-500/10 text-red-400 border-red-500/20 shadow-glow-red',
  };
  
  // Mapping logic matching backend SeverityLevel enum
  const getSeverity = (lvl) => {
    if (lvl < 5) return 'low';
    if (lvl < 10) return 'medium';
    if (lvl < 13) return 'high';
    return 'critical';
  };

  const severity = getSeverity(level);
  
  return (
    <span className={`px-2 py-1 rounded text-xs border uppercase font-bold tracking-wider ${colors[severity]}`}>
      {severity} ({level})
    </span>
  );
};

export const AlertsTable = () => {
  const { alerts, fetchAlerts, isLoading, selectAlert } = useAlertsStore();

  useEffect(() => {
    fetchAlerts();
  }, []);

  if (isLoading && alerts.length === 0) {
    return <div className="text-cyber-primary font-display p-8 text-xl animate-pulse">LOADING SECURITY EVENTS...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex justify-between items-center bg-cyber-card p-4 rounded-lg border border-cyber-border">
        <h2 className="text-xl font-display text-cyber-text">Recent Alerts</h2>
        <div className="flex gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 text-cyber-muted" size={16} />
            <input 
              type="text" 
              placeholder="Search logs..." 
              className="bg-cyber-bg border border-cyber-border rounded px-10 py-2 text-sm focus:border-cyber-primary focus:outline-none w-64 text-cyber-text"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-cyber-card border border-cyber-border hover:border-cyber-primary rounded text-sm transition-colors">
            <Filter size={16} />
            Filter
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-cyber-card rounded-lg border border-cyber-border overflow-hidden shadow-panel">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#0f0f16] text-cyber-muted uppercase text-xs font-bold tracking-wider">
            <tr>
              <th className="p-4">Timestamp</th>
              <th className="p-4">Level</th>
              <th className="p-4">Agent</th>
              <th className="p-4">Description</th>
              <th className="p-4">Rule ID</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-cyber-border">
            {alerts.map((alert) => (
              <tr 
                key={alert.id} 
                onClick={() => selectAlert(alert.id)}
                className="hover:bg-cyber-bg/50 cursor-pointer transition-colors group"
              >
                <td className="p-4 text-cyber-muted font-mono whitespace-nowrap">
                  {format(new Date(alert.timestamp), 'MMM dd HH:mm:ss')}
                </td>
                <td className="p-4">
                  <SeverityBadge level={alert.rule.level} />
                </td>
                <td className="p-4 font-mono text-cyber-primary">
                  {alert.agent.name} <span className="text-cyber-muted text-xs">({alert.agent.ip})</span>
                </td>
                <td className="p-4 text-cyber-text group-hover:text-white transition-colors">
                  {alert.rule.description}
                </td>
                <td className="p-4 font-mono text-cyber-muted">{alert.rule.id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};