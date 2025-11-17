/**
 * WebSocket service for real-time communication with Agent_Q backend
 */

export interface Message {
  type: 'chat_message' | 'ping';
  message?: string;
  project_id?: string;
  access_token?: string;
}

export interface ServerMessage {
  type: 'connected' | 'agent_response' | 'agent_thinking' | 'error' | 'pong' | 'screenshot' | 'code_generated';
  content: string;
  timestamp: string;
  imageUrl?: string;
  imageCaption?: string;
  code?: string;
}

export type MessageHandler = (message: ServerMessage) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private clientId: string;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 2000;
  private messageHandlers: Set<MessageHandler> = new Set();
  private isIntentionalDisconnect: boolean = false;

  constructor(baseUrl: string = 'ws://localhost:8000') {
    this.clientId = this.generateClientId();
    this.url = `${baseUrl}/api/v1/ws/${this.clientId}`;
  }

  private generateClientId(): string {
    return `ext_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected to backend');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: ServerMessage = JSON.parse(event.data);
            console.log('[WebSocket] Received:', message.type);
            this.notifyHandlers(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('[WebSocket] Disconnected');
          if (!this.isIntentionalDisconnect) {
            this.attemptReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnect attempts reached');
      this.notifyHandlers({
        type: 'error',
        content: 'Failed to connect to backend after multiple attempts',
        timestamp: new Date().toISOString()
      });
      return;
    }

    this.reconnectAttempts++;
    console.log(`[WebSocket] Reconnecting... Attempt ${this.reconnectAttempts}`);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('[WebSocket] Reconnect failed:', error);
      });
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  sendMessage(message: Message): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      console.log('[WebSocket] Sent:', message.type);
    } else {
      console.error('[WebSocket] Cannot send message: WebSocket is not connected');
      this.notifyHandlers({
        type: 'error',
        content: 'Not connected to backend. Please refresh.',
        timestamp: new Date().toISOString()
      });
    }
  }

  sendChatMessage(text: string, projectId: string = 'default', accessToken: string = 'default'): void {
    this.sendMessage({
      type: 'chat_message',
      message: text,
      project_id: projectId,
      access_token: accessToken
    });
  }

  ping(): void {
    this.sendMessage({ type: 'ping' });
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  private notifyHandlers(message: ServerMessage): void {
    this.messageHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('[WebSocket] Handler error:', error);
      }
    });
  }

  disconnect(): void {
    this.isIntentionalDisconnect = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export const websocketService = new WebSocketService();
