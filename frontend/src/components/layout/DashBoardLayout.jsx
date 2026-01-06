import React from 'react';
import { Shield, LayoutDashboard, Bell, Activity, Brain, Users, Settings } from 'lucide-react';

const NavItem = ({ icon: Icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-mono border-l-2 transition-all duration-200 
      ${active 
        ? 'border-cyber-primary bg-cyber-primary/10 text-cyber-primary' 
        : 'border-transparent text-cyber-muted hover:text-cyber-text hover:bg-cyber-card'
      }`}
  >
    <Icon className="w-4 h-4" />
    {label}
  </button>
);

export const DashboardLayout = ({ children, currentView, onViewChange }) => {
  return (
    <div className="flex h-screen bg-cyber-bg text-cyber-text overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-cyber-card border-r border-cyber-border flex flex-col">
        <div className="p-6 border-b border-cyber-border">
          <h1 className="text-2xl font-display font-bold tracking-tighter text-white flex items-center gap-2">
            <Shield className="text-cyber-primary w-6 h-6" />
            WAZUH<span className="text-cyber-primary">.AI</span>
          </h1>
          <div className="flex items-center gap-2 mt-2">
            <span className="w-2 h-2 rounded-full bg-cyber-primary animate-pulse"></span>
            <span className="text-xs font-mono text-cyber-muted">SYSTEM ONLINE</span>
          </div>
        </div>

        <nav className="flex-1 py-4 space-y-1">
          <NavItem icon={LayoutDashboard} label="OVERVIEW" active={currentView === 'overview'} onClick={() => onViewChange('overview')} />
          <NavItem icon={Bell} label="ALERTS" active={currentView === 'alerts'} onClick={() => onViewChange('alerts')} />
          <NavItem icon={Users} label="AGENTS" active={currentView === 'agents'} onClick={() => onViewChange('agents')} />
          <NavItem icon={Activity} label="INCIDENTS" active={currentView === 'incidents'} onClick={() => onViewChange('incidents')} />
          <NavItem icon={Brain} label="AI INSIGHTS" active={currentView === 'ai'} onClick={() => onViewChange('ai')} />
        </nav>

        <div className="p-4 border-t border-cyber-border">
          <NavItem icon={Settings} label="SYSTEM CONFIG" />
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Top Status Bar */}
        <header className="h-16 border-b border-cyber-border bg-cyber-card/50 flex items-center justify-between px-6 backdrop-blur-sm z-10">
            <div className="text-xs font-mono text-cyber-muted">
                // SECURITY_LEVEL: <span className="text-cyber-warning">ELEVATED</span>
            </div>
            <div className="flex items-center gap-4">
                <div className="h-2 w-32 bg-cyber-bg rounded-full overflow-hidden border border-cyber-border">
                    <div className="h-full w-2/3 bg-cyber-primary/50"></div>
                </div>
                <span className="font-mono text-xs text-cyber-primary">CPU: 67%</span>
            </div>
        </header>

        {/* Scrollable Page Content */}
        <div className="flex-1 overflow-auto p-6 scrollbar-thin scrollbar-thumb-cyber-border">
            {children}
        </div>
      </main>
    </div>
  );
};