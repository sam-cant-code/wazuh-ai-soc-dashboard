import React, { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { alertService } from '../alerts/alertService';
import { Activity, Users, ShieldAlert, Zap } from 'lucide-react';

const StatCard = ({ label, value, icon: Icon, color }) => (
  <div className="bg-cyber-card p-6 rounded-lg border border-cyber-border shadow-panel relative overflow-hidden group">
    <div className={`absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity p-4 rounded-full bg-${color}-500`}>
      <Icon size={100} />
    </div>
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-cyber-muted text-sm uppercase font-bold tracking-wider">{label}</h3>
      <Icon className={`text-cyber-${color}`} size={24} />
    </div>
    <div className="text-3xl font-display font-bold text-cyber-text">
      {value}
    </div>
  </div>
);

export const OverviewDashboard = () => {
  const [stats, setStats] = useState({ total: 0, critical: 0, agents: 0 });
  const [timeline, setTimeline] = useState([]);

  useEffect(() => {
    // Parallel data fetching
    const loadData = async () => {
      try {
        const [sevMetrics, agentMetrics, timelineData] = await Promise.all([
          alertService.getSeverityMetrics(),
          alertService.getAlerts({ limit: 1 }), // Just to get total count
          alertService.getTimeline('1h')
        ]);

        setStats({
          total: sevMetrics.data.low + sevMetrics.data.medium + sevMetrics.data.high + sevMetrics.data.critical,
          critical: sevMetrics.data.critical,
          agents: agentMetrics.total // Approximation or separate endpoint
        });
        
        // Transform timeline data for Recharts
        const chartData = timelineData.map(point => ({
          time: new Date(point.timestamp).getHours() + ':00',
          alerts: point.total_alerts,
          critical: point.severity_breakdown.critical
        }));
        setTimeline(chartData);

      } catch (e) {
        console.error("Dashboard load failed", e);
      }
    };
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end mb-6">
        <div>
          <h2 className="text-3xl font-display font-bold text-white mb-2">Security Posture</h2>
          <p className="text-cyber-muted">System Overview & Threat Landscape</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-cyber-primary/10 border border-cyber-primary/20 text-cyber-primary text-xs font-bold animate-pulse">
          <div className="w-2 h-2 bg-cyber-primary rounded-full"></div>
          LIVE UPDATES
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard label="Total Alerts (24h)" value={stats.total} icon={Activity} color="primary" />
        <StatCard label="Critical Threats" value={stats.critical} icon={ShieldAlert} color="danger" />
        <StatCard label="Active Agents" value="12" icon={Users} color="warning" />
        <StatCard label="AI Insights" value="5" icon={BrainCircuit} color="text" />
      </div>

      {/* Main Chart */}
      <div className="bg-cyber-card p-6 rounded-lg border border-cyber-border shadow-panel h-[400px]">
        <h3 className="text-lg font-display mb-6">Alert Volume Trend</h3>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={timeline}>
            <defs>
              <linearGradient id="colorAlerts" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00ff9d" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#00ff9d" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a35" />
            <XAxis dataKey="time" stroke="#858595" />
            <YAxis stroke="#858595" />
            <Tooltip 
              contentStyle={{ backgroundColor: '#13131f', borderColor: '#2a2a35', color: '#e0e0e0' }}
              itemStyle={{ color: '#00ff9d' }}
            />
            <Area 
              type="monotone" 
              dataKey="alerts" 
              stroke="#00ff9d" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorAlerts)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};