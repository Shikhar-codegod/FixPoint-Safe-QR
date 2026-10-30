import React, { useState } from 'react';
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
} from 'lucide-react';

export const PublicQrScreen: React.FC = () => {
  const { vehicle, isMobileFrame } = useEmergency();

  const [activeModal, setActiveModal] = useState<
    'ambulance' | 'police' | 'incident' | 'sos' | null
  >(null);

  const mainInterface = (
    <div className="w-full flex flex-col items-center justify-between min-h-[580px] p-5 sm:p-7 select-none">
      {/* 1. Compact FixPoint Drive Logo / Header */}
      <div className="w-full flex items-center justify-between border-b border-[#E2E8F0] pb-4">
        <BrandLogo size="sm" showSubtitle={false} />
        
        {/* Compact Vehicle Identification Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] bg-[#F5F7FA] border border-[#E2E8F0] text-[11px] font-medium text-[#172B43]">
          <Car className="w-3.5 h-3.5 text-[#142B4A]" />
          <span className="font-mono font-semibold">{vehicle.licensePlate}</span>
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
