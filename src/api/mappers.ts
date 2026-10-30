import { ApiAlert, ApiIncident } from './client';
import { IncidentAlert } from '../types';

export const mapIncident = (incident: ApiIncident): IncidentAlert => ({
  id: incident.incident_number,
  vehicleId: incident.qr_code_identifier || 'unknown',
  vehiclePlate: incident.qr_code_identifier || 'Safe-QR',
  vehicleDescription: 'Safe-QR vehicle',
  type: incident.incident_type === 'ACCIDENT' ? 'emergency_sos' : 'routine_report',
  severity: incident.priority.toLowerCase() as IncidentAlert['severity'],
  status: incident.status === 'REPORTED' ? 'investigating' : 'resolved',
  createdAt: incident.created_at,
  updatedAt: incident.updated_at,
  location: {
    address: incident.location_address || 'Location unavailable',
    lat: incident.latitude ?? 0,
    lng: incident.longitude ?? 0,
    accuracyMeters: 0,
    timestamp: incident.created_at,
  },
  description: incident.description,
  timeline: [],
});

export const mapAlert = (alert: ApiAlert): IncidentAlert => ({
  id: alert.id,
  vehicleId: alert.qr_code_identifier || 'unknown',
  vehiclePlate: alert.qr_code_identifier || 'Safe-QR',
  vehicleDescription: 'Safe-QR vehicle',
  type: 'emergency_sos',
  severity: alert.severity.toLowerCase() as IncidentAlert['severity'],
  status: alert.status === 'TRIGGERED' ? 'active_sos' : 'resolved',
  createdAt: alert.created_at,
  updatedAt: alert.updated_at,
  location: {
    address: alert.location_address || 'Location unavailable',
    lat: alert.latitude ?? 0,
    lng: alert.longitude ?? 0,
    accuracyMeters: 0,
    timestamp: alert.created_at,
  },
  description: alert.notes,
  timeline: [],
});
