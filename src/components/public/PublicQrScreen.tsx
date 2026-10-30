import React, { useEffect, useState } from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import { BrandLogo } from '../common/BrandLogo';
import { PublicAmbulanceModal } from './PublicAmbulanceModal';
import { PublicPoliceModal } from './PublicPoliceModal';
import { PublicReportIncidentModal } from './PublicReportIncidentModal';
import { PublicSosTriggerModal } from './PublicSosTriggerModal';
import {
  Ambulance,
  Shield,
  FileText,
  AlertOctagon,
  Car,
  MapPin,
  CheckCircle,
  RefreshCw,
  ShieldOff,
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface QrResolution {
  code_identifier: string;
  status: 'ACTIVE';
  vehicle_registration: string;
  vehicle_model: string;
  is_active: true;
  scan_count: number;
  last_scanned_at: string;
}

type QrState =
  | { status: 'checking' }
  | { status: 'valid'; data: QrResolution }
  | { status: 'unavailable'; message: string };

const getQrToken = (): string | null => {
  const params = new URLSearchParams(window.location.search);
  const queryToken = params.get('qr') || params.get('code');
  if (queryToken) return queryToken;

  const pathParts = window.location.pathname.split('/').filter(Boolean);
  const qrIndex = pathParts.indexOf('qr');
  return qrIndex >= 0 ? pathParts[qrIndex + 1] || null : null;
};

export const PublicQrScreen: React.FC = () => {
  const { vehicle, updateVehicle, isMobileFrame } = useEmergency();
  const [qrState, setQrState] = useState<QrState>({ status: 'checking' });
  const [activeModal, setActiveModal] = useState<
    'ambulance' | 'police' | 'incident' | 'sos' | null
  >(null);

  const qrToken = getQrToken();

  useEffect(() => {
    const controller = new AbortController();
    const token = qrToken;

    if (!token) {
      setQrState({
        status: 'unavailable',
        message: 'This Safe-QR link does not contain a QR token.',
      });
      return () => controller.abort();
    }

    setQrState({ status: 'checking' });
    fetch(`${API_BASE_URL}/qr/resolve/${encodeURIComponent(token)}/`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    })
      .then(async (response) => {
        const payload = await response.json().catch(() => null);
        if (!response.ok || !payload?.data?.is_active) {
          throw new Error(payload?.message || 'This Safe-QR is invalid or unavailable.');
        }
        const resolution = payload.data as QrResolution;
        updateVehicle({
          safeQrCode: resolution.code_identifier,
          licensePlate: resolution.vehicle_registration || vehicle.licensePlate,
          model: resolution.vehicle_model || vehicle.model,
        });
        setQrState({ status: 'valid', data: resolution });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setQrState({
          status: 'unavailable',
          message:
            error instanceof Error
              ? error.message
              : 'The Safe-QR could not be verified. Please try again.',
        });
      });

    return () => controller.abort();
  }, [qrToken]);

  if (qrState.status !== 'valid') {
    const isChecking = qrState.status === 'checking';
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center py-6 px-4 bg-[#F5F7FA]">
        <div className="w-full max-w-md bg-white rounded-[14px] border border-[#E2E8F0] shadow-xl p-7 text-center">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto ${isChecking ? 'bg-[#F5F7FA] text-[#142B4A]' : 'bg-[#FFF5F5] text-[#D93636]'}`}>
            {isChecking ? <RefreshCw className="w-8 h-8 animate-spin" /> : <ShieldOff className="w-8 h-8" />}
          </div>
          <h1 className="text-xl font-semibold text-[#172B43] mt-5">
            {isChecking ? 'Verifying Safe-QR…' : 'Safe-QR unavailable'}
          </h1>
          <p className="text-sm text-[#718096] mt-2">
            {isChecking
              ? 'Please wait while we validate this vehicle QR code.'
              : qrState.message}
          </p>
          {!isChecking && (
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-5 px-4 py-2.5 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-sm font-medium"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    );
  }

  const resolvedVehicle = {
    ...vehicle,
    safeQrCode: qrState.data.code_identifier,
    licensePlate: qrState.data.vehicle_registration || vehicle.licensePlate,
    model: qrState.data.vehicle_model || vehicle.model,
  };

  const mainInterface = (
    <div className="w-full flex flex-col items-center justify-between min-h-[580px] p-5 sm:p-7 select-none">
      {/* 1. Compact FixPoint Drive Logo / Header */}
      <div className="w-full flex items-center justify-between border-b border-[#E2E8F0] pb-4">
        <BrandLogo size="sm" showSubtitle={false} />
        
        {/* Compact Vehicle Identification Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] bg-[#F5F7FA] border border-[#E2E8F0] text-[11px] font-medium text-[#172B43]">
          <Car className="w-3.5 h-3.5 text-[#142B4A]" />
          <span className="font-mono font-semibold">{resolvedVehicle.licensePlate}</span>
        </div>
      </div>

      {/* 2 & 3: Simple heading & supporting text */}
      <div className="w-full my-6 text-center">
        <h1 className="text-[26px] sm:text-[28px] font-semibold text-[#172B43] tracking-tight leading-tight">
          How can we help?
        </h1>
        <p className="text-[14px] sm:text-[15px] text-[#718096] mt-1.5 max-w-sm mx-auto">
          Choose an option to get the assistance you need.
        </p>
      </div>

      {/* 4. Four large, clearly distinguishable action cards arranged in a 2 x 2 grid */}
      <div className="w-full grid grid-cols-2 gap-3.5 sm:gap-4 flex-1 my-auto">
        {/* Card 1: Call Ambulance */}
        <button
          onClick={() => setActiveModal('ambulance')}
          className="group flex flex-col items-center justify-center p-4 sm:p-5 text-center bg-white rounded-[12px] border border-[#E2E8F0] hover:border-[#142B4A] hover:shadow-md transition-all duration-150 cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#142B4A]/20"
        >
          <div className="w-13 h-13 sm:w-14 sm:h-14 rounded-[10px] bg-[#F5F7FA] border border-[#E2E8F0] group-hover:bg-[#142B4A] group-hover:border-[#142B4A] flex items-center justify-center transition-colors mb-3">
            <Ambulance className="w-7 h-7 text-[#142B4A] group-hover:text-white transition-colors" />
          </div>
          <span className="text-[15px] sm:text-[16px] font-semibold text-[#172B43] group-hover:text-[#142B4A] leading-tight">
            Call Ambulance
          </span>
          <span className="text-[12px] text-[#718096] mt-1 line-clamp-2 leading-snug">
            Medical emergency & rapid EMS response
          </span>
        </button>

        {/* Card 2: Call Police */}
        <button
          onClick={() => setActiveModal('police')}
          className="group flex flex-col items-center justify-center p-4 sm:p-5 text-center bg-white rounded-[12px] border border-[#E2E8F0] hover:border-[#142B4A] hover:shadow-md transition-all duration-150 cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#142B4A]/20"
        >
          <div className="w-13 h-13 sm:w-14 sm:h-14 rounded-[10px] bg-[#F5F7FA] border border-[#E2E8F0] group-hover:bg-[#142B4A] group-hover:border-[#142B4A] flex items-center justify-center transition-colors mb-3">
            <Shield className="w-7 h-7 text-[#142B4A] group-hover:text-white transition-colors" />
          </div>
          <span className="text-[15px] sm:text-[16px] font-semibold text-[#172B43] group-hover:text-[#142B4A] leading-tight">
            Call Police
          </span>
          <span className="text-[12px] text-[#718096] mt-1 line-clamp-2 leading-snug">
            Highway patrol & law enforcement
          </span>
        </button>

        {/* Card 3: Report an Incident */}
        <button
          onClick={() => setActiveModal('incident')}
          className="group flex flex-col items-center justify-center p-4 sm:p-5 text-center bg-white rounded-[12px] border border-[#E2E8F0] hover:border-[#142B4A] hover:shadow-md transition-all duration-150 cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#142B4A]/20"
        >
          <div className="w-13 h-13 sm:w-14 sm:h-14 rounded-[10px] bg-[#F5F7FA] border border-[#E2E8F0] group-hover:bg-[#142B4A] group-hover:border-[#142B4A] flex items-center justify-center transition-colors mb-3">
            <FileText className="w-7 h-7 text-[#142B4A] group-hover:text-white transition-colors" />
          </div>
          <span className="text-[15px] sm:text-[16px] font-semibold text-[#172B43] group-hover:text-[#142B4A] leading-tight">
            Report an Incident
          </span>
          <span className="text-[12px] text-[#718096] mt-1 line-clamp-2 leading-snug">
            Parking bump, blocked road, or minor notice
          </span>
        </button>

        {/* Card 4: Create Emergency Alert (Stronger visual emphasis using Emergency Red) */}
        <button
          onClick={() => setActiveModal('sos')}
          className="group relative flex flex-col items-center justify-center p-4 sm:p-5 text-center bg-[#FFF8F8] rounded-[12px] border-2 border-[#D93636] hover:bg-[#D93636] hover:border-[#BD2929] hover:shadow-lg transition-all duration-150 cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#D93636]/30 overflow-hidden"
        >
          {/* Subtle Emergency Badge */}
          <div className="absolute top-2.5 right-2.5 px-1.5 py-0.5 rounded-[4px] bg-[#D93636] group-hover:bg-white text-[10px] font-bold text-white group-hover:text-[#D93636] uppercase tracking-wider">
            Critical SOS
          </div>

          <div className="w-13 h-13 sm:w-14 sm:h-14 rounded-[10px] bg-[#D93636] group-hover:bg-white flex items-center justify-center transition-colors mb-3 shadow-xs">
            <AlertOctagon className="w-7 h-7 text-white group-hover:text-[#D93636] transition-colors" />
          </div>
          <span className="text-[15px] sm:text-[16px] font-bold text-[#D93636] group-hover:text-white leading-tight">
            Create Emergency Alert
          </span>
          <span className="text-[12px] text-[#718096] group-hover:text-white/90 mt-1 line-clamp-2 leading-snug">
            Instant priority dispatch to CAD & emergency contacts
          </span>
        </button>

      </div>

      {/* Bottom Minimal Location & Security Status */}
      <div className="w-full mt-6 pt-4 border-t border-[#E2E8F0] flex items-center justify-between text-[11px] text-[#718096]">
        <div className="flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 text-[#23845B]" />
          <span>GPS Active & Verifiable</span>
        </div>
        <div className="flex items-center gap-1 text-[#23845B]">
          <CheckCircle className="w-3 h-3" />
          <span>Encrypted Safe-QR Link</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center py-6 px-4 bg-[#F5F7FA]">
      {/* Mobile-first presentation: can be rendered in a realistic phone bezel or expanded */}
      {isMobileFrame ? (
        <div className="w-full max-w-[420px] bg-white rounded-[24px] border-[6px] border-[#142B4A] shadow-xl overflow-hidden relative">
          {/* Smartphone Speaker notch simulation */}
          <div className="h-4 bg-[#142B4A] flex items-center justify-center">
            <div className="w-12 h-1 bg-slate-400 rounded-full"></div>
          </div>

          {mainInterface}
        </div>
      ) : (
        <div className="w-full max-w-lg bg-white rounded-[14px] border border-[#E2E8F0] shadow-sm">
          {mainInterface}
        </div>
      )}

      {/* Action Modals */}
      <PublicAmbulanceModal
        isOpen={activeModal === 'ambulance'}
        onClose={() => setActiveModal(null)}
      />
      <PublicPoliceModal
        isOpen={activeModal === 'police'}
        onClose={() => setActiveModal(null)}
      />
      <PublicReportIncidentModal
        isOpen={activeModal === 'incident'}
        onClose={() => setActiveModal(null)}
      />
      <PublicSosTriggerModal
        isOpen={activeModal === 'sos'}
        onClose={() => setActiveModal(null)}
      />
    </div>
  );
};
