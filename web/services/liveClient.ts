export class LiveClient {
  private websocket: WebSocket | null = null;
  private outputAudioContext: AudioContext | null = null;
  private outputNode: GainNode | null = null;
  private nextStartTime = 0;
  private sources = new Set<AudioBufferSourceNode>();
  private serverUrl: string;
  private audioStream: MediaStream | null = null;
  private audioProcessor: ScriptProcessorNode | null = null;
  private inputAudioContext: AudioContext | null = null;

  public onVolumeUpdate: ((vol: number) => void) | null = null;
  public onMessage: ((text: string, isUser: boolean) => void) | null = null;
  public onConnectChange: ((connected: boolean) => void) | null = null;

  constructor(serverUrl: string = 'ws://localhost:8768') {
    this.serverUrl = serverUrl;
  }

  async connect() {
    this.outputAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
    this.outputNode = this.outputAudioContext.createGain();
    this.outputNode.connect(this.outputAudioContext.destination);

    try {
      this.websocket = new WebSocket(this.serverUrl);

      this.websocket.onopen = () => {
        console.log("Connected to Bridge Server");
        this.send({ type: "sync" });
      };

      this.websocket.onmessage = (event) => {
        this.handleServerMessage(JSON.parse(event.data));
      };

      this.websocket.onclose = () => {
        console.log("Disconnected from Bridge Server");
        this.onConnectChange?.(false);
        this.cleanup();
      };

      this.websocket.onerror = (e) => {
        console.error("WebSocket error", e);
        this.onConnectChange?.(false);
      };

      return true;
    } catch (err) {
      console.error("Failed to connect", err);
      return false;
    }
  }

  private async handleServerMessage(message: any) {
    if (message.type === 'connection') {
      const connected = message.status === 'connected';
      this.onConnectChange?.(connected);
      if (connected) {
        await this.startAudioCapture();
      }
    }

    if (message.type === 'text') {
      this.onMessage?.(message.text, false);
    }

    if (message.type === 'audio' && message.audio_base64) {
      this.onVolumeUpdate?.(0.5 + Math.random() * 0.5);

      const audioBuffer = await this.decodeAudioData(message.audio_base64);

      if (this.outputAudioContext && this.outputNode) {
        this.nextStartTime = Math.max(this.nextStartTime, this.outputAudioContext.currentTime);

        const source = this.outputAudioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.outputNode);
        source.start(this.nextStartTime);

        this.nextStartTime += audioBuffer.duration;
        this.sources.add(source);

        source.onended = () => {
          this.sources.delete(source);
          if (this.sources.size === 0) this.onVolumeUpdate?.(0);
        };
      }
    }
  }

  private async startAudioCapture() {
    try {
      this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.inputAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });

      const source = this.inputAudioContext.createMediaStreamSource(this.audioStream);
      this.audioProcessor = this.inputAudioContext.createScriptProcessor(4096, 1, 1);

      this.audioProcessor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);

        let sum = 0;
        for (let i = 0; i < inputData.length; i++) sum += inputData[i] * inputData[i];
        const vol = Math.sqrt(sum / inputData.length);
        this.onVolumeUpdate?.(vol * 5);

        const pcmData = this.float32ToPcmBase64(inputData);
        this.send({ type: 'audio', audio_base64: pcmData });
      };

      source.connect(this.audioProcessor);
      this.audioProcessor.connect(this.inputAudioContext.destination);
    } catch (e) {
      console.error("Failed to start audio capture", e);
    }
  }

  private float32ToPcmBase64(data: Float32Array): string {
    const int16 = new Int16Array(data.length);
    for (let i = 0; i < data.length; i++) {
      int16[i] = Math.max(-1, Math.min(1, data[i])) * 32768;
    }
    const bytes = new Uint8Array(int16.buffer);

    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  private async decodeAudioData(base64: string): Promise<AudioBuffer> {
    const binaryString = atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    const dataInt16 = new Int16Array(bytes.buffer);
    const float32 = new Float32Array(dataInt16.length);
    for (let i = 0; i < dataInt16.length; i++) {
      float32[i] = dataInt16[i] / 32768.0;
    }

    if (!this.outputAudioContext) throw new Error("No output context");

    const buffer = this.outputAudioContext.createBuffer(1, float32.length, 24000);
    buffer.copyToChannel(float32, 0);
    return buffer;
  }

  send(data: any) {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(data));
    }
  }

  toggleMic(enabled: boolean) {
    this.send({ type: 'toggle_mic', enabled });
  }

  toggleCam(enabled: boolean) {
    this.send({ type: 'toggle_cam', enabled });
  }

  toggleThink(enabled: boolean) {
    this.send({ type: 'toggle_think', enabled });
  }

  showFeed() {
    this.send({ type: 'show_feed' });
  }

  sendVideoFrame(base64Data: string) {
    this.send({ type: 'video_frame', frame_base64: base64Data });
  }

  sendText(text: string) {
    this.send({ type: 'text', text });
  }

  resync() {
    this.send({ type: 'sync' });
  }

  disconnect() {
    this.cleanup();
    this.websocket?.close();
  }

  private cleanup() {
    this.audioProcessor?.disconnect();
    this.inputAudioContext?.close();
    this.outputAudioContext?.close();
    this.audioStream?.getTracks().forEach(t => t.stop());
    this.sources.forEach(s => s.stop());
    this.sources.clear();
    this.websocket = null;
    this.inputAudioContext = null;
    this.outputAudioContext = null;
  }
}
