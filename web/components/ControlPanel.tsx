import React, { useState } from 'react';
import { Camera, Mic, Brain, Eye } from 'lucide-react';

interface ControlPanelProps {
  isCamOn: boolean;
  isMicOn: boolean;
  isThinkMode: boolean;
  onToggleCam: () => void;
  onToggleMic: () => void;
  onToggleThink: () => void;
  onShowFeed: () => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  isCamOn,
  isMicOn,
  isThinkMode,
  onToggleCam,
  onToggleMic,
  onToggleThink,
  onShowFeed
}) => {

  const CustomToggle = ({ isOn, onToggle, activeColor = "bg-blue-500" }: { isOn: boolean, onToggle: () => void, activeColor?: string }) => (
    <button
      onClick={onToggle}
      className={`relative w-11 h-6 rounded-full transition-colors duration-300 ease-in-out focus:outline-none ${isOn ? activeColor : 'bg-slate-200'}`}
    >
      <div
        className={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-300 ease-[cubic-bezier(0.175,0.885,0.32,1.275)] ${isOn ? 'translate-x-5' : 'translate-x-0'}`}
      />
    </button>
  );

  const ControlRow = ({ label, icon: Icon, isOn, onToggle, activeColor, children }: any) => (
    <div className="flex flex-col">
      <div className="flex items-center justify-between py-3 group">
        <div className="flex items-center space-x-3 text-slate-600">
          <div className={`p-2 rounded-lg transition-colors duration-300 ${isOn ? 'bg-slate-100 text-slate-800' : 'bg-transparent text-slate-400'}`}>
            <Icon size={18} />
          </div>
          <span className="text-sm font-medium tracking-tight group-hover:text-slate-800 transition-colors">{label}</span>
        </div>
        <CustomToggle isOn={isOn} onToggle={onToggle} activeColor={activeColor} />
      </div>
      {children}
    </div>
  );

  return (
    <div className="absolute top-6 right-6 w-80 bg-white/90 backdrop-blur-2xl border border-white/40 shadow-2xl rounded-3xl p-6 z-20">
      <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-2 pl-1">Device Control</h3>

      <div className="space-y-1">
        <ControlRow
          label="Camera"
          icon={Camera}
          isOn={isCamOn}
          onToggle={onToggleCam}
          activeColor="bg-indigo-500"
        >
          {isCamOn && (
            <button
              onClick={(e) => { e.stopPropagation(); onShowFeed(); }}
              className="ml-11 mb-2 flex items-center gap-2 px-3 py-2 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors"
            >
              <Eye size={14} />
              Show Feed
            </button>
          )}
        </ControlRow>

        <ControlRow
          label="Microphone"
          icon={Mic}
          isOn={isMicOn}
          onToggle={onToggleMic}
          activeColor="bg-rose-500"
        />

        <div className="h-px bg-slate-100/80 my-3 mx-2" />

        <ControlRow
          label="Think-Dialogue"
          icon={Brain}
          isOn={isThinkMode}
          onToggle={onToggleThink}
          activeColor="bg-violet-600"
        />
      </div>

      {isThinkMode && (
        <div className="mt-4 p-3 bg-violet-50 rounded-xl border border-violet-100">
          <p className="text-[11px] text-violet-700 text-center leading-relaxed font-medium">
            TTS will speak Annie Mie's thoughts from &lt;think&gt; blocks along with her response.
          </p>
        </div>
      )}
    </div>
  );
};