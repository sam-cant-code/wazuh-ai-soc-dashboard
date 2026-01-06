import React from 'react';
import { useAlertsStore } from '../stores/useAlertsStore';
import { X, ShieldAlert, Terminal, Clock, Server } from 'lucide-react';

export const AlertDetailPanel = () => {
  const { selectedAlert, selectAlert } = useAlertsStore();

  if (!selectedAlert) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-[600px] bg-[#0f0f16] border-l border-cyber-border shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-cyber-border bg-cyber-card flex justify-between items-start">
        <div>
          <h3 className="text-lg font-display text-cyber-primary flex items-center gap-2">
            <ShieldAlert size={20} />
            Alert Details
          </h3>
          <p className="text-xs text-cyber-muted mt-1 font-mono">{selectedAlert.id}</p>
        </div>
        <button 
          onClick={() => selectAlert(null)}
          className="text-cyber-muted hover:text-white transition-colors"
        >
          <X size={24} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        
        {/* Summary */}
        <div className="space-y-4">
          <h4 className="text-sm uppercase text-cyber-muted font-bold tracking-wider">Description</h4>
          <p className="text-lg leading-relaxed text-white">
            {selectedAlert.rule.description}
          </p>
          
          <div className="grid grid-cols-2 gap-4 mt-4">
             <div className="bg-cyber-bg p-3 rounded border border-cyber-border">
                <div className="flex items-center gap-2 text-cyber-muted text-xs mb-1">
                  <Clock size={14} /> Time
                </div>
                <div className="font-mono text-sm">
                  {new Date(selectedAlert.timestamp).toLocaleString()}
                </div>
             </div>
             <div className="bg-cyber-bg p-3 rounded border border-cyber-border">
                <div className="flex items-center gap-2 text-cyber-muted text-xs mb-1">
                  <Server size={14} /> Agent
                </div>
                <div className="font-mono text-sm text-cyber-primary">
                  {selectedAlert.agent.name}
                </div>
             </div>
          </div>
        </div>

        {/* MITRE ATT&CK */}
        {selectedAlert.rule.mitre && (
          <div className="space-y-2">
            <h4 className="text-sm uppercase text-cyber-muted font-bold tracking-wider">MITRE ATT&CK</h4>
            <div className="flex flex-wrap gap-2">
              {selectedAlert.rule.mitre.tactic.map(t => (
                <span key={t} className="px-2 py-1 bg-purple-900/30 border border-purple-500/30 text-purple-300 text-xs rounded">
                  {t}
                </span>
              ))}
              {selectedAlert.rule.mitre.id.map(id => (
                 <span key={id} className="px-2 py-1 bg-red-900/30 border border-red-500/30 text-red-300 text-xs rounded font-mono">
                  {id}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Raw Data (Log) */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm uppercase text-cyber-muted font-bold tracking-wider">
            <Terminal size={16} />
            Raw Event Payload
          </div>
          <div className="bg-[#050508] p-4 rounded border border-cyber-border font-mono text-xs text-cyber-muted overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(selectedAlert.data || selectedAlert.full_log, null, 2)}
          </div>
        </div>

        {/* AI Insight Placeholder */}
        <div className="bg-gradient-to-br from-cyber-card to-cyber-bg border border-cyber-primary/30 p-4 rounded-lg relative overflow-hidden">
          <div className="absolute top-0 right-0 p-2 opacity-10">
            <BrainCircuit size={64} />
          </div>
          <h4 className="text-cyber-primary font-display mb-2 flex items-center gap-2">
            <BrainCircuit size={16} /> AI Analysis
          </h4>
          <p className="text-sm text-cyber-text/80">
            This alert matches a pattern often associated with lateral movement. Recommended action: Isolate host {selectedAlert.agent.ip} and verify user credentials.
          </p>
        </div>

      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-cyber-border bg-cyber-card flex gap-4">
        <button className="flex-1 bg-cyber-primary/10 hover:bg-cyber-primary/20 text-cyber-primary border border-cyber-primary/50 py-2 rounded font-medium transition-colors">
          Investigate
        </button>
        <button className="flex-1 bg-cyber-danger/10 hover:bg-cyber-danger/20 text-cyber-danger border border-cyber-danger/50 py-2 rounded font-medium transition-colors">
          Block IP
        </button>
      </div>
    </div>
  );
};