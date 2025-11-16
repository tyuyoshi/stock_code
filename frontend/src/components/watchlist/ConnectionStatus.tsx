/**
 * Connection Status Indicator
 *
 * Displays the current WebSocket connection state with appropriate
 * icons and colors for user feedback.
 */

import React from "react";
import { ConnectionState } from "@/lib/websocket";
import { Wifi, WifiOff, Loader2, AlertCircle } from "lucide-react";

export interface ConnectionStatusProps {
  /** Current connection state */
  state: ConnectionState;
  /** Optional error message */
  error?: Error | null;
  /** Show detailed status text (default: true) */
  showText?: boolean;
  /** Compact mode (smaller size, default: false) */
  compact?: boolean;
}

/**
 * Connection Status Indicator Component
 *
 * Displays the WebSocket connection status with visual feedback
 */
export const ConnectionStatus = React.memo<ConnectionStatusProps>(
  ({ state, error, showText = true, compact = false }) => {
    const getStatusConfig = () => {
      switch (state) {
        case ConnectionState.CONNECTED:
          return {
            icon: Wifi,
            color: "text-green-600",
            bgColor: "bg-green-50",
            text: "リアルタイム接続中",
            pulse: false,
          };
        case ConnectionState.CONNECTING:
          return {
            icon: Loader2,
            color: "text-blue-600",
            bgColor: "bg-blue-50",
            text: "接続中...",
            pulse: true,
          };
        case ConnectionState.RECONNECTING:
          return {
            icon: Loader2,
            color: "text-yellow-600",
            bgColor: "bg-yellow-50",
            text: "再接続中...",
            pulse: true,
          };
        case ConnectionState.ERROR:
          return {
            icon: AlertCircle,
            color: "text-red-600",
            bgColor: "bg-red-50",
            text: error?.message || "接続エラー",
            pulse: false,
          };
        case ConnectionState.DISCONNECTED:
        default:
          return {
            icon: WifiOff,
            color: "text-gray-600",
            bgColor: "bg-gray-50",
            text: "未接続",
            pulse: false,
          };
      }
    };

    const config = getStatusConfig();
    const Icon = config.icon;
    const size = compact ? "h-4 w-4" : "h-5 w-5";

    return (
      <div
        className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 ${config.bgColor} ${compact ? "text-xs" : "text-sm"}`}
      >
        <Icon
          className={`${size} ${config.color} ${config.pulse ? "animate-spin" : ""}`}
        />
        {showText && (
          <span className={`font-medium ${config.color}`}>{config.text}</span>
        )}
      </div>
    );
  }
);

ConnectionStatus.displayName = "ConnectionStatus";
