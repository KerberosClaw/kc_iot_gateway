import { useState, useEffect } from 'react';
import { Shield, Plus, Pencil, Trash2, X, Check } from 'lucide-react';
import { fetchRules, createRule, updateRule, deleteRule, toggleRule, type Rule } from '../lib/api';
import { t, type Lang } from '../lib/i18n';

const MOCK_RULES: Rule[] = [
  { name: 'high_temperature', description: '廠區溫度過高', device: 'factory_temp_01', condition: { field: 'temperature', operator: '>', threshold: 35 }, severity: 'critical', cooldown: 30, actions: [{ type: 'console', message: '[CRITICAL] {device_name} temperature {value}' }], active: true, created_at: Date.now() / 1000 },
  { name: 'plc_high_temp', description: 'PLC 溫度過高', device: 'plc_01', condition: { field: 'temperature', operator: '>', threshold: 30 }, severity: 'warning', cooldown: 30, actions: [{ type: 'console' }], active: true, created_at: Date.now() / 1000 },
  { name: 'pump_auto_control', description: '溫度過高自動開泵', device: 'plc_01', condition: { field: 'temperature', operator: '>', threshold: 28 }, severity: 'info', cooldown: 60, actions: [{ type: 'device_write', target_device: 'plc_01', params: { pump_on: true } }, { type: 'console' }], active: true, created_at: Date.now() / 1000 },
];

