import React, { useState } from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import { Ambulance, MapPin, Phone, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const PublicAmbulanceModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { vehicle } = useEmergency();
  const [callerPhone, setCallerPhone] = useState('');
  const [conditionNote, setConditionNote] = useState('');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-[14px] border border-[#E2E8F0] shadow-xl w-full max-w-md overflow-hidden">
        <div className="bg-[#142B4A] text-white p-4.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-[8px] bg-[#D93636] flex items-center justify-center shrink-0">
              <Ambulance className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-[17px] font-semibold text-white">Call Ambulance (EMS)</h3>
              <p className="text-xs text-slate-300">
                Vehicle: {vehicle.licensePlate} • Safe-QR SOS
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-300 hover:text-white p-1 rounded-md">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form className="p-5 space-y-4">
          <div className="bg-[#FFF5F5] border border-[#D93636]/30 p-3 rounded-[10px] text-xs text-[#172B43]">
            <span className="font-semibold text-[#D93636]">Manual emergency call</span>
            <p className="text-[12px] text-[#718096] mt-0.5">
              FixPoint will open your phone dialer. It does not place, verify, or claim an EMS dispatch.
            </p>
          </div>

          <div className="bg-[#F5F7FA] p-3 rounded-[10px] border border-[#E2E8F0] flex items-start gap-2.5">
            <MapPin className="w-4 h-4 text-[#D93636] shrink-0 mt-0.5" />
            <div className="text-xs">
              <span className="font-medium text-[#172B43]">Location available to you:</span>
              <p className="text-[#718096] text-[11px] mt-0.5">
                Interstate 405 NB / SR-520 interchange (Lat 47.6205, Lng -122.1887)
              </p>
            </div>
          </div>

          <div>
            <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
              Visible injuries or conditions (Optional)
            </label>
            <textarea
              value={conditionNote}
              onChange={(e) => setConditionNote(e.target.value)}
              placeholder="Tell EMS what you observe after the call connects."
              rows={2}
              className="w-full text-xs p-2.5 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A] text-[#172B43]"
            />
          </div>

          <div>
            <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
              Your Contact Phone (for EMS callback)
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
            href="tel:108"
            className="w-full py-3 bg-[#D93636] hover:bg-[#BD2929] text-white rounded-[8px] text-[15px] font-semibold flex items-center justify-center gap-2 transition-colors shadow-sm"
          >
            <Ambulance className="w-5 h-5" />
            <span>Call Ambulance (108)</span>
          </a>
          <p className="text-[11px] text-[#718096] text-center">
            Provide the location and condition details when the call connects.
          </p>
        </form>
      </div>
    </div>
  );
};
