import React, { useState } from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import { Ambulance, MapPin, Phone, ShieldCheck, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const PublicAmbulanceModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { vehicle, callAmbulanceAction } = useEmergency();
  const [callerPhone, setCallerPhone] = useState('');
  const [conditionNote, setConditionNote] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmedId, setConfirmedId] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleCall = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      const id = callAmbulanceAction(
        conditionNote || 'Medical emergency requested via Safe-QR code scan.',
        callerPhone || '+1 (555) 911-0000'
      );
      setConfirmedId(id);
      setIsSubmitting(false);
    }, 400);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-[14px] border border-[#E2E8F0] shadow-xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="bg-[#142B4A] text-white p-4.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-[8px] bg-[#D93636] flex items-center justify-center shrink-0">
              <Ambulance className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-[17px] font-semibold text-white">
                Call Ambulance (EMS)
              </h3>
              <p className="text-xs text-slate-300">
                Vehicle: {vehicle.licensePlate} • Safe-QR SOS
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-300 hover:text-white p-1 rounded-md"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {confirmedId ? (
          <div className="p-6 text-center space-y-4">
            <div className="w-14 h-14 rounded-full bg-[#23845B]/15 text-[#23845B] flex items-center justify-center mx-auto">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <div>
              <h4 className="text-[18px] font-semibold text-[#172B43]">
                Ambulance Dispatched
              </h4>
              <p className="text-xs text-[#718096] mt-1">
                Emergency Medical Dispatch incident #{confirmedId} created.
              </p>
            </div>

            <div className="bg-[#F5F7FA] p-3.5 rounded-[10px] border border-[#E2E8F0] text-left text-xs space-y-1.5">
              <div className="flex justify-between text-[#172B43] font-medium">
                <span>Unit Dispatched:</span>
                <span className="font-semibold text-[#142B4A]">Medic Unit 402</span>
              </div>
              <div className="flex justify-between text-[#172B43]">
                <span>Estimated Arrival:</span>
                <span className="font-semibold text-[#23845B]">3–4 minutes</span>
              </div>
              <div className="flex justify-between text-[#718096]">
                <span>Live GPS Link:</span>
                <span>Transmitted to regional EMS CAD</span>
              </div>
            </div>

            <button
              onClick={() => {
                setConfirmedId(null);
                onClose();
              }}
              className="w-full py-2.5 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-[14px] font-medium transition-colors"
            >
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleCall} className="p-5 space-y-4">
            <div className="bg-[#F5F7FA] p-3 rounded-[10px] border border-[#E2E8F0] flex items-start gap-2.5">
              <MapPin className="w-4 h-4 text-[#D93636] shrink-0 mt-0.5" />
              <div className="text-xs">
                <span className="font-medium text-[#172B43]">
                  GPS Coordinates Verified:
                </span>
                <p className="text-[#718096] text-[11px] mt-0.5">
                  Interstate 405 NB / SR-520 interchange (Lat 47.6205, Lng -122.1887)
                </p>
              </div>
            </div>

            <div>
              <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
                Any visible injuries or conditions? (Optional)
              </label>
              <textarea
                value={conditionNote}
                onChange={(e) => setConditionNote(e.target.value)}
                placeholder="e.g. Driver feeling dizzy, passenger trapped, chest pain..."
                rows={2}
                className="w-full text-xs p-2.5 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A] text-[#172B43]"
              />
            </div>

            <div>
              <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
                Your Contact Phone (for 911 callback)
              </label>
              <div className="relative">
                <Phone className="w-4 h-4 text-[#718096] absolute left-3 top-2.5" />
                <input
                  type="tel"
                  value={callerPhone}
                  onChange={(e) => setCallerPhone(e.target.value)}
                  placeholder="+1 (555) 000-0000"
                  className="w-full text-xs pl-9 pr-3 py-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A] text-[#172B43]"
                />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 bg-[#D93636] hover:bg-[#BD2929] text-white rounded-[8px] text-[15px] font-semibold flex items-center justify-center gap-2 transition-colors shadow-xs"
              >
                <Ambulance className="w-5 h-5" />
                <span>{isSubmitting ? 'Dispatching EMS...' : 'Confirm Ambulance Dispatch'}</span>
              </button>
              <p className="text-[11px] text-[#718096] text-center mt-2">
                In immediate life-threatening situations, also dial 911 directly.
              </p>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
