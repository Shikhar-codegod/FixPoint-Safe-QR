import React, { useState } from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import { Shield, MapPin, Phone, CheckCircle2, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const PublicPoliceModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { vehicle, callPoliceAction } = useEmergency();
  const [callerPhone, setCallerPhone] = useState('');
  const [reason, setReason] = useState('Traffic Accident / Highway Collision');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmedId, setConfirmedId] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleCall = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      const id = callPoliceAction(
        reason,
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
            <div className="w-9 h-9 rounded-[8px] bg-[#203D60] flex items-center justify-center shrink-0 border border-slate-600">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-[17px] font-semibold text-white">
                Call Police (Highway Patrol)
              </h3>
              <p className="text-xs text-slate-300">
                Plate: {vehicle.licensePlate} • Safe-QR Emergency
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
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div>
              <h4 className="text-[18px] font-semibold text-[#172B43]">
                Police Unit Dispatched
              </h4>
              <p className="text-xs text-[#718096] mt-1">
                Highway Patrol CAD Incident #{confirmedId} created.
              </p>
            </div>

            <div className="bg-[#F5F7FA] p-3.5 rounded-[10px] border border-[#E2E8F0] text-left text-xs space-y-1.5">
              <div className="flex justify-between text-[#172B43]">
                <span className="text-[#718096]">Officer Assigned:</span>
                <span className="font-semibold text-[#142B4A]">Officer J. Kowalski (PD-394)</span>
              </div>
              <div className="flex justify-between text-[#172B43]">
                <span className="text-[#718096]">Estimated Arrival:</span>
                <span className="font-semibold text-[#D99A27]">5–6 minutes</span>
              </div>
              <div className="flex justify-between text-[#718096]">
                <span className="text-[#718096]">Vehicle Telemetry:</span>
                <span>Plate {vehicle.licensePlate} broadcasted</span>
              </div>
            </div>

            <button
              onClick={() => {
                setConfirmedId(null);
                onClose();
              }}
              className="w-full py-2.5 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-[14px] font-medium transition-colors"
            >
              Close
            </button>
          </div>
        ) : (
          <form onSubmit={handleCall} className="p-5 space-y-4">
            <div className="bg-[#F5F7FA] p-3 rounded-[10px] border border-[#E2E8F0] flex items-start gap-2.5">
              <MapPin className="w-4 h-4 text-[#142B4A] shrink-0 mt-0.5" />
              <div className="text-xs">
                <span className="font-medium text-[#172B43]">
                  Location Telemetry Ready:
                </span>
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
                  placeholder="+1 (555) 000-0000"
                  className="w-full text-xs pl-9 pr-3 py-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A] text-[#172B43]"
                />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-[15px] font-semibold flex items-center justify-center gap-2 transition-colors shadow-xs"
              >
                <Shield className="w-5 h-5 text-white" />
                <span>{isSubmitting ? 'Contacting Police CAD...' : 'Confirm Police Dispatch'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
