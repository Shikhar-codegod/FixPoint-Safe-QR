const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface ApiEnvelope<T> {
  data: T;
  message?: string;
}

export interface ApiIncident {
  incident_number: string;
  incident_type: string;
  status: string;
  priority: string;
  location_precision: string;
  latitude: number | null;
  longitude: number | null;
  location_address: string;
  description: string;
  operator_notes?: string;
  claimed_by_email?: string | null;
  qr_code_identifier: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiAlert {
  id: string;
  qr_code_identifier: string | null;
  status: string;
  severity: string;
  latitude: number | null;
  longitude: number | null;
  location_address: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

const request = async <T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiEnvelope<T>> => {
  const token = localStorage.getItem('fp_access_token');
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.message || payload?.detail || 'The server request failed.');
  }
  return payload as ApiEnvelope<T>;
};

export const publicIncidentReport = (qrCode: string, body: Record<string, unknown>) =>
  request<ApiIncident>(`/incidents/report/${encodeURIComponent(qrCode)}/`, {
    method: 'POST',
    body: JSON.stringify(body),
  });

export const publicEmergencyAlert = (qrCode: string, body: Record<string, unknown>) =>
  request<ApiAlert>(`/alerts/public/${encodeURIComponent(qrCode)}/`, {
    method: 'POST',
    body: JSON.stringify(body),
  });

export const fetchIncidentQueue = () =>
  request<ApiIncident[]>('/incidents/queue/');

export const updateIncident = (incidentNumber: string, body: Record<string, unknown>) =>
  request<ApiIncident>(`/incidents/${encodeURIComponent(incidentNumber)}/`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
