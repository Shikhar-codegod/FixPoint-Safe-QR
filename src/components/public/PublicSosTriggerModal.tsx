import React, { useState } from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import {
  AlertOctagon,
  MapPin,
  Radio,
  Send,
  ShieldAlert,
  X,
  CheckCircle,
} from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onOpenOperations?: () => void;
}

export const PublicSosTriggerModal: React.FC<Props> = ({
  isOpen,
  onClose,
  onOpenOperations,
}) => {
  const {
    vehicle,
    triggerEmergencyAlert,
    setRole,
  } = useEmergency();

  const [description, setDescription] = useState('');
  const [reporterPhone, setReporterPhone] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmedId, setConfirmedId] = useState<string | null>(null);
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | undefined>();
  const [error, setError] = useState<string | null>(null);
  const [isPreview, setIsPreview] = useState(false);

  if (!isOpen) return null;

  const handleTrigger = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPreview) {
      setIsPreview(true);
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const id = await triggerEmergencyAlert(
        description || 'High-urgency collision / distress alert triggered from Safe-QR decal scan.',
        'Public Scanner on Scene',
        reporterPhone || undefined,
        location
      );
      setConfirmedId(id);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to create the alert.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setError('Location is not available on this device. You can still submit the alert.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => setLocation({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      }),
      () => setError('Location permission was denied. You can still submit the alert.')
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/65 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-[14px] border border-[#E2E8F0] shadow-2xl w-full max-w-md overflow-hidden">
        {/* Emergency Red Header */}
        <div className="bg-[#D93636] text-white p-4.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-[8px] bg-white/20 flex items-center justify-center shrink-0">
              <AlertOctagon className="w-6 h-6 text-white animate-pulse" />
            </div>
            <div>
              <h3 className="text-[18px] font-bold text-white tracking-tight">
                Create Emergency Alert
              </h3>
              <p className="text-xs text-white/90">
                FixPoint Safe-QR • Critical SOS Dispatch
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

        {confirmedId ? (
          <div className="p-6 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-[#D93636]/10 text-[#D93636] flex items-center justify-center mx-auto">
              <Radio className="w-8 h-8 animate-pulse" />
            </div>

            <div>
              <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#D93636] text-white mb-1.5">
                SOS LEVEL 1 BROADCAST ACTIVE
              </span>
              <h4 className="text-[20px] font-bold text-[#172B43]">
                Emergency Alert Transmitted
              </h4>
              <p className="text-xs text-[#718096] mt-1">
                Incident ID: <span className="font-mono font-semibold text-[#142B4A]">{confirmedId}</span>
              </p>
            </div>

            {/* Dispatch checklist */}
            <div className="bg-[#F5F7FA] p-3.5 rounded-[10px] border border-[#E2E8F0] text-left text-xs space-y-2">
              <div className="flex items-center gap-2 text-[#23845B] font-medium">
                <CheckCircle className="w-4 h-4 shrink-0" />
                <span>Alert record accepted by FixPoint</span>
              </div>
              <div className="flex items-center gap-2 text-[#23845B] font-medium">
                <CheckCircle className="w-4 h-4 shrink-0" />
                <span>
                  Contact notification processing started where configured
                </span>
              </div>
              <div className="flex items-center gap-2 text-[#23845B] font-medium">
                <CheckCircle className="w-4 h-4 shrink-0" />
                <span>{location ? 'Location included with alert' : 'Location was not provided'}</span>
              </div>
            </div>

            <div className="space-y-2 pt-2">
              <button
                onClick={() => {
                  setConfirmedId(null);
                  onClose();
                  setRole('operations');
                }}
                className="w-full py-2.5 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-[14px] font-semibold flex items-center justify-center gap-2 transition-colors shadow-xs"
              >
                <span>View in Operations Command</span>
              </button>

              <button
                onClick={() => {
                  setConfirmedId(null);
                  onClose();
                }}
                className="w-full py-2 bg-white hover:bg-[#F5F7FA] text-[#172B43] rounded-[8px] text-[13px] font-medium border border-[#E2E8F0] transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleTrigger} className="p-5 space-y-4">
            <div className="bg-[#FFF5F5] border border-[#D93636]/30 p-3 rounded-[10px] text-xs text-[#172B43] flex items-start gap-2.5">
              <ShieldAlert className="w-5 h-5 text-[#D93636] shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-[#D93636]">
                  Immediate Emergency Action:
                </span>
                <p className="text-[12px] text-[#718096] mt-0.5">
                  This submits an emergency alert record for vehicle <strong>{vehicle.licensePlate}</strong> ({vehicle.make} {vehicle.model}). FixPoint does not claim that emergency services were dispatched.
                </p>
              </div>
            </div>

            <div className="bg-[#F5F7FA] p-3 rounded-[10px] border border-[#E2E8F0] flex items-start gap-2.5">
              <MapPin className="w-4 h-4 text-[#D93636] shrink-0 mt-0.5" />
              <div className="text-xs">
                <span className="font-medium text-[#172B43]">
                  Vehicle Incident Location:
                </span>
                <p className="text-[#718096] text-[11px] mt-0.5 font-mono">
                  {location ? `Lat ${location.latitude.toFixed(5)}, Lng ${location.longitude.toFixed(5)}` : 'Location not requested'}
                </p>
              </div>
            </div>

            <button type="button" onClick={requestLocation} className="w-full py-2 border border-[#E2E8F0] rounded-[8px] text-xs text-[#142B4A]">
              {location ? 'Location captured' : 'Request current location (optional)'}
            </button>

            <div>
              <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
                Describe the Emergency
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. Major crash, driver unresponsive, vehicle smoking, medical distress..."
                rows={3}
                className="w-full text-xs p-2.5 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#D93636] text-[#172B43]"
              />
            </div>

            <div>
              <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
                Your Contact Number on Scene
              </label>
              <input
                type="tel"
                value={reporterPhone}
                onChange={(e) => setReporterPhone(e.target.value)}
                placeholder="+1 (555) 000-0000"
                className="w-full text-xs p-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#D93636] text-[#172B43]"
              />
            </div>

            {isPreview && (
              <div className="rounded-[10px] border border-[#D93636]/30 bg-[#FFF5F5] p-3 text-xs text-[#172B43]">
                <strong>Alert preview</strong>
                <p className="mt-1">{description || 'No description provided.'}</p>
                <p className="mt-1 text-[#718096]">
                  {location ? 'Current location will be included.' : 'No location will be included.'}
                </p>
              </div>
            )}

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3.5 bg-[#D93636] hover:bg-[#BD2929] text-white rounded-[8px] text-[15px] font-bold flex items-center justify-center gap-2 transition-colors shadow-sm"
              >
                <AlertOctagon className="w-5 h-5 text-white" />
                <span>{isSubmitting ? 'SUBMITTING ALERT...' : isPreview ? 'CONFIRM & SUBMIT ALERT' : 'PREVIEW ALERT'}</span>
              </button>
              <p className="text-[11px] text-[#718096] text-center mt-2">
                Nothing is submitted until you explicitly confirm the preview.
              </p>
            </div>
            {error && <p role="alert" className="text-xs text-[#D93636]">{error}</p>}
          </form>
        )}
      </div>
    </div>
  );
};
