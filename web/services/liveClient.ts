export class LiveClient {
  private websocket: WebSocket | null = null;
  private serverUrl: string;

  public onVolumeUpdate: ((vol: number) => void) | null = null;
  public onMessage: ((text: string, isUser: boolean) => void) | null = null;
  public onConnectChange: ((connected: boolean) => void) | null = null;

  constructor(serverUrl: string = 'ws://localhost:8768') {
    this.serverUrl = serverUrl;
  }

  async connect() {
    console.log("[WS] Connecting to", this.serverUrl);

    if (this.websocket) {
      console.log("[WS] Closing existing connection first");
      this.websocket.close();
      this.websocket = null;
    }

    try {
      this.websocket = new WebSocket(this.serverUrl);

      this.websocket.onopen = () => {
        console.log("[WS] Connected to Bridge Server");
        this.onConnectChange?.(true);
        this.send({ type: "sync" });
      };

      this.websocket.onmessage = (event) => {
        this.handleServerMessage(JSON.parse(event.data));
      };

      this.websocket.onclose = () => {
        console.log("[WS] Disconnected from Bridge Server");
        this.onConnectChange?.(false);
      };

      this.websocket.onerror = (e) => {
        console.error("[WS] WebSocket error", e);
        this.onConnectChange?.(false);
      };

      return true;
    } catch (err) {
      console.error("[WS] Failed to connect", err);
      return false;
    }
  }

  private handleServerMessage(message: any) {
    console.log("[WS] Received:", message);

    if (message.type === 'status') {
      this.onConnectChange?.(message.connected);
    }

    if (message.type === 'connection') {
      this.onConnectChange?.(message.status === 'connected');
    }

    if (message.type === 'text') {
      console.log("[WS] Text message:", message.text);
      this.onMessage?.(message.text, false);
    }

    if (message.type === 'volume') {
      this.onVolumeUpdate?.(message.level);
    }

    if (message.type === 'response') {
      console.log("[WS] Server response:", message.data);
    }
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

  sendText(text: string) {
    this.send({ type: 'text', text });
  }

  resync() {
    this.send({ type: 'sync' });
  }

  disconnect() {
    this.websocket?.close();
    this.websocket = null;
  }
}
