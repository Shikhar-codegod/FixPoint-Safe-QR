import React, { useState } from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import { IncidentAlert, IncidentStatus } from '../../types';
import {
  AlertOctagon,
  Ambulance,
  CheckCircle2,
  Clock,
  MapPin,
  Phone,
  Shield,
  User,
  Users,
  X,
  Send,
  FileText,
  AlertTriangle,
} from 'lucide-react';

interface Props {
  incidentId: string | null;
  onClose: () => void;
}

export const IncidentDetailModal: React.FC<Props> = ({ incidentId, onClose }) => {
  const {
    incidents,
    updateIncidentStatus,
    assignResponder,
    vehicle,
    emergencyContacts,
    medicalInfo,
    privacyConsent,
  } = useEmergency();

  const [cadNote, setCadNote] = useState('');
  const [selectedResponder, setSelectedResponder] = useState('Medic Unit 402 (EMT-P Elena Rostova)');
  const [responderEta, setResponderEta] = useState(4);

  const incident = incidents.find((i) => i.id === incidentId);
  if (!incident) return null;

  const isEmergency = incident.type === 'emergency_sos' || incident.type === 'ambulance';

  const handleStatusChange = (status: IncidentStatus) => {
    updateIncidentStatus(incident.id, status, cadNote || undefined);
    setCadNote('');
  };

  const handleAssignResponder = (e: React.FormEvent) => {
    e.preventDefault();
    assignResponder(
      incident.id,
      selectedResponder,
      'Metro Emergency Regional Command',
      responderEta
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-[14px] border border-[#E2E8F0] shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Top Header */}
        <div
          className={`p-4 text-white flex items-center justify-between shrink-0 ${
            isEmergency ? 'bg-[#D93636]' : 'bg-[#142B4A]'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-[8px] bg-white/20 flex items-center justify-center shrink-0">
              {isEmergency ? (
                <AlertOctagon className="w-5 h-5 text-white" />
              ) : (
                <FileText className="w-5 h-5 text-white" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-[17px] font-bold text-white">
                  Incident CAD #{incident.id}
                </h3>
                <span className="px-2 py-0.5 rounded-[4px] text-[10px] font-extrabold uppercase bg-white text-[#172B43]">
                  {incident.status.replace('_', ' ')}
                </span>
              </div>
              <p className="text-xs text-white/90">
                {incident.vehicleDescription} • Safe-QR: {incident.vehiclePlate}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white p-1 rounded-md"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Top Quick Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3 bg-[#F5F7FA] rounded-[10px] border border-[#E2E8F0]">
              <span className="text-[11px] font-semibold text-[#718096] uppercase tracking-wider block">
                Incident Location
              </span>
              <div className="flex items-start gap-1.5 mt-1 text-xs font-medium text-[#172B43]">
                <MapPin className="w-3.5 h-3.5 text-[#D93636] shrink-0 mt-0.5" />
                <span>{incident.location.address}</span>
              </div>
              <span className="text-[10px] text-[#718096] font-mono mt-0.5 block">
                Lat: {incident.location.lat.toFixed(4)}, Lng: {incident.location.lng.toFixed(4)}
              </span>
            </div>

            <div className="p-3 bg-[#F5F7FA] rounded-[10px] border border-[#E2E8F0]">
              <span className="text-[11px] font-semibold text-[#718096] uppercase tracking-wider block">
                Reporter on Scene
              </span>
              <span className="text-xs font-semibold text-[#172B43] mt-1 block">
                {incident.reporterName || 'Public Safe-QR Scan'}
              </span>
              <span className="text-[11px] text-[#718096] font-mono mt-0.5 block">
                {incident.reporterPhone || 'No contact entered'}
              </span>
            </div>

            <div className="p-3 bg-[#F5F7FA] rounded-[10px] border border-[#E2E8F0]">
              <span className="text-[11px] font-semibold text-[#718096] uppercase tracking-wider block">
                Assigned Unit
              </span>
              {incident.assignedResponder ? (
                <div>
                  <span className="text-xs font-bold text-[#142B4A] mt-1 block">
                    {incident.assignedResponder.name}
                  </span>
                  <span className="text-[11px] text-[#23845B] font-semibold mt-0.5 block">
                    ETA: {incident.assignedResponder.etaMinutes} min ({incident.assignedResponder.type})
                  </span>
                </div>
              ) : (
                <span className="text-xs text-[#D99A27] font-medium mt-1 block">
                  Awaiting Unit Assignment
                </span>
              )}
            </div>
          </div>

          {/* Description */}
          <div className="p-3.5 rounded-[10px] bg-white border border-[#E2E8F0] shadow-2xs">
            <h4 className="text-xs font-semibold text-[#718096] uppercase tracking-wider mb-1">
              Field Report Description
            </h4>
            <p className="text-sm text-[#172B43] leading-relaxed">
              {incident.description}
            </p>
          </div>

          {/* Emergency Medical Telemetry (If SOS and consented) */}
          {isEmergency && (
            <div className="p-4 rounded-[10px] bg-[#FFF8F8] border border-[#D93636]/30 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#D93636] uppercase tracking-wider flex items-center gap-1.5">
                  <AlertOctagon className="w-4 h-4" />
                  Authorized Driver Medical Telemetry
                </span>
                <span className="text-[10px] font-medium text-[#718096]">
                  Consent-authorized for verified EMS
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1 text-xs">
                <div className="bg-white p-2 rounded border border-[#E2E8F0]">
                  <span className="text-[11px] text-[#718096]">Blood Type</span>
                  <span className="font-bold text-[#D93636] block text-sm">
                    {privacyConsent.shareBloodTypeOnSos ? medicalInfo.bloodType : '[Confidential]'}
                  </span>
                </div>

                <div className="bg-white p-2 rounded border border-[#E2E8F0]">
                  <span className="text-[11px] text-[#718096]">Severe Allergies</span>
                  <span className="font-semibold text-[#172B43] block">
                    {privacyConsent.shareAllergiesOnSos ? medicalInfo.allergies.join(', ') : '[Restricted]'}
                  </span>
                </div>

                <div className="bg-white p-2 rounded border border-[#E2E8F0]">
                  <span className="text-[11px] text-[#718096]">Primary Contact</span>
                  <span className="font-semibold text-[#172B43] block">
                    {emergencyContacts[0]?.name} ({emergencyContacts[0]?.phone})
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Unit Dispatch Form */}
          <div className="p-4 bg-[#F5F7FA] rounded-[10px] border border-[#E2E8F0] space-y-3">
            <h4 className="text-xs font-semibold text-[#142B4A] uppercase tracking-wider flex items-center gap-1.5">
              <Users className="w-4 h-4" />
              Dispatch & CAD Routing
            </h4>

            <form onSubmit={handleAssignResponder} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2">
                <label className="block text-[11px] font-medium text-[#718096] mb-1">
                  Available Patrol / EMS Units
                </label>
                <select
                  value={selectedResponder}
                  onChange={(e) => setSelectedResponder(e.target.value)}
                  className="w-full text-xs p-2 rounded-[8px] border border-[#E2E8F0] bg-white text-[#172B43]"
                >
                  <option value="Medic Unit 402 (EMT-P Elena Rostova)">
                    Medic Unit 402 (EMT-P Elena Rostova) - 0.8 mi away
                  </option>
                  <option value="State Patrol Cruiser 14 (Officer Kowalski)">
                    State Patrol Cruiser 14 (Officer Kowalski) - 1.4 mi away
                  </option>
                  <option value="Fire Rescue Squad 09">
                    Fire Rescue Squad 09 - Heavy Extraction Unit - 2.1 mi away
                  </option>
                  <option value="FixPoint Roadside Patrol 03">
                    FixPoint Roadside Patrol 03 (Tow & Hazard) - 3.0 mi away
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[#718096] mb-1">
                  Estimated Travel (Min)
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    min={1}
                    max={60}
                    value={responderEta}
                    onChange={(e) => setResponderEta(Number(e.target.value))}
                    className="w-16 text-xs p-2 rounded-[8px] border border-[#E2E8F0] bg-white text-center"
                  />
                  <button
                    type="submit"
                    className="flex-1 py-2 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-xs font-semibold transition-colors"
                  >
                    Assign Unit
                  </button>
                </div>
              </div>
            </form>
          </div>

          {/* Incident Timeline Audit Log */}
          <div>
            <h4 className="text-xs font-semibold text-[#718096] uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-[#718096]" />
              Event Timeline & Telemetry Audit Trail
            </h4>
            <div className="border border-[#E2E8F0] rounded-[10px] divide-y divide-[#E2E8F0] overflow-hidden bg-white text-xs">
              {incident.timeline.map((event) => (
                <div key={event.id} className="p-3 flex items-start gap-3 hover:bg-[#F5F7FA]/50 transition-colors">
                  <span
                    className={`mt-1 w-2.5 h-2.5 rounded-full shrink-0 ${
                      event.badgeType === 'danger'
                        ? 'bg-[#D93636]'
                        : event.badgeType === 'warning'
                        ? 'bg-[#D99A27]'
                        : event.badgeType === 'success'
                        ? 'bg-[#23845B]'
                        : 'bg-[#142B4A]'
                    }`}
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-[#172B43]">{event.title}</span>
                      <span className="text-[11px] text-[#718096]">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-[#718096] mt-0.5 text-xs">{event.description}</p>
                    <span className="text-[10px] text-[#142B4A] font-medium mt-1 inline-block">
                      Actor: {event.actor}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Actions: Status Transition */}
        <div className="p-4 bg-[#F5F7FA] border-t border-[#E2E8F0] flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#718096] font-medium">Set Status:</span>
            <button
              onClick={() => handleStatusChange('en_route')}
              className="px-2.5 py-1.5 rounded-[6px] text-xs font-medium border border-[#E2E8F0] bg-white hover:bg-slate-50 text-[#172B43]"
            >
              En Route
            </button>
            <button
              onClick={() => handleStatusChange('on_scene')}
              className="px-2.5 py-1.5 rounded-[6px] text-xs font-medium border border-[#E2E8F0] bg-white hover:bg-slate-50 text-[#172B43]"
            >
              On Scene
            </button>
            <button
              onClick={() => handleStatusChange('resolved')}
              className="px-2.5 py-1.5 rounded-[6px] text-xs font-medium bg-[#23845B] hover:bg-[#1f734f] text-white"
            >
              Resolve & Close
            </button>
          </div>

          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-xs font-medium"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
};
