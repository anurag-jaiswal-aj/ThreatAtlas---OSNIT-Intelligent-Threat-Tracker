import type { Event } from '../types';

export interface WebSocketMessage {
  type: string;
  action?: string;
  event?: Event;
  message?: string;
}

type EventCallback = (event: Event, action: string) => void;
type StatusCallback = (connected: boolean) => void;

class RealtimeWebSocketService {
  private socket: WebSocket | null = null;
  private eventCallbacks: Set<EventCallback> = new Set();
  private statusCallbacks: Set<StatusCallback> = new Set();
  private pingInterval: any = null;
  private reconnectTimeout: any = null;
  private isExplicitlyClosed = false;

  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Fallback to localhost:8000 if running on dev server
    const host = window.location.port === '3000' ? 'localhost:8000' : window.location.host;
    return `${protocol}//${host}/api/v1/ws/events`;
  }

  public connect(): void {
    this.isExplicitlyClosed = false;
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const url = this.getWebSocketUrl();
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        console.log('[WebSocket] Real-time event stream connected.');
        this.notifyStatus(true);
        this.startHeartbeat();
      };

      this.socket.onmessage = (msg: MessageEvent) => {
        try {
          const data: WebSocketMessage = JSON.parse(msg.data);
          if (data.type === 'EVENT_CREATED' || data.type === 'EVENT_UPDATED' || data.type === 'EVENT_MERGED') {
            if (data.event) {
              const action = data.action || (data.type === 'EVENT_CREATED' ? 'created' : 'updated');
              this.notifyEvent(data.event, action);
            }
          }
        } catch (err) {
          console.warn('[WebSocket] Error parsing message:', err);
        }
      };

      this.socket.onerror = (err) => {
        console.warn('[WebSocket] Real-time stream error:', err);
      };

      this.socket.onclose = () => {
        console.log('[WebSocket] Real-time stream disconnected.');
        this.notifyStatus(false);
        this.stopHeartbeat();

        if (!this.isExplicitlyClosed) {
          this.scheduleReconnect();
        }
      };
    } catch (err) {
      console.warn('[WebSocket] Failed to initialize WebSocket connection:', err);
      this.scheduleReconnect();
    }
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true;
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.notifyStatus(false);
  }

  public subscribe(onEvent: EventCallback, onStatus?: StatusCallback): () => void {
    this.eventCallbacks.add(onEvent);
    if (onStatus) this.statusCallbacks.add(onStatus);

    // Auto-connect on first subscriber
    if (!this.socket || this.socket.readyState === WebSocket.CLOSED) {
      this.connect();
    }

    return () => {
      this.eventCallbacks.delete(onEvent);
      if (onStatus) this.statusCallbacks.delete(onStatus);
    };
  }

  private notifyEvent(event: Event, action: string): void {
    this.eventCallbacks.forEach((cb) => cb(event, action));
  }

  private notifyStatus(connected: boolean): void {
    this.statusCallbacks.forEach((cb) => cb(connected));
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.pingInterval = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send('ping');
      }
    }, 15000);
  }

  private stopHeartbeat(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeout) return;
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      console.log('[WebSocket] Reconnecting to real-time event stream...');
      this.connect();
    }, 5000);
  }
}

export const wsService = new RealtimeWebSocketService();
