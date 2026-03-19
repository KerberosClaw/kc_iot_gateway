import { useState, useEffect, useRef } from 'react';
import type { DeviceData } from '../lib/api';

const MOCK_DEVICES: DeviceData[] = [
  {
    device_id: 'factory_temp_01',
    name: '廠區溫度感測器',
    protocol: 'mqtt',
    fields: { temperature: 25.0, humidity: 55.0 },
    online: true,
    last_update: Date.now() / 1000,
  },
  {
    device_id: 'plc_01',
    name: '產線 PLC',
    protocol: 'modbus',
    fields: { temperature: 26.0, humidity: 50.0, motor_speed: 1200, pump_on: false },
    online: true,
    last_update: Date.now() / 1000,
  },
  {
    device_id: 'env_sensor_01',
    name: '環境感測器（廠商 A）',
    protocol: 'webhook',
    fields: { temperature: 23.5, humidity: 62.0, battery: 87 },
    online: true,
    last_update: Date.now() / 1000,
  },
  {
    device_id: 'door_sensor_01',
    name: '門禁感測器（廠商 B）',
    protocol: 'webhook',
    fields: { status: 'closed' },
    online: true,
    last_update: Date.now() / 1000,
  },
];

export function useDemoMode() {
  const [devices, setDevices] = useState<Record<string, DeviceData>>({});
  const [history, setHistory] = useState<Record<string, { time: number; values: Record<string, number> }[]>>({});
  const startTime = useRef(Date.now());

  useEffect(() => {
    // Init devices
    const devMap: Record<string, DeviceData> = {};
    MOCK_DEVICES.forEach(d => { devMap[d.device_id] = { ...d }; });
    setDevices(devMap);

    // Simulate data updates
    const interval = setInterval(() => {
      const elapsed = (Date.now() - startTime.current) / 1000;

      setDevices(prev => {
        const next = { ...prev };

        // MQTT sensor - sine wave
        if (next['factory_temp_01']) {
          const temp = 25 + 5 * Math.sin(elapsed * 0.1) + (Math.random() - 0.5);
          const hum = 55 + 8 * Math.sin(elapsed * 0.07) + (Math.random() - 0.5) * 2;
          next['factory_temp_01'] = {
            ...next['factory_temp_01'],
            fields: { temperature: Math.round(temp * 100) / 100, humidity: Math.round(hum * 100) / 100 },
            last_update: Date.now() / 1000,
          };
        }

        // Modbus PLC
        if (next['plc_01']) {
          const temp = 26 + 4 * Math.sin(elapsed * 0.08) + (Math.random() - 0.5);
          const hum = 50 + 6 * Math.sin(elapsed * 0.06) + (Math.random() - 0.5) * 2;
          next['plc_01'] = {
            ...next['plc_01'],
            fields: {
              ...next['plc_01'].fields,
              temperature: Math.round(temp * 100) / 100,
              humidity: Math.round(hum * 100) / 100,
            },
            last_update: Date.now() / 1000,
          };
        }

        return next;
      });

      // Update history
      setHistory(prev => {
        const next = { ...prev };
        const now = Date.now();
        const elapsed2 = (now - startTime.current) / 1000;

        for (const id of ['factory_temp_01', 'plc_01']) {
          const existing = next[id] || [];
          const values: Record<string, number> = {};
          if (id === 'factory_temp_01') {
            values.temperature = Math.round((25 + 5 * Math.sin(elapsed2 * 0.1)) * 100) / 100;
            values.humidity = Math.round((55 + 8 * Math.sin(elapsed2 * 0.07)) * 100) / 100;
          } else {
            values.temperature = Math.round((26 + 4 * Math.sin(elapsed2 * 0.08)) * 100) / 100;
            values.humidity = Math.round((50 + 6 * Math.sin(elapsed2 * 0.06)) * 100) / 100;
          }
          next[id] = [...existing, { time: now, values }].slice(-60);
        }

        return next;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return { devices, history, connected: true };
}
