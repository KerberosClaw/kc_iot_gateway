const BASE = '';

export interface DeviceData {
  device_id: string;
  name: string;
  protocol: string;
  fields: Record<string, number | string | boolean>;
  online: boolean;
  last_update: number;
}

export interface Rule {
  name: string;
  description: string;
  device: string;
  condition: { field?: string; operator?: string; threshold?: number; type?: string; timeout?: number };
  severity: string;
  cooldown: number;
  actions: { type: string; message?: string; url?: string; target_device?: string; params?: Record<string, unknown> }[];
  active: boolean;
  created_at: number;
}

export interface Alert {
  id: number;
  rule_name: string;
  device_id: string;
  severity: string;
  message: string;
  value: string;
  created_at: number;
}

export interface WebhookDevice {
  id: string;
  name: string;
  identity: { field: string; value: string };
  fields: Record<string, { path: string; type: string; unit?: string }>;
}

export async function fetchDevices(): Promise<DeviceData[]> {
  const resp = await fetch(`${BASE}/api/devices`);
  return resp.json();
}

export async function readDevice(id: string): Promise<Record<string, unknown>> {
  const resp = await fetch(`${BASE}/api/devices/${id}/read`);
  return resp.json();
}

export async function writeDevice(id: string, params: Record<string, unknown>): Promise<Record<string, unknown>> {
  const resp = await fetch(`${BASE}/api/devices/${id}/write`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return resp.json();
}

export async function fetchRules(): Promise<Rule[]> {
  const resp = await fetch(`${BASE}/api/rules`);
  return resp.json();
}

export async function createRule(rule: Partial<Rule>): Promise<void> {
  await fetch(`${BASE}/api/rules`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rule),
  });
}

export async function updateRule(name: string, updates: Partial<Rule>): Promise<void> {
  await fetch(`${BASE}/api/rules/${name}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
}

export async function deleteRule(name: string): Promise<void> {
  await fetch(`${BASE}/api/rules/${name}`, { method: 'DELETE' });
}

export async function toggleRule(name: string): Promise<void> {
  await fetch(`${BASE}/api/rules/${name}/toggle`, { method: 'PATCH' });
}

export async function fetchAlerts(severity?: string, limit = 50): Promise<Alert[]> {
  const params = new URLSearchParams();
  if (severity) params.set('severity', severity);
  params.set('limit', String(limit));
  const resp = await fetch(`${BASE}/api/alerts?${params}`);
  return resp.json();
}

export async function fetchWebhookDevices(): Promise<WebhookDevice[]> {
  const resp = await fetch(`${BASE}/api/webhook-devices`);
  return resp.json();
}

export async function sendWebhook(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  const resp = await fetch(`${BASE}/webhook`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return resp.json();
}
