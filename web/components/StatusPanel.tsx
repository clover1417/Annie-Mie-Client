import React from 'react';
import { Activity, Clock, Cpu, Mic, Video, Zap, Server } from 'lucide-react';

interface StatusPanelProps {
  connected: boolean;
  micName: string;
  camName: string;
  fps: number;
  modelName: string;
  onSync: () => void;
}

export const StatusPanel: React.FC<StatusPanelProps> = ({
  connected,
  micName,
  camName,
  fps,
  modelName,
  onSync
}) => {
  return (
    <div className="absolute top-6 left-6 w-80 bg-white/90 backdrop-blur-2xl border border-white/40 shadow-2xl rounded-3xl p-6 z-20 flex flex-col gap-5">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <div className="relative">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
            <Zap size={24} fill="currentColor" className="drop-shadow-sm" />
          </div>
          <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-400'}`} />
        </div>
        <div>
          <h1 className="font-bold text-slate-800 text-xl tracking-tight">Annie Mie</h1>
          <div className="flex items-center gap-1 text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full w-fit mt-1">
            <Server size={10} />
            <span className="truncate max-w-[120px]">{modelName}</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="bg-slate-50/50 rounded-2xl p-4 border border-slate-100 space-y-3">
        <div className="flex items-center space-x-3 text-xs text-slate-600">
          <Mic size={14} className="text-slate-400 shrink-0" />
          <span className="truncate font-medium">{micName}</span>
        </div>
        <div className="flex items-center space-x-3 text-xs text-slate-600">
          <Video size={14} className="text-slate-400 shrink-0" />
          <span className="truncate font-medium">{camName}</span>
        </div>
        <div className="flex items-center justify-between text-xs text-slate-600 pt-1 border-t border-slate-100">
          <div className="flex items-center space-x-2">
            <Clock size={14} className="text-slate-400" />
            <span>Capture: {fps} FPS</span>
          </div>
          <div className={`font-bold ${connected ? 'text-emerald-500' : 'text-slate-400'}`}>
            {connected ? 'ONLINE' : 'OFFLINE'}
          </div>
        </div>
      </div>

      {/* Sync Button */}
      <button
        type="button"
        onClick={onSync}
        className={`w-full py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 shadow-sm border ${connected
            ? 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            : 'bg-slate-900 border-slate-900 text-white hover:bg-slate-800 hover:shadow-lg'
          }`}
      >
        {connected ? 'Resync Connection' : 'Sync System'}
      </button>
    </div>
  );
};