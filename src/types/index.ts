export type IncidentType = 'emergency_sos' | 'ambulance' | 'police' | 'routine_report';

export type IncidentStatus = 'active_sos' | 'dispatched' | 'en_route' | 'on_scene' | 'resolved' | 'investigating';

export type RoutineIncidentCategory = 'parking_bump' | 'vehicle_obstruction' | 'flat_tire_or_breakdown' | 'lights_left_on' | 'other';

export interface LocationData {
  address: string;
  lat: number;
  lng: number;
  accuracyMeters: number;
  timestamp: string;
}

export interface EmergencyContact {
  id: string;
  name: string;
  relationship: string;
  phone: string;
  priority: 1 | 2 | 3;
  notifyOnSos: boolean;
  notifyOnRoutine: boolean;
}

export interface MedicalInfo {
  bloodType: string;
  allergies: string[];
  medicalConditions: string[];
  medications: string[];
  organDonor: boolean;
  dnrStatus: boolean;
  physicianName: string;
  physicianPhone: string;
  additionalNotes: string;
}

export interface PrivacyConsent {
  shareBloodTypeOnSos: boolean;
  shareAllergiesOnSos: boolean;
  shareMedicationsOnSos: boolean;
  shareFullMedicalToVerifiedResponder: boolean;
  autoNotifyContactsSms: boolean;
  shareLiveGpsLocation: boolean;
  requirePinForSensitiveHistory: boolean;
}

export interface VehicleData {
  id: string;
  safeQrCode: string;
  licensePlate: string;
  make: string;
  model: string;
  year: number;
  color: string;
  vin: string;
  insuranceProvider: string;
  policyNumber: string;
  ownerName: string;
  ownerPhone: string;
  ownerEmail: string;
  emergencyPin: string;
  registeredDate: string;
  qrScanCount: number;
  lastScannedAt?: string;
}

export interface IncidentTimelineEvent {
  id: string;
  timestamp: string;
  title: string;
  description: string;
  actor: string;
  actorRole: 'system' | 'public_scanner' | 'dispatcher' | 'responder';
  badgeType?: 'danger' | 'warning' | 'info' | 'success';
}

export interface IncidentAlert {
  id: string;
  vehicleId: string;
  vehiclePlate: string;
  vehicleDescription: string;
  type: IncidentType;
  category?: RoutineIncidentCategory;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: IncidentStatus;
  createdAt: string;
  updatedAt: string;
  location: LocationData;
  reporterName?: string;
  reporterPhone?: string;
  description: string;
  assignedResponder?: {
    id: string;
    name: string;
    badgeNumber: string;
    agency: string;
    type: 'paramedic' | 'police' | 'roadside_patrol';
    etaMinutes: number;
    contactNumber: string;
  };
  timeline: IncidentTimelineEvent[];
  medicalAccessed?: boolean;
  notes?: string;
}

export interface ResponderUser {
  id: string;
  name: string;
  badgeNumber: string;
  agency: string;
  unitId: string;
  role: 'paramedic' | 'police_officer' | 'field_inspector';
  verified: boolean;
  verificationExpiry: string;
  tokenExpiresInMinutes: number;
}
