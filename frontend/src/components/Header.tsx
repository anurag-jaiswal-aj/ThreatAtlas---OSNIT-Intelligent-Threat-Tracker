import React, { useState } from 'react';
import { Shield, RefreshCw, AlertTriangle, Layers, Bell } from 'lucide-react';
import { processPendingPosts } from '../api/client';
import type { ProcessPendingResponse, EventGlobalMetrics } from '../types';
import { AlertsModal } from './AlertsModal';

interface HeaderProps {
  isOnline: boolean;
  globalMetrics: EventGlobalMetrics;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isOnline,
  globalMetrics,
  onRefresh,
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processResult, setProcessResult] = useState<ProcessPendingResponse | null>(null);
  const [isAlertsModalOpen, setIsAlertsModalOpen] = useState(false);

  const handleProcessPending = async () => {
    setIsProcessing(true);
    setProcessResult(null);
    try {
      const res = await processPendingPosts();
      setProcessResult(res);
      onRefresh();
    } catch (err) {
      console.error('Failed to process pending posts:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <header className="h-16 bg-slate-950/90 border-b border-slate-800/80 px-6 flex items-center justify-between backdrop-blur-md z-30 relative select-none">
      {/* Brand & System Title */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-600/20 border border-blue-500/30 rounded-lg flex items-center justify-center text-blue-400">
          <Shield className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-wider text-slate-100 uppercase">
              Threat<span className="text-blue-500">Atlas</span>
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-mono tracking-widest bg-blue-950 text-blue-400 border border-blue-800/50 rounded uppercase">
              OSINT v1.0
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono">Defensive Intelligence Platform</p>
        </div>
      </div>

      {/* Metrics & System Status */}
      <div className="hidden md:flex items-center gap-6">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/60 border border-slate-800 rounded-md font-mono text-xs">
          <Layers className="w-4 h-4 text-slate-400" />
          <span className="text-slate-400">Active Events:</span>
          <span className="text-slate-200 font-bold">{globalMetrics.total}</span>
        </div>

        {globalMetrics.high > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-red-950/40 border border-red-900/50 rounded-md font-mono text-xs animate-pulse">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span className="text-red-300">High Threat:</span>
            <span className="text-red-400 font-bold">{globalMetrics.high}</span>
          </div>
        )}

        <div className="flex items-center gap-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              isOnline ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-red-500 shadow-[0_0_8px_#ef4444]'
            }`}
          />
          <span className="text-xs font-mono text-slate-300">
            {isOnline ? 'SYSTEM ONLINE' : 'DISCONNECTED'}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setIsAlertsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs rounded-lg border border-slate-700 transition-all cursor-pointer"
        >
          <Bell className="w-3.5 h-3.5" />
          <span>Alerts</span>
        </button>

        <button
          onClick={handleProcessPending}
          disabled={isProcessing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-medium text-xs rounded-lg border border-blue-500/50 transition-all shadow-lg shadow-blue-950/50 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isProcessing ? 'animate-spin' : ''}`} />
          <span>{isProcessing ? 'Processing Pipeline...' : 'Process Pending OSINT'}</span>
        </button>

        {processResult && (
          <div className="hidden lg:block text-xs font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/50 px-3 py-1.5 rounded-md">
            +{processResult.processed_count} Processed ({processResult.events_created} Created, {processResult.events_merged} Merged)
          </div>
        )}
      </div>

      <AlertsModal
        isOpen={isAlertsModalOpen}
        onClose={() => setIsAlertsModalOpen(false)}
      />
    </header>
  );
};
