import React from 'react';

interface VisualizerProps {
  volume: number;
  isActive: boolean;
  isThinkMode: boolean;
}

export const Visualizer: React.FC<VisualizerProps> = ({ isActive, isThinkMode }) => {
  return (
    <div className="w-full h-full flex flex-col items-center justify-center relative">
      {isActive && (
        <div className="z-10 animate-fade-in text-center">
          <h2 className={`text-2xl font-bold tracking-[0.2em] uppercase transition-colors duration-500 ${isThinkMode ? 'text-violet-600' : 'text-slate-400'}`}>
            {isThinkMode ? 'Listening (TTS Active)' : 'Listening'}
          </h2>
        </div>
      )}

      {!isActive && (
        <div className="text-center">
          <div className="w-16 h-16 rounded-full border-2 border-slate-300/30 mx-auto mb-4" />
          <p className="text-slate-400/50 font-semibold">Ready to Connect</p>
        </div>
      )}
    </div>
  );
};