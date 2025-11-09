/**
 * WebSocket Client for Real-time Stock Price Updates
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Connection state management
 * - Error handling and notifications
 * - Cookie-based authentication
 * - Memory leak prevention
 */

export enum ConnectionState {
  CONNECTING = "connecting",
  CONNECTED = "connected",
  DISCONNECTED = "disconnected",
  ERROR = "error",
  RECONNECTING = "reconnecting",
}

export interface StockPrice {
  company_id: number;
  ticker_symbol: string;
  company_name: string;
  current_price: number;
  change: number;
  change_percent: number;
  quantity?: number;
  purchase_price?: number;
  unrealized_pl?: number;
}

export interface PriceUpdateMessage {
  type: "price_update";
  watchlist_id: number;
  stocks: StockPrice[];
  timestamp: string;
}

export interface WebSocketClientOptions {
  watchlistId: number;
  onMessage: (message: PriceUpdateMessage) => void;
  onStateChange: (state: ConnectionState) => void;
  onError?: (error: Error) => void;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
}

/**
 * WebSocket client for real-time stock price updates
 *
 * Usage:
 * ```ts
 * const client = new WebSocketClient({
 *   watchlistId: 123,
 *   onMessage: (msg) => console.log(msg),
 *   onStateChange: (state) => console.log(state),
 * });
 * client.connect();
 * // ... later
 * client.disconnect();
 * ```
 */
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private options: Required<WebSocketClientOptions>;
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private isManualDisconnect = false;
  private currentState: ConnectionState = ConnectionState.DISCONNECTED;

  constructor(options: WebSocketClientOptions) {
    this.options = {
      ...options,
      maxReconnectAttempts: options.maxReconnectAttempts ?? 5,
      reconnectInterval: options.reconnectInterval ?? 3000,
      onError: options.onError ?? ((error) => console.error("WebSocket error:", error)),
    };
  }

  /**
   * Connect to WebSocket server
   */
  public connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn("[WebSocket] Already connected");
      return;
    }

    this.isManualDisconnect = false;
    this.setState(ConnectionState.CONNECTING);

    try {
      const wsUrl = this.buildWebSocketUrl();
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      this.handleError(error as Event);
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    this.isManualDisconnect = true;
    this.clearReconnectTimeout();

    if (this.ws) {
      this.ws.close(1000, "Client disconnected");
      this.ws = null;
    }

    this.setState(ConnectionState.DISCONNECTED);
  }

  /**
   * Get current connection state
   */
  public getState(): ConnectionState {
    return this.currentState;
  }

  /**
   * Check if WebSocket is connected
   */
  public isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Build WebSocket URL
   *
   * Authentication is handled via HttpOnly cookies sent automatically
   * by the browser in the WebSocket upgrade request headers.
   */
  private buildWebSocketUrl(): string {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const wsProtocol = baseUrl.startsWith("https") ? "wss" : "ws";
    const wsBaseUrl = baseUrl.replace(/^https?/, wsProtocol);

    // No token parameter needed - authentication uses HttpOnly cookies
    return `${wsBaseUrl}/api/v1/ws/watchlist/${this.options.watchlistId}/prices`;
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(): void {
    console.log("[WebSocket] Connected");
    this.reconnectAttempts = 0;
    this.setState(ConnectionState.CONNECTED);
  }

  /**
   * Handle WebSocket message event
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: PriceUpdateMessage = JSON.parse(event.data);

      if (message.type === "price_update") {
        this.options.onMessage(message);
      } else {
        console.warn("[WebSocket] Unknown message type:", message);
      }
    } catch (error) {
      console.error("[WebSocket] Failed to parse message:", error);
      this.options.onError?.(new Error("Failed to parse WebSocket message"));
    }
  }

  /**
   * Handle WebSocket error event
   */
  private handleError(event: Event): void {
    console.error("[WebSocket] Error:", event);
    this.setState(ConnectionState.ERROR);

    const error = new Error("WebSocket connection error");
    this.options.onError?.(error);
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(event: CloseEvent): void {
    console.log(`[WebSocket] Closed: code=${event.code}, reason=${event.reason}`);

    this.ws = null;

    // Don't reconnect if manually disconnected or max attempts reached
    if (this.isManualDisconnect) {
      this.setState(ConnectionState.DISCONNECTED);
      return;
    }

    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error("[WebSocket] Max reconnection attempts reached");
      this.setState(ConnectionState.ERROR);
      this.options.onError?.(new Error("Failed to reconnect after maximum attempts"));
      return;
    }

    // Attempt reconnection with exponential backoff
    this.attemptReconnect();
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    this.reconnectAttempts++;
    this.setState(ConnectionState.RECONNECTING);

    // Exponential backoff: 3s, 6s, 12s, 24s, 48s
    const delay = this.options.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts})...`
    );

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Clear reconnection timeout
   */
  private clearReconnectTimeout(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  /**
   * Set connection state and notify listeners
   */
  private setState(state: ConnectionState): void {
    if (this.currentState !== state) {
      this.currentState = state;
      this.options.onStateChange(state);
    }
  }
}
