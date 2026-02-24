/**
 * WebSocket client for real-time job status updates.
 */

import type { Job } from './api';

export interface WebSocketMessage {
  type: 'status' | 'status_update';
  data: Job;
}

type StatusCallback = (job: Job) => void;
type ErrorCallback = (error: Error) => void;

export class JobStatusWebSocket {
  private ws: WebSocket | null = null;
  private jobId: number | null = null;
  private token: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000; // Start with 2 seconds
  private maxReconnectDelay = 30000; // Max 30 seconds
  private isIntentionallyClosed = false;
  private statusCallback: StatusCallback | null = null;
  private errorCallback: ErrorCallback | null = null;

  /**
   * Connect to WebSocket for a specific job.
   */
  connect(jobId: number, token: string): void {
    if (this.ws) {
      this.disconnect();
    }

    // Store job ID and token for reconnection
    this.jobId = jobId;
    this.token = token;
    this.isIntentionallyClosed = false;

    const wsUrl = this.getWebSocketUrl(jobId, token);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log(`WebSocket connected for job ${this.jobId}`);
      this.reconnectAttempts = 0;
      this.reconnectDelay = 2000;
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        if (message.type === 'status' || message.type === 'status_update') {
          this.statusCallback?.(message.data);

          // Auto-close on terminal states
          if (message.data.status === 'success' || message.data.status === 'error') {
            setTimeout(() => {
              this.disconnect();
            }, 1000);
          }
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        this.errorCallback?.(error as Error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.errorCallback?.(new Error('WebSocket connection error'));
    };

    this.ws.onclose = (event) => {
      console.log(`WebSocket closed for job ${this.jobId}:`, event.code, event.reason);

      // Attempt to reconnect if not intentionally closed and not a policy error
      if (
        !this.isIntentionallyClosed &&
        this.reconnectAttempts < this.maxReconnectAttempts &&
        event.code !== 1008 // Policy violation (auth failure)
      ) {
        this.reconnectAttempts++;
        const delay = Math.min(
          this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
          this.maxReconnectDelay
        );

        console.log(`Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
          if (!this.isIntentionallyClosed && this.jobId !== null && this.token !== null) {
            this.connect(this.jobId, this.token);
          }
        }, delay);
      } else if (event.code === 1008) {
        // Auth failure - don't retry
        this.errorCallback?.(new Error('Authentication failed'));
      }
    };
  }

  /**
   * Disconnect from WebSocket.
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Register callback for status updates.
   */
  onStatusChange(callback: StatusCallback): void {
    this.statusCallback = callback;
  }

  /**
   * Register callback for errors.
   */
  onError(callback: ErrorCallback): void {
    this.errorCallback = callback;
  }

  /**
   * Get WebSocket URL for a specific job.
   */
  private getWebSocketUrl(jobId: number, token: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/api/ws/job/${jobId}?token=${encodeURIComponent(token)}`;
  }

  /**
   * Check if WebSocket is connected.
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}
