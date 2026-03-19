export type Lang = 'zh' | 'en';

const messages = {
  // Header
  'online': { zh: '在線', en: 'online' },
  'connected': { zh: '已連線', en: 'Connected' },
  'disconnected': { zh: '未連線', en: 'Disconnected' },

  // Tabs
  'tab.devices': { zh: '設備', en: 'Devices' },
  'tab.alerts': { zh: '告警', en: 'Alerts' },
  'tab.rules': { zh: '規則', en: 'Rules' },
  'tab.webhook': { zh: 'Webhook 模擬', en: 'Webhook Sim' },

  // Devices
  'devices.empty': { zh: '尚無設備連線', en: 'No devices connected' },
  'devices.realtime': { zh: '即時數據', en: 'Real-time Data' },
  'devices.set': { zh: '設定', en: 'Set' },

  // Alerts
  'alerts.title': { zh: '告警記錄', en: 'Alerts' },
  'alerts.empty': { zh: '尚無告警', en: 'No alerts' },
  'alerts.all': { zh: '全部', en: 'All' },
  'alerts.critical': { zh: '嚴重', en: 'Critical' },
  'alerts.warning': { zh: '警告', en: 'Warning' },
  'alerts.info': { zh: '資訊', en: 'Info' },

  // Rules
  'rules.title': { zh: '告警規則', en: 'Alert Rules' },
  'rules.add': { zh: '新增規則', en: 'Add Rule' },
  'rules.name': { zh: '名稱', en: 'Name' },
  'rules.device': { zh: '設備', en: 'Device' },
  'rules.severity': { zh: '等級', en: 'Severity' },
  'rules.cooldown': { zh: '冷卻時間 (秒)', en: 'Cooldown (sec)' },
  'rules.field': { zh: '欄位', en: 'Field' },
  'rules.operator': { zh: '運算子', en: 'Operator' },
  'rules.threshold': { zh: '閾值', en: 'Threshold' },
  'rules.actionType': { zh: '動作類型', en: 'Action Type' },
  'rules.description': { zh: '描述', en: 'Description' },
  'rules.condition': { zh: '條件', en: 'Condition' },
  'rules.actions': { zh: '動作', en: 'Actions' },
  'rules.cancel': { zh: '取消', en: 'Cancel' },
  'rules.save': { zh: '儲存', en: 'Save' },

  // Webhook Simulator
  'webhook.title': { zh: 'Webhook 模擬器', en: 'Webhook Simulator' },
  'webhook.device': { zh: '設備', en: 'Device' },
  'webhook.send': { zh: '發送 Webhook', en: 'Send Webhook' },
  'webhook.sending': { zh: '發送中...', en: 'Sending...' },
  'webhook.empty': { zh: '尚無 Webhook 設備', en: 'No webhook devices configured' },
} as const;

// 常見欄位名稱翻譯（設備欄位來自 YAML，UI 顯示用）
const fieldNames: Record<string, { zh: string; en: string }> = {
  temperature: { zh: '溫度', en: 'Temperature' },
  humidity: { zh: '濕度', en: 'Humidity' },
  battery: { zh: '電量', en: 'Battery' },
  motor_speed: { zh: '馬達轉速', en: 'Motor Speed' },
  pump_on: { zh: '幫浦開關', en: 'Pump' },
  pressure: { zh: '壓力', en: 'Pressure' },
  brightness: { zh: '亮度', en: 'Brightness' },
  power: { zh: '電源', en: 'Power' },
  status: { zh: '狀態', en: 'Status' },
  valve_open: { zh: '閥門開關', en: 'Valve' },
};

export function fieldLabel(name: string, lang: Lang): string {
  return fieldNames[name]?.[lang] || name;
}

type MessageKey = keyof typeof messages;

export function t(key: MessageKey, lang: Lang): string {
  return messages[key]?.[lang] || key;
}

export function useLang() {
  const get = (): Lang => {
    const saved = localStorage.getItem('iot-lang');
    return (saved === 'en' ? 'en' : 'zh') as Lang;
  };

  return { get };
}
