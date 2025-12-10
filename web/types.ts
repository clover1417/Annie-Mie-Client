export interface Message {
  id: string;
  role: 'user' | 'model' | 'system';
  text: string;
  timestamp: Date;
}

export interface AttachedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  data: string; // Base64
}

export interface LiveConfig {
  model: string;
  voiceName: string;
  systemInstruction: string;
}
