import React, { useState, useEffect } from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import { IncidentStatus } from '../../types';
import {
  ShieldCheck,
  Clock,
  MapPin,
  HeartPulse,
  Phone,
  AlertOctagon,
  CheckCircle,
  FileText,
  Navigation,
  Car,
  Lock,
  Unlock,
  Radio,
  Ambulance,
  AlertTriangle,
} from 'lucide-react';

interface Props {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const ResponderDashboard: React.FC<Props> = ({ activeTab, setActiveTab }) => {
  const {
    responderUser,
    incidents,
    updateIncidentStatus,
    unlockMedicalAccess,
    vehicle,
    emergencyContacts,
    medicalInfo,
    privacyConsent,
    showToast,
  } = useEmergency();

  // Active assigned incident
  const assignedIncident =
    incidents.find((i) => i.assignedResponder?.id === responderUser.id || i.type === 'emergency_sos') ||
    incidents[0];

  // Access expiry countdown timer simulation
  const [secondsRemaining, setSecondsRemaining] = useState(42 * 60 + 18);
  const [isMedicalUnlocked, setIsMedicalUnlocked] = useState(
    assignedIncident?.medicalAccessed || false
  );
  const [triageNotes, setTriageNotes] = useState('');

  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTimer = (totalSec: number) => {
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    return `${m}m ${s < 10 ? '0' : ''}${s}s`;
  };

  const handleUnlockMedical = () => {
    if (assignedIncident) {
      unlockMedicalAccess(assignedIncident.id);
      setIsMedicalUnlocked(true);
    }
  };

  const handleStatusUpdate = (newStatus: IncidentStatus) => {
    if (assignedIncident) {
      updateIncidentStatus(
        assignedIncident.id,
        newStatus,
        `Responder ${responderUser.name} set status: ${newStatus}`
      );
    }
  };

