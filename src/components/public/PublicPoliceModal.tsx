import React, { useState } from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import { Shield, MapPin, Phone, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const PublicPoliceModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { vehicle } = useEmergency();
  const [callerPhone, setCallerPhone] = useState('');
  const [reason, setReason] = useState('Traffic Accident / Highway Collision');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-[14px] border border-[#E2E8F0] shadow-xl w-full max-w-md overflow-hidden">
        <div className="bg-[#142B4A] text-white p-4.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-[8px] bg-[#203D60] flex items-center justify-center shrink-0 border border-slate-600">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-[17px] font-semibold text-white">Call Police (112)</h3>
              <p className="text-xs text-slate-300">
                Plate: {vehicle.licensePlate} • Safe-QR Emergency
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-300 hover:text-white p-1 rounded-md">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form className="p-5 space-y-4">
          <div className="bg-[#F5F7FA] p-3 rounded-[10px] border border-[#E2E8F0] text-xs text-[#172B43]">
            <span className="font-semibold">Manual emergency call</span>
            <p className="text-[11px] text-[#718096] mt-0.5">
              FixPoint will open your phone dialer. It does not place, verify, or claim a police dispatch.
            </p>
          </div>

          <div className="bg-[#F5F7FA] p-3 rounded-[10px] border border-[#E2E8F0] flex items-start gap-2.5">
            <MapPin className="w-4 h-4 text-[#142B4A] shrink-0 mt-0.5" />
            <div className="text-xs">
              <span className="font-medium text-[#172B43]">Location available to you:</span>
              <p className="text-[#718096] text-[11px] mt-0.5">
                Vehicle {vehicle.make} {vehicle.model} ({vehicle.licensePlate})
              </p>
            </div>
          </div>

          <div>
            <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
              Situation Type
            </label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full text-xs p-2.5 rounded-[8px] border border-[#E2E8F0] bg-white focus:outline-none focus:border-[#142B4A] text-[#172B43]"
            >
              <option value="Traffic Accident / Highway Collision">Traffic Accident / Highway Collision</option>
              <option value="Hit and Run Incident">Hit and Run Incident</option>
              <option value="Vandalism or Vehicle Tampering">Vandalism or Vehicle Tampering</option>
              <option value="Road Hazard / Severe Traffic Blockage">Road Hazard / Severe Traffic Blockage</option>
              <option value="Driver or Passenger Safety Threat">Driver or Passenger Safety Threat</option>
            </select>
          </div>

          <div>
            <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
              Your Contact Number (for officer callback)
            </label>
            <div className="relative">
              <Phone className="w-4 h-4 text-[#718096] absolute left-3 top-2.5" />
              <input
                type="tel"
                value={callerPhone}
                onChange={(e) => setCallerPhone(e.target.value)}
                placeholder="+91 00000 00000"
                className="w-full text-xs pl-9 pr-3 py-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A] text-[#172B43]"
              />
            </div>
          </div>

          <a
            href="tel:112"
            className="w-full py-3 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-[15px] font-semibold flex items-center justify-center gap-2 transition-colors shadow-sm"
          >
            <Shield className="w-5 h-5 text-white" />
            <span>Call Police (112)</span>
          </a>
          <p className="text-[11px] text-[#718096] text-center">
            Tell the operator the situation and your current location.
          </p>
        </form>
      </div>
    </div>
  );
};
