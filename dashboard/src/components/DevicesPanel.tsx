import { useState } from 'react';
import { Activity, Wifi, WifiOff, Gauge, Thermometer, Droplets, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { DeviceData } from '../lib/api';
import { writeDevice } from '../lib/api';
import { t, fieldLabel, type Lang } from '../lib/i18n';

interface Props {
  devices: Record<string, DeviceData>;
  history: Record<string, { time: number; values: Record<string, number> }[]>;
  lang: Lang;
}

const FIELD_ICONS: Record<string, typeof Thermometer> = {
  temperature: Thermometer, humidity: Droplets, motor_speed: Gauge, pressure: Gauge, battery: Zap,
};
const CHART_COLORS = ['#4ade80', '#60a5fa', '#f59e0b', '#a78bfa', '#fb7185'];

export function DevicesPanel({ devices, history, lang }: Props) {
  const deviceList = Object.values(devices);
  if (!deviceList.length) {
    return <div className="text-center py-20" style={{ color: 'var(--text-muted)' }}>{t('devices.empty', lang)}</div>;
  }
  return (
    <div className="space-y-4">
      {deviceList.map(device => (
        <DeviceCard key={device.device_id} device={device} history={history[device.device_id] || []} lang={lang} />
      ))}
    </div>
  );
}

function DeviceCard({ device, history, lang }: { device: DeviceData; history: { time: number; values: Record<string, number> }[]; lang: Lang }) {
  const [expanded, setExpanded] = useState(false);
  const [writing, setWriting] = useState<string | null>(null);
  const [writeValue, setWriteValue] = useState('');

  const handleWrite = async (field: string) => {
    let val: unknown = writeValue;
    if (writeValue === 'true') val = true;
    else if (writeValue === 'false') val = false;
    else if (!isNaN(Number(writeValue))) val = Number(writeValue);
    await writeDevice(device.device_id, { [field]: val });
    setWriting(null);
    setWriteValue('');
  };

  const numericFields = Object.entries(device.fields).filter(([, v]) => typeof v === 'number');
  const chartData = history.map(h => ({ time: new Date(h.time).toLocaleTimeString(), ...h.values }));

  return (
    <div className="rounded-lg overflow-hidden" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <div className="flex items-center justify-between px-4 py-3 cursor-pointer transition" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3">
          {device.online ? <Wifi size={16} style={{ color: 'var(--green)' }} /> : <WifiOff size={16} style={{ color: 'var(--red)' }} />}
          <span className="font-semibold">{device.name}</span>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{device.device_id}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2 py-0.5 rounded" style={{ background: 'var(--blue-bg)', color: 'var(--blue)' }}>{device.protocol}</span>
          <Activity size={14} className={`transition ${expanded ? 'rotate-180' : ''}`} style={{ color: 'var(--text-muted)' }} />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 px-4 pb-3">
        {Object.entries(device.fields).map(([name, value]) => {
          const Icon = FIELD_ICONS[name] || Activity;
          const isWritable = typeof value === 'boolean' || name === 'motor_speed';
          return (
            <div key={name} className="rounded-md p-3" style={{ background: 'var(--bg-field)' }}>
              <div className="flex items-center gap-1 text-xs uppercase mb-1" style={{ color: 'var(--text-muted)' }}>
                <Icon size={12} />{fieldLabel(name, lang)}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                  {typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(2)) : typeof value === 'boolean' ? (value ? 'ON' : 'OFF') : String(value)}
                </span>
                {isWritable && writing !== name && (
                  <button className="text-xs px-2 py-0.5 rounded transition" style={{ background: 'var(--border)', color: 'var(--text-secondary)' }}
                    onClick={(e) => { e.stopPropagation(); setWriting(name); setWriteValue(String(value)); }}>{t('devices.set', lang)}</button>
                )}
              </div>
              {writing === name && (
                <div className="flex gap-1 mt-2" onClick={e => e.stopPropagation()}>
                  {typeof value === 'boolean' ? (
                    <select className="flex-1 rounded px-2 py-1 text-sm" style={{ background: 'var(--border)', border: '1px solid var(--border-light)', color: 'var(--text)' }} value={writeValue} onChange={e => setWriteValue(e.target.value)}>
                      <option value="true">ON</option><option value="false">OFF</option>
                    </select>
                  ) : (
                    <input type="number" className="flex-1 rounded px-2 py-1 text-sm w-20" style={{ background: 'var(--border)', border: '1px solid var(--border-light)', color: 'var(--text)' }} value={writeValue} onChange={e => setWriteValue(e.target.value)} autoFocus />
                  )}
                  <button className="px-2 py-1 rounded text-xs font-semibold" style={{ background: 'var(--green-bg)', color: 'var(--green)' }} onClick={() => handleWrite(name)}>OK</button>
                  <button className="px-2 py-1 rounded text-xs" style={{ background: 'var(--border)', color: 'var(--text-secondary)' }} onClick={() => setWriting(null)}>X</button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {expanded && chartData.length > 2 && (
        <div className="px-4 pb-4">
          <div className="rounded-md p-3" style={{ background: 'var(--bg-field)' }}>
            <div className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>{t('devices.realtime', lang)}</div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
                <Tooltip contentStyle={{ background: 'var(--bg-field)', border: '1px solid var(--border-light)', borderRadius: 6, fontSize: 12 }} labelStyle={{ color: 'var(--text-secondary)' }} />
                {numericFields.map(([name], i) => (
                  <Line key={name} type="monotone" dataKey={name} stroke={CHART_COLORS[i % CHART_COLORS.length]} dot={false} strokeWidth={2} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
