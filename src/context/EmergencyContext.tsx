import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  VehicleData,
  EmergencyContact,
  MedicalInfo,
  PrivacyConsent,
  IncidentAlert,
  IncidentStatus,
  RoutineIncidentCategory,
  ResponderUser,
} from '../types';
import {
  initialVehicle,
  initialEmergencyContacts,
  initialMedicalInfo,
  initialPrivacyConsent,
  initialResponder,
  initialIncidents,
} from '../mock/initialData';
import { fetchIncidentQueue, publicEmergencyAlert, publicIncidentReport, updateIncident } from '../api/client';
import { mapAlert, mapIncident } from '../api/mappers';

export type AppRole = 'public-qr' | 'customer' | 'operations' | 'responder';

interface ToastNotice {
  id: string;
  text: string;
  type: 'success' | 'danger' | 'info' | 'warning';
}

interface EmergencyContextType {
  role: AppRole;
  setRole: (role: AppRole) => void;
  vehicle: VehicleData;
  updateVehicle: (data: Partial<VehicleData>) => void;
  emergencyContacts: EmergencyContact[];
  addEmergencyContact: (contact: Omit<EmergencyContact, 'id'>) => void;
  updateEmergencyContact: (id: string, contact: Partial<EmergencyContact>) => void;
  deleteEmergencyContact: (id: string) => void;
  medicalInfo: MedicalInfo;
  updateMedicalInfo: (data: Partial<MedicalInfo>) => void;
  privacyConsent: PrivacyConsent;
  updatePrivacyConsent: (data: Partial<PrivacyConsent>) => void;
  incidents: IncidentAlert[];
  selectedIncidentId: string | null;
  setSelectedIncidentId: (id: string | null) => void;
  triggerEmergencyAlert: (description: string, reporterName?: string, reporterPhone?: string, location?: { latitude: number; longitude: number }) => Promise<string>;
  reportRoutineIncident: (category: RoutineIncidentCategory, description: string, reporterName?: string, reporterPhone?: string, location?: { latitude: number; longitude: number }) => Promise<string>;
  callAmbulanceAction: (details: string, callerPhone?: string) => string;
  callPoliceAction: (details: string, callerPhone?: string) => string;
  updateIncidentStatus: (incidentId: string, status: IncidentStatus, notes?: string) => void;
  claimIncident: (incidentId: string) => Promise<void>;
  assignResponder: (incidentId: string, responderName: string, agency: string, etaMinutes: number) => void;
  responderUser: ResponderUser;
  unlockMedicalAccess: (incidentId: string) => boolean;
  isMobileFrame: boolean;
  setIsMobileFrame: (val: boolean) => void;
  toasts: ToastNotice[];
  showToast: (text: string, type?: 'success' | 'danger' | 'info' | 'warning') => void;
  removeToast: (id: string) => void;
  resetDemoData: () => void;
  incidentsLoading: boolean;
  incidentsError: string | null;
  refreshIncidents: () => Promise<void>;
}

const EmergencyContext = createContext<EmergencyContextType | undefined>(undefined);

