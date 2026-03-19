import { useState, useEffect } from 'react';
import { Radio, Server, AlertTriangle, Shield, Webhook, Sun, Moon, Languages, Monitor } from 'lucide-react';
import { useWebSocket } from './hooks/useWebSocket';
import { useDemoMode } from './hooks/useDemoMode';
import { useTheme } from './hooks/useTheme';
import { useLang } from './hooks/useLang';
import { t } from './lib/i18n';
import { DevicesPanel } from './components/DevicesPanel';
import { AlertsPanel } from './components/AlertsPanel';
import { RulesPanel } from './components/RulesPanel';
import { WebhookSimPanel } from './components/WebhookSimPanel';

type Tab = 'devices' | 'alerts' | 'rules' | 'webhook';

function useAutoDetectDemo() {
  const [isDemo, setIsDemo] = useState(false);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    fetch('/api/devices')
      .then(r => { if (!r.ok) throw new Error(); setIsDemo(false); })
      .catch(() => setIsDemo(true))
      .finally(() => setChecked(true));
  }, []);

  return { isDemo, checked };
}

function App() {
  const [tab, setTab] = useState<Tab>('devices');
  const { theme, toggle: toggleTheme } = useTheme();
  const { lang, toggle: toggleLang } = useLang();
  const { isDemo, checked } = useAutoDetectDemo();

  const ws = useWebSocket();
  const demo = useDemoMode();

  // Use demo data when API is unreachable
  const { devices, history, connected } = isDemo ? demo : ws;

  if (!checked) return null;

  const tabs: { id: Tab; label: string; icon: typeof Server }[] = [
    { id: 'devices', label: t('tab.devices', lang), icon: Server },
    { id: 'alerts', label: t('tab.alerts', lang), icon: AlertTriangle },
    { id: 'rules', label: t('tab.rules', lang), icon: Shield },
    { id: 'webhook', label: t('tab.webhook', lang), icon: Webhook },
  ];

  const onlineCount = Object.values(devices).filter(d => d.online).length;
  const totalCount = Object.keys(devices).length;

  return (
    <div className="max-w-5xl mx-auto px-4 py-4">
      {/* Demo Mode Banner */}
      {isDemo && (
        <div
          className="flex items-center justify-center gap-2 py-2 px-4 rounded-lg mb-4 text-sm font-semibold"
          style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--yellow)', border: '1px solid rgba(245, 158, 11, 0.3)' }}
        >
          <Monitor size={16} />
          {lang === 'zh' ? 'Demo Mode — 顯示模擬數據，非即時設備連線' : 'Demo Mode — Showing simulated data, not connected to live devices'}
        </div>
      )}

      {/* Header */}
      <header className="flex items-center justify-between pb-4 mb-4" style={{ borderBottom: '1px solid var(--border)' }}>
        <div className="flex items-center gap-3">
          <Radio size={20} style={{ color: 'var(--green)' }} />
          <h1 className="text-lg font-bold" style={{ color: 'var(--green)' }}>KC IoT Gateway</h1>
          {totalCount > 0 && (
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{onlineCount}/{totalCount} {t('online', lang)}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleLang}
            className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs font-semibold transition hover:opacity-80"
            style={{ background: 'var(--bg-field)', border: '1px solid var(--border-light)', color: 'var(--text-secondary)' }}
            title={lang === 'zh' ? 'Switch to English' : '切換為中文'}
          >
            <Languages size={14} />
            {lang === 'zh' ? 'EN' : '中文'}
          </button>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg transition hover:opacity-80"
            style={{ background: 'var(--bg-field)', border: '1px solid var(--border-light)' }}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark'
              ? <Sun size={16} style={{ color: 'var(--yellow)' }} />
              : <Moon size={16} style={{ color: 'var(--blue)' }} />}
          </button>
          <span
            className="text-xs px-3 py-1 rounded-full"
            style={{
              background: connected ? 'var(--green-bg)' : 'var(--red-bg)',
              color: connected ? 'var(--green)' : 'var(--red)',
            }}
          >
            {isDemo ? 'Demo' : connected ? t('connected', lang) : t('disconnected', lang)}
          </span>
        </div>
      </header>

      {/* Tabs */}
      <nav className="flex gap-1 mb-5">
        {tabs.map(tb => {
          const Icon = tb.icon;
          const active = tab === tb.id;
          return (
            <button
              key={tb.id}
              className="flex items-center gap-1.5 px-4 py-2 rounded-md text-sm transition"
              style={{
                background: active ? 'var(--bg-field)' : 'transparent',
                color: active ? 'var(--green)' : 'var(--text-secondary)',
                border: active ? '1px solid var(--border-light)' : '1px solid transparent',
              }}
              onClick={() => setTab(tb.id)}
            >
              <Icon size={14} />
              {tb.label}
            </button>
          );
        })}
      </nav>

      {/* Content */}
      {tab === 'devices' && <DevicesPanel devices={devices} history={history} lang={lang} />}
      {tab === 'alerts' && <AlertsPanel lang={lang} isDemo={isDemo} />}
      {tab === 'rules' && <RulesPanel lang={lang} isDemo={isDemo} />}
      {tab === 'webhook' && <WebhookSimPanel lang={lang} isDemo={isDemo} />}
    </div>
  );
}

export default App;
