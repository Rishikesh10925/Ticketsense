export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "ticketsense_token";

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = tokenStore.get();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }), ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers },
  });
  if (response.status === 401) { tokenStore.clear(); window.dispatchEvent(new Event("ticketsense:unauthorized")); }
  if (!response.ok) {
    let message = "Unable to complete the request. Please try again.";
    try { const body = await response.json(); message = body.detail || message; } catch { /* non-JSON error */ }
    throw new ApiError(message, response.status);
  }
  return response.status === 204 ? undefined as T : response.json();
}

export interface User { id:string; email:string; full_name:string; role:string; department_id:string|null; tenant_id:string|null }
export interface Evidence { title:string; excerpt:string; score:number; source?:string }
export interface Analysis { category?:string; intent?:string; sentiment?:string; priority_score?:number; sla_risk?:number; confidence?:number; decision?:string; decision_reason?:string; root_causes?:Array<{label:string;probability:number}>; evidence?:Evidence[]; [key:string]:unknown }
export interface Ticket { id:string; subject:string; description:string; status:string; priority:string|null; sentiment:string|null; department_id?:string|null; confidence_score:number|null; ai_draft_reply?:string|null; created_at:string; updated_at?:string; analysis:Analysis }
export interface Analytics { total_tickets:number; open_tickets:number; resolved_tickets:number; escalated_tickets:number; average_confidence:number; status_distribution:Record<string,number> }
export interface Incident { id:string; title:string; service:string; status:string; severity:string; ticket_count:number; growth_rate:number; common_symptom?:string }
export interface Notification { id:string; title:string; message:string; kind:string; is_read:boolean; created_at:string }

export const api = {
  login: async (email:string,password:string) => {
    const body = new URLSearchParams({ username: email, password });
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, { method:"POST", headers:{"Content-Type":"application/x-www-form-urlencoded"}, body });
    if (!response.ok) { let msg="Incorrect email or password"; try {msg=(await response.json()).detail||msg}catch{}; throw new ApiError(msg,response.status); }
    const data = await response.json(); tokenStore.set(data.access_token); return data.access_token as string;
  },
  me: () => request<User>("/api/auth/me"),
  tickets: (query="",status="") => request<Ticket[]>(`/api/tickets?${new URLSearchParams({q:query,status_filter:status})}`),
  ticket: (id:string) => request<Ticket>(`/api/tickets/${id}`),
  createTicket: (payload:Record<string,string>) => request<Ticket>("/api/tickets",{method:"POST",body:JSON.stringify(payload)}),
  ticketAction: (id:string,payload:{action:string;response?:string;reason?:string}) => request<Ticket>(`/api/tickets/${id}/action`,{method:"POST",body:JSON.stringify(payload)}),
  analysis: (id:string) => request<Analysis>(`/api/tickets/${id}/ai-analysis`),
  evidence: (id:string) => request<Evidence[]>(`/api/tickets/${id}/evidence`),
  similar: (id:string) => request<Array<{id:string;subject:string;status:string;similarity:number;resolution?:string}>>(`/api/tickets/${id}/similar`),
  trace: (id:string) => request<Array<{action:string;detail:Record<string,unknown>;timestamp:string}>>(`/api/tickets/${id}/trace`),
  analytics: () => request<Analytics>("/api/analytics"),
  aiMetrics: () => request<{agents:Array<Record<string,number|string>>;provider:string;external_cost_usd:number}>("/api/ai/metrics"),
  incidents: () => request<Incident[]>("/api/incidents"),
  knowledge: (q="") => request<Array<{id:string;title:string;excerpt:string;source?:string;updated_at:string}>>(`/api/knowledge?${new URLSearchParams({q})}`),
  notifications: () => request<Notification[]>("/api/notifications"),
  markNotificationRead: (id:string) => request<{id:string;is_read:boolean}>(`/api/notifications/${id}/read`,{method:"POST"}),
  auditLogs: () => request<Array<Record<string,unknown>>>("/api/audit-logs"),
  integrations: () => request<Array<{id:string;provider:string;name:string;enabled:boolean}>>("/api/integrations"),
};

export type HealthResponse = {status:string;database:string};
export const fetchHealth = () => request<HealthResponse>("/api/health");
export const fetchTickets = () => api.tickets();
export const createTicket = (payload:Record<string,string>) => api.createTicket(payload);