export const EmergencyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [role, setRole] = useState<AppRole>('public-qr');
  const [vehicle, setVehicle] = useState<VehicleData>(() => {
    const saved = localStorage.getItem('fp_vehicle');
    return saved ? JSON.parse(saved) : initialVehicle;
  });
  const [emergencyContacts, setEmergencyContacts] = useState<EmergencyContact[]>(() => {
    const saved = localStorage.getItem('fp_contacts');
    return saved ? JSON.parse(saved) : initialEmergencyContacts;
  });
  const [medicalInfo, setMedicalInfo] = useState<MedicalInfo>(() => {
    const saved = localStorage.getItem('fp_medical');
    return saved ? JSON.parse(saved) : initialMedicalInfo;
  });
  const [privacyConsent, setPrivacyConsent] = useState<PrivacyConsent>(() => {
    const saved = localStorage.getItem('fp_privacy');
    return saved ? JSON.parse(saved) : initialPrivacyConsent;
  });
  const [incidents, setIncidents] = useState<IncidentAlert[]>(() => {
    const saved = localStorage.getItem('fp_incidents');
    return saved ? JSON.parse(saved) : initialIncidents;
  });
  const [responderUser] = useState<ResponderUser>(initialResponder);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [isMobileFrame, setIsMobileFrame] = useState<boolean>(true);
  const [toasts, setToasts] = useState<ToastNotice[]>([]);
  const [incidentsLoading, setIncidentsLoading] = useState(false);
  const [incidentsError, setIncidentsError] = useState<string | null>(null);

  const refreshIncidents = async () => {
    const token = localStorage.getItem('fp_access_token');
    if (!token) {
      setIncidentsError('Operations access requires an API access token.');
      return;
    }
    setIncidentsLoading(true);
    setIncidentsError(null);
    try {
      const response = await fetchIncidentQueue();
      setIncidents(response.data.map(mapIncident));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to load incidents.';
      setIncidentsError(message);
      showToast(message, 'danger');
    } finally {
      setIncidentsLoading(false);
    }
  };

  useEffect(() => {
    if (role === 'operations') void refreshIncidents();
  }, [role]);

  // Local storage persistence
  useEffect(() => {
    localStorage.setItem('fp_vehicle', JSON.stringify(vehicle));
  }, [vehicle]);

  useEffect(() => {
    localStorage.setItem('fp_contacts', JSON.stringify(emergencyContacts));
  }, [emergencyContacts]);

  useEffect(() => {
    localStorage.setItem('fp_medical', JSON.stringify(medicalInfo));
  }, [medicalInfo]);

  useEffect(() => {
    localStorage.setItem('fp_privacy', JSON.stringify(privacyConsent));
  }, [privacyConsent]);

  useEffect(() => {
    localStorage.setItem('fp_incidents', JSON.stringify(incidents));
  }, [incidents]);

  const showToast = (text: string, type: 'success' | 'danger' | 'info' | 'warning' = 'info') => {
    const id = 'toast_' + Date.now() + Math.random().toString(36).substring(2, 6);
    setToasts((prev) => [...prev, { id, text, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const updateVehicle = (data: Partial<VehicleData>) => {
    setVehicle((prev) => ({ ...prev, ...data }));
    showToast('Vehicle profile updated successfully', 'success');
  };

  const addEmergencyContact = (contact: Omit<EmergencyContact, 'id'>) => {
    const newContact: EmergencyContact = {
      ...contact,
      id: 'cnt-' + Date.now(),
    };
    setEmergencyContacts((prev) => [...prev, newContact]);
    showToast(`Added emergency contact: ${contact.name}`, 'success');
  };

  const updateEmergencyContact = (id: string, contact: Partial<EmergencyContact>) => {
    setEmergencyContacts((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...contact } : c))
    );
    showToast('Emergency contact updated', 'success');
  };

  const deleteEmergencyContact = (id: string) => {
    setEmergencyContacts((prev) => prev.filter((c) => c.id !== id));
    showToast('Emergency contact removed', 'info');
  };

  const updateMedicalInfo = (data: Partial<MedicalInfo>) => {
    setMedicalInfo((prev) => ({ ...prev, ...data }));
    showToast('Medical emergency record updated', 'success');
  };

  const updatePrivacyConsent = (data: Partial<PrivacyConsent>) => {
    setPrivacyConsent((prev) => ({ ...prev, ...data }));
    showToast('Privacy & emergency consent preferences saved', 'success');
  };

  const triggerEmergencyAlert = async (
    description: string,
    reporterName?: string,
    reporterPhone?: string,
    location?: { latitude: number; longitude: number }
  ) => {
    const qrCode = vehicle.safeQrCode;
    if (!qrCode) throw new Error('A verified Safe-QR code is required.');
    const response = await publicEmergencyAlert(qrCode, {
      severity: 'CRITICAL',
      latitude: location?.latitude ?? null,
      longitude: location?.longitude ?? null,
      notes: [description, reporterName, reporterPhone].filter(Boolean).join('\n'),
    });
    const incident = mapAlert(response.data);
    setIncidents((prev) => [incident, ...prev]);
    showToast('Emergency alert accepted by the server.', 'danger');
    return incident.id;
  };

  const reportRoutineIncident = async (
    category: RoutineIncidentCategory,
    description: string,
    reporterName?: string,
    reporterPhone?: string,
    location?: { latitude: number; longitude: number }
  ) => {
    const response = await publicIncidentReport(vehicle.safeQrCode, {
      incident_type: category === 'parking_bump' ? 'DAMAGE' : 'OTHER',
      priority: 'LOW',
      location_precision: location ? 'PRECISE' : 'NONE',
      latitude: location?.latitude ?? null,
      longitude: location?.longitude ?? null,
      reporter_contact_shared: Boolean(reporterPhone),
      description: [category, description, reporterName, reporterPhone].filter(Boolean).join(' - '),
    });
    const incident = mapIncident(response.data);
    setIncidents((prev) => [incident, ...prev]);
    showToast('Incident report accepted by the server.', 'success');
    return incident.id;
  };

  const callAmbulanceAction = (details: string, callerPhone?: string) => {
    const newId = `INC-2026-${Math.floor(1000 + Math.random() * 9000)}`;
    const nowIso = new Date().toISOString();

    const newIncident: IncidentAlert = {
      id: newId,
      vehicleId: vehicle.id,
      vehiclePlate: vehicle.licensePlate,
      vehicleDescription: `${vehicle.year} ${vehicle.make} ${vehicle.model} (${vehicle.color})`,
      type: 'ambulance',
      severity: 'critical',
      status: 'dispatched',
      createdAt: nowIso,
      updatedAt: nowIso,
      location: {
        address: 'Current Device Geolocation (Lat 47.6205, Lng -122.1887)',
        lat: 47.6205,
        lng: -122.1887,
        accuracyMeters: 4.0,
        timestamp: nowIso,
      },
      reporterName: 'Emergency Caller via Safe-QR',
      reporterPhone: callerPhone || '+1 (555) 911-0000',
      description: details || 'Medical emergency requested at vehicle scene.',
      assignedResponder: {
        id: 'RESP-402',
        name: 'Elena Rostova, EMT-P',
        badgeNumber: 'EMS-7921',
        agency: 'Metro First Responder Regional Command',
        type: 'paramedic',
        etaMinutes: 4,
        contactNumber: '+1 (555) 883-4920',
      },
      timeline: [
        {
          id: 'evt-amb-' + Date.now(),
          timestamp: nowIso,
          title: 'Ambulance Call Triggered',
          description: 'Emergency medical dispatch routed. GPS telemetry beamed to regional EMS CAD.',
          actor: 'Public Caller',
          actorRole: 'public_scanner',
          badgeType: 'danger',
        },
      ],
    };

    setIncidents((prev) => [newIncident, ...prev]);
    showToast('Ambulance Dispatch Simulated: Medic Unit 402 routed (ETA 4 min)', 'danger');
    return newId;
  };

  const callPoliceAction = (details: string, callerPhone?: string) => {
    const newId = `INC-2026-${Math.floor(1000 + Math.random() * 9000)}`;
    const nowIso = new Date().toISOString();

    const newIncident: IncidentAlert = {
      id: newId,
      vehicleId: vehicle.id,
      vehiclePlate: vehicle.licensePlate,
      vehicleDescription: `${vehicle.year} ${vehicle.make} ${vehicle.model} (${vehicle.color})`,
      type: 'police',
      severity: 'high',
      status: 'dispatched',
      createdAt: nowIso,
      updatedAt: nowIso,
      location: {
        address: 'Current Device Geolocation (Lat 47.6205, Lng -122.1887)',
        lat: 47.6205,
        lng: -122.1887,
        accuracyMeters: 4.0,
        timestamp: nowIso,
      },
      reporterName: 'Emergency Caller via Safe-QR',
      reporterPhone: callerPhone || '+1 (555) 911-0000',
      description: details || 'Police assistance requested at vehicle scene.',
      assignedResponder: {
        id: 'RESP-POL-108',
        name: 'Officer J. Kowalski',
        badgeNumber: 'PD-394',
        agency: 'City Police Highway Patrol',
        type: 'police',
        etaMinutes: 6,
        contactNumber: '+1 (555) 883-1122',
      },
      timeline: [
        {
          id: 'evt-pol-' + Date.now(),
          timestamp: nowIso,
          title: 'Police Call Triggered',
          description: 'Highway Patrol unit dispatched to vehicle coordinates.',
          actor: 'Public Caller',
          actorRole: 'public_scanner',
          badgeType: 'warning',
        },
      ],
    };

    setIncidents((prev) => [newIncident, ...prev]);
    showToast('Police Dispatch Simulated: Officer Kowalski routed (ETA 6 min)', 'warning');
    return newId;
  };

  const updateIncidentStatus = async (incidentId: string, status: IncidentStatus, notes?: string) => {
    const token = localStorage.getItem('fp_access_token');
    if (token) {
      const backendStatus: Record<IncidentStatus, string> = {
        active_sos: 'DISPATCHED',
        dispatched: 'DISPATCHED',
        en_route: 'IN_PROGRESS',
        on_scene: 'IN_PROGRESS',
        resolved: 'RESOLVED',
        investigating: 'REPORTED',
      };

      try {
        const response = await updateIncident(incidentId, {
          status: backendStatus[status],
          ...(notes ? { operator_notes: notes } : {}),
        });
        setIncidents((prev) => prev.map((item) => item.id === incidentId ? mapIncident(response.data) : item));
        showToast(`Incident status updated to: ${status}`, 'info');
        return;
      } catch (error) {
        showToast(error instanceof Error ? error.message : 'Unable to update incident.', 'danger');
        return;
      }
    }
    setIncidents((prev) =>
      prev.map((inc) => {
        if (inc.id !== incidentId) return inc;
        const nowIso = new Date().toISOString();
        const statusLabels: Record<IncidentStatus, string> = {
          active_sos: 'Active SOS Alert',
          dispatched: 'Unit Dispatched',
          en_route: 'Unit En Route',
          on_scene: 'Unit Arrived On Scene',
          resolved: 'Incident Resolved & Closed',
          investigating: 'Under Routine Review',
        };

        return {
          ...inc,
          status,
          updatedAt: nowIso,
          timeline: [
            ...inc.timeline,
            {
              id: 'evt-u-' + Date.now(),
              timestamp: nowIso,
              title: `Status Changed to: ${statusLabels[status]}`,
              description: notes || `Operational status updated in central dispatch console.`,
              actor: 'Ops Console / Field Officer',
              actorRole: 'dispatcher',
              badgeType: status === 'resolved' ? 'success' : 'info',
            },
          ],
        };
      })
    );
    showToast(`Incident status updated to: ${status}`, 'info');
  };

  const claimIncident = async (incidentId: string) => {
    try {
      const response = await updateIncident(incidentId, { claim: true });
      setIncidents((prev) => prev.map((item) => item.id === incidentId ? mapIncident(response.data) : item));
      showToast('Alert claimed by this operator.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Unable to claim alert.', 'danger');
    }
  };

  const assignResponder = (incidentId: string, responderName: string, agency: string, etaMinutes: number) => {
    setIncidents((prev) =>
      prev.map((inc) => {
        if (inc.id !== incidentId) return inc;
        const nowIso = new Date().toISOString();
        return {
          ...inc,
          status: 'dispatched',
          updatedAt: nowIso,
          assignedResponder: {
            id: 'RESP-' + Math.floor(100 + Math.random() * 900),
            name: responderName,
            badgeNumber: 'FL-902',
            agency,
            type: 'paramedic',
            etaMinutes,
            contactNumber: '+1 (555) 700-1122',
          },
          timeline: [
            ...inc.timeline,
            {
              id: 'evt-a-' + Date.now(),
              timestamp: nowIso,
              title: `Assigned Responder: ${responderName}`,
              description: `Unit from ${agency} dispatched with ${etaMinutes} minute estimated arrival time.`,
              actor: 'Dispatch Command',
              actorRole: 'dispatcher',
              badgeType: 'warning',
            },
          ],
        };
      })
    );
    showToast(`Assigned ${responderName} (${agency})`, 'success');
  };

  const unlockMedicalAccess = (incidentId: string): boolean => {
    setIncidents((prev) =>
      prev.map((inc) => {
        if (inc.id !== incidentId) return inc;
        const nowIso = new Date().toISOString();
        return {
          ...inc,
          medicalAccessed: true,
          updatedAt: nowIso,
          timeline: [
            ...inc.timeline,
            {
              id: 'evt-med-' + Date.now(),
              timestamp: nowIso,
              title: 'Verified Responder Emergency Medical Access Granted',
              description: `EMT-P Elena Rostova accessed authorized medical telemetry under emergency consent.`,
              actor: 'EMT-P Elena Rostova',
              actorRole: 'responder',
              badgeType: 'info',
            },
          ],
        };
      })
    );
    showToast('Authorized Medical Data Decrypted for Verified Responder', 'info');
    return true;
  };

  const resetDemoData = () => {
    setVehicle(initialVehicle);
    setEmergencyContacts(initialEmergencyContacts);
    setMedicalInfo(initialMedicalInfo);
    setPrivacyConsent(initialPrivacyConsent);
    setIncidents(initialIncidents);
    showToast('FixPoint Drive demo data reset to default state', 'info');
  };

  return (
    <EmergencyContext.Provider
      value={{
        role,
        setRole,
        vehicle,
        updateVehicle,
        emergencyContacts,
        addEmergencyContact,
        updateEmergencyContact,
        deleteEmergencyContact,
        medicalInfo,
        updateMedicalInfo,
        privacyConsent,
        updatePrivacyConsent,
        incidents,
        selectedIncidentId,
        setSelectedIncidentId,
        triggerEmergencyAlert,
        reportRoutineIncident,
        callAmbulanceAction,
        callPoliceAction,
        updateIncidentStatus,
        claimIncident,
        assignResponder,
        responderUser,
        unlockMedicalAccess,
        isMobileFrame,
        setIsMobileFrame,
        toasts,
        showToast,
        removeToast,
        resetDemoData,
        incidentsLoading,
        incidentsError,
        refreshIncidents,
      }}
    >
      {children}
    </EmergencyContext.Provider>
  );
};

export const useEmergency = () => {
  const context = useContext(EmergencyContext);
  if (!context) {
    throw new Error('useEmergency must be used within an EmergencyProvider');
  }
  return context;
};
