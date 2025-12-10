import React, { useState } from 'react';
import { Settings, Sliders, Volume2, Shield } from 'lucide-react';

export const SettingsButton: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="absolute bottom-6 left-6 z-40">
            <button 
                onClick={() => setIsOpen(!isOpen)}
                className={`p-3 rounded-full transition-all duration-300 shadow-lg ${isOpen ? 'bg-slate-800 text-white rotate-90' : 'bg-white text-slate-600 hover:bg-slate-50'}`}
            >
                <Settings size={20} />
            </button>

            {isOpen && (
                <div className="absolute bottom-14 left-0 w-64 bg-white/90 backdrop-blur-2xl border border-white/50 rounded-2xl shadow-2xl p-4 animate-slide-up origin-bottom-left">
                    <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-3">System Settings</h3>
                    
                    <div className="space-y-1">
                        <button className="w-full flex items-center space-x-3 p-2.5 rounded-xl hover:bg-slate-100 transition-colors text-left text-slate-700">
                            <Sliders size={16} />
                            <span className="text-xs font-medium">Model Parameters</span>
                        </button>
                        <button className="w-full flex items-center space-x-3 p-2.5 rounded-xl hover:bg-slate-100 transition-colors text-left text-slate-700">
                            <Volume2 size={16} />
                            <span className="text-xs font-medium">Audio Output</span>
                        </button>
                        <button className="w-full flex items-center space-x-3 p-2.5 rounded-xl hover:bg-slate-100 transition-colors text-left text-slate-700">
                            <Shield size={16} />
                            <span className="text-xs font-medium">Privacy & Data</span>
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};