import React, { useEffect, useState, useRef, useCallback } from 'react';
import { LiveClient } from './services/liveClient';
import { StatusPanel } from './components/StatusPanel';
import { ControlPanel } from './components/ControlPanel';
import { ChatBar } from './components/ChatBar';
import { Visualizer } from './components/Visualizer';
import { SettingsButton } from './components/SettingsButton';
import { AttachedFile } from './types';

const DISPLAY_MODEL_NAME = "Qwen3-Omni-30B-A3B-Instruct";
const BRIDGE_SERVER_URL = "ws://localhost:8768";

const App: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [micOn, setMicOn] = useState(false);
  const [camOn, setCamOn] = useState(false);
  const [thinkMode, setThinkMode] = useState(false);
  const [audioVolume, setAudioVolume] = useState(0);

  const [micName, setMicName] = useState("Default Microphone");
  const [camName, setCamName] = useState("Camera 0");

  const liveClientRef = useRef<LiveClient | null>(null);

  useEffect(() => {
    const client = new LiveClient(BRIDGE_SERVER_URL);
    liveClientRef.current = client;

    client.onVolumeUpdate = (vol) => setAudioVolume(vol);
    client.onConnectChange = (isConnected) => {
      setConnected(isConnected);
      if (isConnected) {
        setMicOn(true);
        client.toggleMic(true);
      } else {
        setMicOn(false);
      }
    };

    navigator.mediaDevices.enumerateDevices().then(devices => {
      const audio = devices.find(d => d.kind === 'audioinput');
      const video = devices.find(d => d.kind === 'videoinput');
      if (audio) setMicName(audio.label || "USB Microphone");
      if (video) setCamName(video.label || "Webcam 0");
    });

    client.connect();

    return () => {
      client.disconnect();
    };
  }, []);

  const handleToggleMic = useCallback(() => {
    const newState = !micOn;
    setMicOn(newState);
    liveClientRef.current?.toggleMic(newState);
  }, [micOn]);

  const handleToggleCam = useCallback(() => {
    const newState = !camOn;
    setCamOn(newState);
    liveClientRef.current?.toggleCam(newState);
  }, [camOn]);

  const handleToggleThink = useCallback(() => {
    const newState = !thinkMode;
    setThinkMode(newState);
    liveClientRef.current?.toggleThink(newState);
  }, [thinkMode]);

  const handleShowFeed = useCallback(() => {
    liveClientRef.current?.showFeed();
  }, []);

  const toggleConnection = useCallback(() => {
    if (connected) {
      liveClientRef.current?.disconnect();
      setConnected(false);
    } else {
      liveClientRef.current?.resync();
    }
  }, [connected]);

  const handleSendMessage = (text: string, files: AttachedFile[]) => {
    liveClientRef.current?.sendText(text);
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-slate-50 font-sans selection:bg-blue-100 selection:text-blue-900">

      <div className={`absolute inset-0 transition-opacity duration-[2000ms] ${connected ? 'opacity-100' : 'opacity-0'}`}>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-200/30 rounded-full blur-[100px] animate-pulse-slow pointer-events-none mix-blend-multiply" />
        <div className="absolute top-1/3 left-1/3 w-[600px] h-[600px] bg-blue-200/30 rounded-full blur-[120px] pointer-events-none mix-blend-multiply" />
      </div>

      <main className="absolute inset-0 flex flex-col items-center justify-center z-10 pointer-events-none">
        <Visualizer
          volume={audioVolume}
          isActive={connected}
          isThinkMode={thinkMode}
        />
      </main>

      <StatusPanel
        connected={connected}
        micName={micName}
        camName={camName}
        fps={camOn ? 30 : 0}
        modelName={DISPLAY_MODEL_NAME}
        onSync={toggleConnection}
      />

      <ControlPanel
        isCamOn={camOn}
        isMicOn={micOn}
        isThinkMode={thinkMode}
        onToggleCam={handleToggleCam}
        onToggleMic={handleToggleMic}
        onToggleThink={handleToggleThink}
        onShowFeed={handleShowFeed}
      />

      <SettingsButton />

      <ChatBar
        disabled={micOn}
        onSendMessage={handleSendMessage}
      />

    </div>
  );
};

export default App;