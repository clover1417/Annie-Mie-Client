import React, { useEffect, useState, useRef, useCallback } from 'react';
import { LiveClient } from './services/liveClient';
import { StatusPanel } from './components/StatusPanel';
import { ControlPanel } from './components/ControlPanel';
import { ChatBar } from './components/ChatBar';
import { Avatar3D } from './components/Avatar3D';
import { SettingsButton } from './components/SettingsButton';
import { AttachedFile } from './types';
import { ServerSimulator } from './components/ServerSimulator';

const DISPLAY_MODEL_NAME = "Qwen3-Omni-30B-A3B-Instruct";
const BRIDGE_SERVER_URL = "ws://localhost:8768";

const App: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [micOn, setMicOn] = useState(false);
  const [camOn, setCamOn] = useState(true);
  const [thinkMode, setThinkMode] = useState(false);
  const [audioVolume, setAudioVolume] = useState(0);

  const [micName, setMicName] = useState("Default Microphone");
  const [camName, setCamName] = useState("Camera 0");

  const [simulatorMessages, setSimulatorMessages] = useState<any[]>([]);

  const liveClientRef = useRef<LiveClient | null>(null);

  useEffect(() => {
    const client = new LiveClient(BRIDGE_SERVER_URL);
    liveClientRef.current = client;

    client.onVolumeUpdate = (vol) => setAudioVolume(vol);
    client.onConnectChange = (isConnected) => {
      setConnected(isConnected);
      if (isConnected) {
        client.loadSimulatorMessages();
      }
    };

    client.onSimulatorMessagesLoaded = (messages) => {
      setSimulatorMessages(messages);
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
      liveClientRef.current?.resync();
    } else {
      liveClientRef.current?.connect();
    }
  }, [connected]);

  const handleSendMessage = (text: string, files: AttachedFile[]) => {
    liveClientRef.current?.sendText(text);
  };

  const handleSaveSimulatorMessages = useCallback((messages: any[]) => {
    liveClientRef.current?.saveSimulatorMessages(messages);
  }, []);

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-white font-sans selection:bg-blue-100 selection:text-blue-900">

      <main className="absolute inset-0 z-10">
        <Avatar3D />
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

      <ServerSimulator
        onSimulate={(text, rate, latency) => {
          liveClientRef.current?.simulateServerMessage(text, rate, latency);
        }}
        onSaveMessages={handleSaveSimulatorMessages}
        initialMessages={simulatorMessages}
      />

    </div>
  );
};

export default App;