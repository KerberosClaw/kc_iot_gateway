import { useState, useEffect } from 'react';
import { AlertTriangle, AlertCircle, Info, RefreshCw } from 'lucide-react';
import { fetchAlerts, type Alert } from '../lib/api';
import { t, type Lang } from '../lib/i18n';

const SEVERITY_CONFIG: Record<string, { border: string; icon: typeof AlertTriangle; color: string }> = {
  critical: { border: 'var(--red)', icon: AlertTriangle, color: 'var(--red)' },
  warning: { border: 'var(--yellow)', icon: AlertCircle, color: 'var(--yellow)' },
  info: { border: 'var(--blue)', icon: Info, color: 'var(--blue)' },
};

const MOCK_ALERTS: Alert[] = [
  { id: 1, rule_name: 'high_temperature', device_id: 'factory_temp_01', severity: 'critical', message: 'high_temperature: temperature=36.2', value: '36.2', created_at: Date.now() / 1000 - 120 },
  { id: 2, rule_name: 'pump_auto_control', device_id: 'plc_01', severity: 'info', message: 'pump_auto_control: temperature=29.1', value: '29.1', created_at: Date.now() / 1000 - 300 },
  { id: 3, rule_name: 'plc_high_temp', device_id: 'plc_01', severity: 'warning', message: 'plc_high_temp: temperature=31.5', value: '31.5', created_at: Date.now() / 1000 - 600 },
];

export function AlertsPanel({ lang, isDemo = false }: { lang: Lang; isDemo?: boolean }) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filter, setFilter] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const load = async () => {
    if (isDemo) {
      const filtered = filter ? MOCK_ALERTS.filter(a => a.severity === filter) : MOCK_ALERTS;
      setAlerts(filtered);
      return;
    }
    setLoading(true);
    setAlerts(await fetchAlerts(filter || undefined));
    setLoading(false);
  };

  useEffect(() => { load(); }, [filter, isDemo]);
  useEffect(() => {
    if (isDemo) return;
    const i = setInterval(load, 5000);
    return () => clearInterval(i);
  }, [filter, isDemo]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold" style={{ color: 'var(--text-secondary)' }}>{t('alerts.title', lang)}</h2>
        <div className="flex items-center gap-2">
          <select className="rounded-md px-3 py-1.5 text-sm" style={{ background: 'var(--bg-field)', border: '1px solid var(--border-light)', color: 'var(--text)' }} value={filter} onChange={e => setFilter(e.target.value)}>
            <option value="">{t('alerts.all', lang)}</option>
            <option value="critical">{t('alerts.critical', lang)}</option>
            <option value="warning">{t('alerts.warning', lang)}</option>
            <option value="info">{t('alerts.info', lang)}</option>
          </select>
          {!isDemo && (
            <button className="p-1.5 rounded-md transition" style={{ background: 'var(--bg-field)', border: '1px solid var(--border-light)', color: 'var(--text-secondary)' }} onClick={load}>
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          )}
        </div>
      </div>

      {!alerts.length && <div className="text-center py-20" style={{ color: 'var(--text-muted)' }}>{t('alerts.empty', lang)}</div>}

      <div className="space-y-2">
        {alerts.map(alert => {
          const cfg = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.info;
          const Icon = cfg.icon;
          return (
            <div key={alert.id} className="rounded-r-md p-3" style={{ background: 'var(--bg-card)', borderLeft: `4px solid ${cfg.border}` }}>
              <div className="flex items-start gap-2">
                <Icon size={16} style={{ color: cfg.color, marginTop: 2, flexShrink: 0 }} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm">{alert.rule_name}</span>
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{new Date(alert.created_at * 1000).toLocaleString()}</span>
                  </div>
                  <div className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>{alert.device_id} &mdash; {alert.message}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
