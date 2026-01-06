import React from 'react';
import { LayoutDashboard, AlertCircle, Shield, Activity, BrainCircuit } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const NavItem = ({ to, icon: Icon, label }) => (
  <NavLink 
    to={to} 
    className={({ isActive }) => 
      `flex items-center gap-3 px-4 py-3 rounded-r-lg border-l-2 transition-all duration-200 ${
        isActive 
          ? 'bg-cyber-card border-cyber-primary text-cyber-primary shadow-[0_0_10px_rgba(0,255,157,0.1)]' 
          : 'border-transparent text-cyber-muted hover:text-cyber-text hover:bg-cyber-card/50'
      }`
    }
  >
    <Icon size={20} />
    <span className="font-medium">{label}</span>
  </NavLink>
);

export const MainLayout = ({ children }) => {
  return (
    <div className="flex h-screen bg-cyber-bg text-cyber-text font-mono overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex flex-col border-r border-cyber-border bg-[#0a0a0f]/95 backdrop-blur">
        <div className="p-6 flex items-center gap-3 border-b border-cyber-border/50">
          <Shield className="text-cyber-primary animate-pulse" size={32} />
          <h1 className="text-xl font-display font-bold tracking-wider">WAZUH<span className="text-cyber-primary">.AI</span></h1>
        </div>
        
        <nav className="flex-1 py-6 space-y-1">
          <NavItem to="/" icon={LayoutDashboard} label="Overview" />
          <NavItem to="/alerts" icon={AlertCircle} label="Alerts" />
          <NavItem to="/agents" icon={Activity} label="Agents" />
          <NavItem to="/ai-insights" icon={BrainCircuit} label="AI Insights" />
        </nav>

        <div className="p-4 border-t border-cyber-border/50">
          <div className="flex items-center gap-2 text-xs text-cyber-muted">
            <div className="w-2 h-2 rounded-full bg-cyber-primary animate-pulse"></div>
            System Status: ONLINE
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto cyber-grid relative">
        <div className="max-w-[1600px] mx-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
};