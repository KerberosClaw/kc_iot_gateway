import { useState, useEffect } from 'react';
import { Send, Radio } from 'lucide-react';
import { fetchWebhookDevices, sendWebhook, type WebhookDevice } from '../lib/api';
import { t, fieldLabel, type Lang } from '../lib/i18n';

export function WebhookSimPanel({ lang }: { lang: Lang }) {
  const [devices, setDevices] = useState<WebhookDevice[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<string>('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    fetchWebhookDevices().then(devs => {
      setDevices(devs);
      if (devs.length) { setSelected(devs[0].id); initValues(devs[0]); }
    });
  }, []);

  const initValues = (dev: WebhookDevice) => {
    const vals: Record<string, string> = {};
    for (const [name, cfg] of Object.entries(dev.fields)) {
      if (cfg.type === 'float') vals[name] = (20 + Math.random() * 10).toFixed(1);
      else if (cfg.type === 'int') vals[name] = String(Math.floor(50 + Math.random() * 50));
      else if (cfg.type === 'bool') vals[name] = 'true';
      else vals[name] = 'open';
    }
    setValues(vals);
  };

  const handleSelectChange = (id: string) => {
    setSelected(id);
    const dev = devices.find(d => d.id === id);
    if (dev) initValues(dev);
    setResult('');
  };

  const handleSend = async () => {
    const dev = devices.find(d => d.id === selected);
    if (!dev) return;
    setSending(true);
    const payload: Record<string, unknown> = {};

    const idPath = dev.identity.field.replace('$.', '').split('.');
    let obj: Record<string, unknown> = payload;
    for (let i = 0; i < idPath.length - 1; i++) { obj[idPath[i]] = obj[idPath[i]] || {}; obj = obj[idPath[i]] as Record<string, unknown>; }
    obj[idPath[idPath.length - 1]] = dev.identity.value;

    for (const [name, cfg] of Object.entries(dev.fields)) {
      const raw = values[name] || '';
      let val: unknown = raw;
      if (cfg.type === 'float') val = parseFloat(raw);
      else if (cfg.type === 'int') val = parseInt(raw);
      else if (cfg.type === 'bool') val = raw === 'true';
      const dataPath = cfg.path.replace('$.', '').split('.');
      let target: Record<string, unknown> = payload;
      for (let i = 0; i < dataPath.length - 1; i++) { target[dataPath[i]] = target[dataPath[i]] || {}; target = target[dataPath[i]] as Record<string, unknown>; }
      target[dataPath[dataPath.length - 1]] = val;
    }

    try {
      const resp = await sendWebhook(payload);
      setResult(`Sent:\n${JSON.stringify(payload, null, 2)}\n\nResponse:\n${JSON.stringify(resp, null, 2)}`);
    } catch (e) { setResult(`Error: ${e}`); }
    setSending(false);
  };

  if (!devices.length) {
    return <div className="text-center py-20" style={{ color: 'var(--text-muted)' }}>{t('webhook.empty', lang)}</div>;
  }

  const currentDev = devices.find(d => d.id === selected);
  const inputStyle = { background: 'var(--bg-field)', border: '1px solid var(--border-light)', color: 'var(--text)' };

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-secondary)' }}>{t('webhook.title', lang)}</h2>
      <div className="rounded-md p-4" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        <div className="mb-4">
          <div className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{t('webhook.device', lang)}</div>
          <select className="w-full rounded-md px-3 py-2 text-sm" style={inputStyle} value={selected} onChange={e => handleSelectChange(e.target.value)}>
            {devices.map(d => <option key={d.id} value={d.id}>{d.name} ({d.id})</option>)}
          </select>
        </div>

        {currentDev && (
          <div className="grid grid-cols-2 gap-3 mb-4">
            {Object.entries(currentDev.fields).map(([name, cfg]) => (
              <div key={name}>
                <div className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{fieldLabel(name, lang)} ({cfg.type}{cfg.unit ? `, ${cfg.unit}` : ''})</div>
                {cfg.type === 'bool' ? (
                  <select className="w-full rounded-md px-3 py-2 text-sm" style={inputStyle} value={values[name] || 'true'} onChange={e => setValues({ ...values, [name]: e.target.value })}>
                    <option value="true">true</option><option value="false">false</option>
                  </select>
                ) : (
                  <input type={cfg.type === 'float' || cfg.type === 'int' ? 'number' : 'text'} step={cfg.type === 'float' ? '0.1' : '1'} className="w-full rounded-md px-3 py-2 text-sm" style={inputStyle} value={values[name] || ''} onChange={e => setValues({ ...values, [name]: e.target.value })} />
                )}
              </div>
            ))}
          </div>
        )}

        <button className="flex items-center justify-center gap-2 w-full py-2.5 rounded-md font-semibold transition disabled:opacity-50" style={{ background: 'var(--green-bg)', color: 'var(--green)' }} onClick={handleSend} disabled={sending}>
          {sending ? <Radio size={16} className="animate-pulse" /> : <Send size={16} />}
          {sending ? t('webhook.sending', lang) : t('webhook.send', lang)}
        </button>

        {result && (
          <pre className="mt-4 rounded-md p-3 text-xs overflow-x-auto whitespace-pre-wrap" style={{ background: 'var(--bg-field)', border: '1px solid var(--border-light)', color: 'var(--text-secondary)' }}>{result}</pre>
        )}
      </div>
    </div>
  );
}
