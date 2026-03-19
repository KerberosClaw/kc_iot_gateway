import { useEffect, useRef, useCallback, useState } from 'react';
import type { DeviceData } from '../lib/api';

interface WSMessage {
  type: 'init' | 'device_update' | 'alert';
  devices?: DeviceData[];
  device_id?: string;
  data?: Record<string, unknown>;
}

export function useWebSocket() {
  const [devices, setDevices] = useState<Record<string, DeviceData>>({});
  const [connected, setConnected] = useState(false);
  const [history, setHistory] = useState<Record<string, { time: number; values: Record<string, number> }[]>>({});
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${proto}//${location.host}/ws`);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      setTimeout(connect, 3000);
    };

    ws.onmessage = (e) => {
      const msg: WSMessage = JSON.parse(e.data);

      if (msg.type === 'init' && msg.devices) {
        const devMap: Record<string, DeviceData> = {};
        msg.devices.forEach(d => { devMap[d.device_id] = d; });
        setDevices(devMap);
      }

      if (msg.type === 'device_update' && msg.device_id && msg.data) {
        const id = msg.device_id;
        const data = msg.data;

        setDevices(prev => {
          const existing = prev[id];
          if (!existing) return prev;
          return {
            ...prev,
            [id]: {
              ...existing,
              fields: { ...existing.fields, ...data } as DeviceData['fields'],
              online: true,
              last_update: Date.now() / 1000,
            },
          };
        });

        // Append to history for charts (keep last 60 data points)
        setHistory(prev => {
          const numericData: Record<string, number> = {};
          for (const [k, v] of Object.entries(data)) {
            if (typeof v === 'number') numericData[k] = v;
          }
          if (Object.keys(numericData).length === 0) return prev;

          const existing = prev[id] || [];
          const updated = [...existing, { time: Date.now(), values: numericData }];
          return { ...prev, [id]: updated.slice(-60) };
        });
      }
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => { wsRef.current?.close(); };
  }, [connect]);

  return { devices, connected, history };
}