export function RulesPanel({ lang, isDemo = false }: { lang: Lang; isDemo?: boolean }) {
  const [rules, setRules] = useState<Rule[]>([]);
  const [editing, setEditing] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const load = async () => {
    if (isDemo) { setRules(MOCK_RULES); return; }
    setRules(await fetchRules());
  };
  useEffect(() => { load(); }, [isDemo]);

  const handleToggle = async (name: string) => {
    if (isDemo) { setRules(prev => prev.map(r => r.name === name ? { ...r, active: !r.active } : r)); return; }
    await toggleRule(name); await load();
  };
  const handleDelete = async (name: string) => {
    if (isDemo) { setRules(prev => prev.filter(r => r.name !== name)); return; }
    await deleteRule(name); await load();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold" style={{ color: 'var(--text-secondary)' }}>{t('rules.title', lang)}</h2>
        <button className="flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-semibold transition" style={{ background: 'var(--green-bg)', color: 'var(--green)' }} onClick={() => setCreating(true)}>
          <Plus size={14} /> {t('rules.add', lang)}
        </button>
      </div>

      {creating && <RuleForm lang={lang} isDemo={isDemo} onSave={async (rule) => {
        if (isDemo) { setRules(prev => [...prev, { ...MOCK_RULES[0], ...rule, created_at: Date.now() / 1000 } as Rule]); }
        else { await createRule(rule); await load(); }
        setCreating(false);
      }} onCancel={() => setCreating(false)} />}

      <div className="space-y-2">
        {rules.map(rule => (
          <div key={rule.name}>
            {editing === rule.name ? (
              <RuleForm lang={lang} isDemo={isDemo} initial={rule} onSave={async (updates) => {
                if (isDemo) { setRules(prev => prev.map(r => r.name === rule.name ? { ...r, ...updates } as Rule : r)); }
                else { await updateRule(rule.name, updates); await load(); }
                setEditing(null);
              }} onCancel={() => setEditing(null)} />
            ) : (
              <div className="rounded-md p-3" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Shield size={14} style={{ color: 'var(--text-muted)' }} />
                    <span className="font-semibold">{rule.name}</span>
                    <SeverityBadge severity={rule.severity} />
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{rule.description}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="p-1 rounded transition" style={{ color: 'var(--text-muted)' }} onClick={() => setEditing(rule.name)}><Pencil size={14} /></button>
                    <button className="p-1 rounded transition" style={{ color: 'var(--text-muted)' }} onClick={() => handleDelete(rule.name)}><Trash2 size={14} /></button>
                    <button className="w-10 h-5 rounded-full relative transition" style={{ background: rule.active ? 'var(--green-bg)' : 'var(--border-light)' }} onClick={() => handleToggle(rule.name)}>
                      <div className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all" style={{ left: rule.active ? 20 : 2 }} />
                    </button>
                  </div>
                </div>
                <div className="mt-2 text-xs flex gap-4" style={{ color: 'var(--text-muted)' }}>
                  <span>{t('rules.device', lang)}: {rule.device}</span>
                  <span>{t('rules.condition', lang)}: {rule.condition.field} {rule.condition.operator} {rule.condition.threshold}</span>
                  <span>{t('rules.cooldown', lang)}: {rule.cooldown}s</span>
                  <span>{t('rules.actions', lang)}: {rule.actions.map(a => a.type).join(', ')}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, { bg: string; text: string }> = {
    critical: { bg: 'var(--red-bg)', text: 'var(--red)' },
    warning: { bg: 'rgba(217, 119, 6, 0.15)', text: 'var(--yellow)' },
    info: { bg: 'rgba(37, 99, 235, 0.15)', text: 'var(--blue)' },
  };
  const c = colors[severity] || colors.info;
  return <span className="text-xs px-1.5 py-0.5 rounded" style={{ background: c.bg, color: c.text }}>{severity}</span>;
}

function RuleForm({ lang, isDemo: _isDemo, initial, onSave, onCancel }: { lang: Lang; isDemo?: boolean; initial?: Partial<Rule>; onSave: (rule: Partial<Rule>) => Promise<void>; onCancel: () => void }) {
  const [form, setForm] = useState({
    name: initial?.name || '', description: initial?.description || '', device: initial?.device || '*',
    field: initial?.condition?.field || 'temperature', operator: initial?.condition?.operator || '>',
    threshold: initial?.condition?.threshold ?? 30, severity: initial?.severity || 'warning',
    cooldown: initial?.cooldown ?? 300, actionType: initial?.actions?.[0]?.type || 'console',
    actionMessage: initial?.actions?.[0]?.message || '{rule_name}: {device_name} {field}={value}',
  });

  const handleSave = async () => {
    await onSave({
      name: form.name, description: form.description, device: form.device,
      condition: { field: form.field, operator: form.operator, threshold: form.threshold },
      severity: form.severity, cooldown: form.cooldown,
      actions: [{ type: form.actionType, message: form.actionMessage }],
    });
  };

  const inputStyle = { background: 'var(--bg-field)', border: '1px solid var(--border-light)', color: 'var(--text)' };
  const fields: { label: string; key: string; type?: string; options?: string[]; disabled?: boolean }[] = [
    { label: t('rules.name', lang), key: 'name', disabled: !!initial },
    { label: t('rules.device', lang), key: 'device' },
    { label: t('rules.severity', lang), key: 'severity', options: ['critical', 'warning', 'info'] },
    { label: t('rules.cooldown', lang), key: 'cooldown', type: 'number' },
    { label: t('rules.field', lang), key: 'field' },
    { label: t('rules.operator', lang), key: 'operator', options: ['>', '<', '>=', '<=', '==', '!='] },
    { label: t('rules.threshold', lang), key: 'threshold', type: 'number' },
    { label: t('rules.actionType', lang), key: 'actionType', options: ['console', 'telegram', 'webhook', 'device_write'] },
  ];

  return (
    <div className="rounded-md p-4 mb-2" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-light)' }}>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {fields.map(f => (
          <div key={f.key}>
            <div className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{f.label}</div>
            {f.options ? (
              <select className="w-full rounded-md px-3 py-1.5 text-sm" style={inputStyle} value={(form as Record<string, unknown>)[f.key] as string} onChange={e => setForm({ ...form, [f.key]: f.type === 'number' ? Number(e.target.value) : e.target.value })}>
                {f.options.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            ) : (
              <input className="w-full rounded-md px-3 py-1.5 text-sm" style={inputStyle} type={f.type || 'text'} step={f.type === 'number' ? '0.1' : undefined} value={(form as Record<string, unknown>)[f.key] as string} onChange={e => setForm({ ...form, [f.key]: f.type === 'number' ? Number(e.target.value) : e.target.value })} disabled={f.disabled} />
            )}
          </div>
        ))}
      </div>
      <div className="mt-3">
        <div className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{t('rules.description', lang)}</div>
        <input className="w-full rounded-md px-3 py-1.5 text-sm" style={inputStyle} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
      </div>
      <div className="flex gap-2 mt-3 justify-end">
        <button className="flex items-center gap-1 px-3 py-1.5 rounded-md text-sm transition" style={{ background: 'var(--border)', color: 'var(--text-secondary)' }} onClick={onCancel}><X size={14} /> {t('rules.cancel', lang)}</button>
        <button className="flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-semibold transition" style={{ background: 'var(--green-bg)', color: 'var(--green)' }} onClick={handleSave}><Check size={14} /> {t('rules.save', lang)}</button>
      </div>
    </div>
  );
}