  const handleAddTriageLog = (e: React.FormEvent) => {
    e.preventDefault();
    if (!triageNotes.trim() || !assignedIncident) return;
    updateIncidentStatus(
      assignedIncident.id,
      assignedIncident.status,
      `[Triage Note] ${triageNotes.trim()}`
    );
    setTriageNotes('');
    showToast('Triage observation logged to CAD incident record', 'success');
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Verification Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-[26px] sm:text-[28px] font-semibold text-[#172B43] tracking-tight">
              Responder CAD Terminal
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#23845B]/15 text-[#23845B] flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              Verified First Responder
            </span>
          </div>
          <p className="text-[14px] text-[#718096] mt-1">
            Authorized field console for {responderUser.agency} • {responderUser.unitId}.
          </p>
        </div>

        {/* Access Expiry Indicator (Section 9 requirement) */}
        <div className="flex items-center gap-3 p-3 bg-white rounded-[10px] border border-[#E2E8F0] shadow-xs">
          <Clock className="w-4 h-4 text-[#D99A27] shrink-0" />
          <div className="text-right">
            <span className="text-[11px] font-medium text-[#718096] block uppercase tracking-wider">
              Emergency Access Expiry
            </span>
            <span className="text-sm font-mono font-bold text-[#142B4A]">
              {formatTimer(secondsRemaining)}
            </span>
          </div>
        </div>
      </div>

      {/* Responder Verification Banner Card */}
      <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-4.5 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-[9px] bg-[#142B4A] text-white flex items-center justify-center font-bold">
            <Ambulance className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[15px] font-semibold text-[#172B43]">
                {responderUser.name}
              </span>
              <span className="text-xs font-mono font-semibold text-[#718096]">
                [{responderUser.badgeNumber}]
              </span>
            </div>
            <p className="text-xs text-[#718096] mt-0.5">
              Unit: <strong className="text-[#142B4A]">{responderUser.unitId}</strong> • Verified Agency: {responderUser.agency}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <div className="px-2.5 py-1 rounded bg-[#F5F7FA] border border-[#E2E8F0] text-[#718096] font-mono">
            Session Token: <span className="text-[#142B4A] font-semibold">FP-CAD-9921-X</span>
          </div>
          <span className="flex items-center gap-1 text-[#23845B] font-semibold">
            <CheckCircle className="w-3.5 h-3.5" />
            Active
          </span>
        </div>
      </div>

      {/* Main Grid: Assigned Incident + Authorized Information */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Assigned Incident Card & Field Controls (Section 9 requirement) */}
        <div className="lg:col-span-7 space-y-4">
          {assignedIncident ? (
            <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-6 shadow-xs space-y-5">
              {/* Header with Priority indicator */}
              <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-[6px] text-xs font-bold uppercase tracking-wider bg-[#D93636] text-white flex items-center gap-1.5">
                    <AlertOctagon className="w-3.5 h-3.5" />
                    Priority 1 • Critical SOS
                  </span>
                  <span className="font-mono text-xs font-semibold text-[#718096]">
                    #{assignedIncident.id}
                  </span>
                </div>

                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    assignedIncident.status === 'on_scene'
                      ? 'bg-[#23845B]/15 text-[#23845B]'
                      : 'bg-[#D99A27]/20 text-[#D99A27]'
                  }`}
                >
                  {assignedIncident.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>

              {/* Target Vehicle Spec */}
              <div className="bg-[#F5F7FA] p-3.5 rounded-[10px] border border-[#E2E8F0] grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div>
                  <span className="text-[11px] text-[#718096] block">Vehicle Plate</span>
                  <span className="font-mono font-bold text-sm text-[#142B4A]">
                    {assignedIncident.vehiclePlate}
                  </span>
                </div>
                <div>
                  <span className="text-[11px] text-[#718096] block">Vehicle Description</span>
                  <span className="font-semibold text-[#172B43]">
                    {assignedIncident.vehicleDescription}
                  </span>
                </div>
                <div>
                  <span className="text-[11px] text-[#718096] block">Safe-QR Code</span>
                  <span className="font-mono font-medium text-[#718096]">
                    {vehicle.safeQrCode}
                  </span>
                </div>
              </div>

              {/* Scene Location */}
              <div className="p-3.5 rounded-[10px] bg-white border border-[#E2E8F0] space-y-1 text-xs">
                <span className="font-semibold text-[#718096] uppercase tracking-wider text-[11px] block">
                  Incident Scene & Coordinates
                </span>
                <div className="flex items-center gap-2 text-[#172B43] font-medium text-sm">
                  <MapPin className="w-4 h-4 text-[#D93636] shrink-0" />
                  <span>{assignedIncident.location.address}</span>
                </div>
                <div className="flex items-center justify-between text-[#718096] text-[11px] pt-1">
                  <span className="font-mono">
                    Lat: {assignedIncident.location.lat.toFixed(4)}, Lng: {assignedIncident.location.lng.toFixed(4)} (±{assignedIncident.location.accuracyMeters}m)
                  </span>
                  <span className="text-[#23845B] font-semibold">ETA: 3 mins (0.8 mi)</span>
                </div>
              </div>

              {/* Dispatch Report Narrative */}
              <div className="p-3.5 rounded-[10px] bg-[#FFF8F8] border border-[#D93636]/20 text-xs">
                <span className="font-bold text-[#D93636] block uppercase tracking-wider text-[11px]">
                  Caller & Dispatch Narrative
                </span>
                <p className="text-[#172B43] mt-1 text-sm leading-relaxed">
                  {assignedIncident.description}
                </p>
                <div className="mt-2 text-[11px] text-[#718096]">
                  Reported by: <strong>{assignedIncident.reporterName}</strong> ({assignedIncident.reporterPhone})
                </div>
              </div>

              {/* Field Action Buttons */}
              <div className="space-y-2 pt-2 border-t border-[#E2E8F0]">
                <span className="text-xs font-semibold text-[#718096] uppercase tracking-wider block">
                  Scene Status Progression
                </span>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => handleStatusUpdate('en_route')}
                    className={`py-2 rounded-[8px] text-xs font-semibold transition-colors border ${
                      assignedIncident.status === 'en_route'
                        ? 'bg-[#142B4A] text-white border-[#142B4A]'
                        : 'bg-white text-[#172B43] border-[#E2E8F0] hover:bg-slate-50'
                    }`}
                  >
                    1. En Route
                  </button>
                  <button
                    onClick={() => handleStatusUpdate('on_scene')}
                    className={`py-2 rounded-[8px] text-xs font-semibold transition-colors border ${
                      assignedIncident.status === 'on_scene'
                        ? 'bg-[#142B4A] text-white border-[#142B4A]'
                        : 'bg-white text-[#172B43] border-[#E2E8F0] hover:bg-slate-50'
                    }`}
                  >
                    2. Arrived On Scene
                  </button>
                  <button
                    onClick={() => handleStatusUpdate('resolved')}
                    className="py-2 rounded-[8px] text-xs font-semibold bg-[#23845B] hover:bg-[#1f734f] text-white transition-colors"
                  >
                    3. Scene Cleared
                  </button>
                </div>
              </div>

              {/* Log Triage Notes */}
              <form onSubmit={handleAddTriageLog} className="pt-2">
                <label className="block text-[12px] font-medium text-[#172B43] mb-1">
                  Log Field Triage Observation
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={triageNotes}
                    onChange={(e) => setTriageNotes(e.target.value)}
                    placeholder="e.g. Patient extracted, vitals stable, BP 124/82..."
                    className="flex-1 text-xs p-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A]"
                  />
                  <button
                    type="submit"
                    className="px-3 py-2 bg-[#142B4A] text-white rounded-[8px] text-xs font-medium hover:bg-[#203D60]"
                  >
                    Log to CAD
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-8 text-center text-[#718096]">
              No active incidents currently assigned to your unit.
            </div>
          )}
        </div>

        {/* Right Column: Authorized Information Panels & Permission Boundaries (Section 9 requirement) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Authorized Medical Information Panel */}
          <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
              <div className="flex items-center gap-2">
                <HeartPulse className="w-5 h-5 text-[#D93636]" />
                <h3 className="text-[16px] font-semibold text-[#172B43]">
                  Authorized Medical Data
                </h3>
              </div>
              <span className="text-[11px] font-semibold text-[#23845B] bg-[#23845B]/10 px-2 py-0.5 rounded-full">
                Audit Logged
              </span>
            </div>

            {/* Decryption status */}
            {!isMedicalUnlocked ? (
              <div className="p-4 bg-[#F5F7FA] rounded-[10px] border border-[#E2E8F0] text-center space-y-3">
                <Lock className="w-8 h-8 text-[#718096] mx-auto" />
                <div>
                  <h4 className="text-sm font-semibold text-[#172B43]">
                    Emergency EHR Telemetry Locked
                  </h4>
                  <p className="text-xs text-[#718096] mt-0.5 max-w-xs mx-auto">
                    Requires verified responder authorization to decrypt full medical history under HIPAA emergency exception.
                  </p>
                </div>
                <button
                  onClick={handleUnlockMedical}
                  className="px-4 py-2 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-xs font-semibold flex items-center justify-center gap-2 mx-auto shadow-xs"
                >
                  <Unlock className="w-3.5 h-3.5" />
                  <span>Decrypt Patient Medical Profile</span>
                </button>
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                <div className="p-3 bg-[#FFF5F5] rounded-[8px] border border-[#D93636]/30">
                  <span className="text-[11px] font-semibold text-[#718096] uppercase tracking-wider block">
                    Patient Blood Group
                  </span>
                  <span className="text-xl font-bold text-[#D93636] block mt-0.5">
                    {medicalInfo.bloodType}
                  </span>
                  <span className="text-[10px] text-[#718096] block mt-0.5">
                    {medicalInfo.organDonor ? 'Registered Organ Donor' : 'Standard Status'}
                  </span>
                </div>

                <div className="p-3 bg-[#F5F7FA] rounded-[8px] border border-[#E2E8F0]">
                  <span className="text-[11px] font-semibold text-[#718096] uppercase tracking-wider block">
                    Critical Drug Allergies
                  </span>
                  <div className="mt-1 space-y-1">
                    {medicalInfo.allergies.map((allg, idx) => (
                      <span
                        key={idx}
                        className="inline-block mr-1.5 px-2 py-0.5 rounded-[4px] bg-[#D93636]/10 text-[#D93636] font-semibold text-[11px]"
                      >
                        {allg}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-3 bg-[#F5F7FA] rounded-[8px] border border-[#E2E8F0]">
                  <span className="text-[11px] font-semibold text-[#718096] uppercase tracking-wider block">
                    Active Conditions & Meds
                  </span>
                  <p className="text-[#172B43] font-medium mt-1">
                    {medicalInfo.medicalConditions.join(', ')}
                  </p>
                  <p className="text-[#718096] mt-0.5 text-[11px]">
                    Current: {medicalInfo.medications.join(', ')}
                  </p>
                </div>

                <div className="p-3 bg-[#F8FAFC] rounded-[8px] border border-[#E2E8F0] space-y-1">
                  <span className="text-[11px] font-semibold text-[#718096] uppercase tracking-wider block">
                    Driver In-Vehicle Placement Note
                  </span>
                  <p className="text-[#172B43] text-xs">
                    "{medicalInfo.additionalNotes}"
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Emergency Contact Quick Dial Panel */}
          <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-5 shadow-xs space-y-3">
            <h3 className="text-[15px] font-semibold text-[#172B43] flex items-center gap-2">
              <Phone className="w-4 h-4 text-[#142B4A]" />
              <span>Next of Kin Emergency Contacts</span>
            </h3>

            <div className="space-y-2 text-xs">
              {emergencyContacts.map((cnt) => (
                <div
                  key={cnt.id}
                  className="p-2.5 rounded-[8px] bg-[#F5F7FA] border border-[#E2E8F0] flex items-center justify-between"
                >
                  <div>
                    <span className="font-semibold text-[#172B43] block">
                      {cnt.name} ({cnt.relationship})
                    </span>
                    <span className="font-mono text-[11px] text-[#718096]">
                      {cnt.phone}
                    </span>
                  </div>
                  <a
                    href={`tel:${cnt.phone}`}
                    className="px-2.5 py-1 bg-white hover:bg-slate-100 text-[#142B4A] border border-[#E2E8F0] rounded-[6px] font-medium text-xs flex items-center gap-1"
                  >
                    <Phone className="w-3 h-3 text-[#23845B]" />
                    <span>Call</span>
                  </a>
                </div>
              ))}
            </div>
          </div>

          {/* Clear Permission Boundaries & Compliance (Section 9 requirement) */}
          <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-5 shadow-xs space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#172B43]">
              <Lock className="w-4 h-4 text-[#142B4A]" />
              <span>Authorized Access Scope & Boundaries</span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="p-2.5 rounded-[8px] bg-[#F2FAF6] border border-[#23845B]/20 text-[#23845B]">
                <strong className="block text-[11px] uppercase tracking-wider">
                  ✓ Authorized for EMT-P Elena Rostova
                </strong>
                <span className="text-[11px] text-[#172B43] mt-0.5 block">
                  Blood type, allergies, medications, next of kin contacts, real-time GPS telemetry.
                </span>
              </div>

              <div className="p-2.5 rounded-[8px] bg-[#FFF5F5] border border-[#D93636]/20 text-[#D93636]">
                <strong className="block text-[11px] uppercase tracking-wider">
                  ✕ Restricted by Privacy Sandbox
                </strong>
                <span className="text-[11px] text-[#718096] mt-0.5 block">
                  Home residential address, full insurance policy details, unrelated medical records.
                </span>
              </div>
            </div>

            <div className="text-[10px] text-[#718096] leading-tight">
              All views cryptographically signed & archived under FixPoint Safe-QR CAD audit specification 2026.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
