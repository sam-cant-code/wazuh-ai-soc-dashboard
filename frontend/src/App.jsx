import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import { OverviewDashboard } from './features/overview/overviewDashboard';
import { AlertsTable } from './features/alerts/components/AlertsTable';
import { AlertDetailPanel } from './features/alerts/components/AlertDetailPanel';

function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<OverviewDashboard />} />
          <Route path="/alerts" element={
            <>
              <AlertsTable />
              <AlertDetailPanel />
            </>
          } />
          {/* Placeholders for other routes */}
          <Route path="/agents" element={<div className="text-cyber-muted p-10">Agent Management Module</div>} />
          <Route path="/ai-insights" element={<div className="text-cyber-muted p-10">AI Insights Module</div>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}

export default App;