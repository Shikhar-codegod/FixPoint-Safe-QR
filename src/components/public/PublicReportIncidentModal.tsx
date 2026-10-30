import React, { useState } from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import { RoutineIncidentCategory } from '../../types';
import { AlertTriangle, CheckCircle2, FileText, Lock, Send, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const PublicReportIncidentModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { vehicle, reportRoutineIncident } = useEmergency();
  const [category, setCategory] = useState<RoutineIncidentCategory>('parking_bump');
  const [description, setDescription] = useState('');
  const [reporterName, setReporterName] = useState('');
  const [reporterPhone, setReporterPhone] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmedId, setConfirmedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const id = await reportRoutineIncident(
        category,
        description,
        reporterName || undefined,
        reporterPhone || undefined
      );
      setConfirmedId(id);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to submit the report.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-[14px] border border-[#E2E8F0] shadow-xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="bg-[#142B4A] text-white p-4.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-[8px] bg-[#203D60] flex items-center justify-center shrink-0 border border-slate-600">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-[17px] font-semibold text-white">
                Report an Incident
              </h3>
              <p className="text-xs text-slate-300">
                Non-emergency vehicle notice • Safe-QR
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
                Report accepted
              </h4>
              <p className="text-xs text-[#718096] mt-1">
                Report #{confirmedId} was saved for Safe-QR {vehicle.licensePlate}.
              </p>
            </div>

            <div className="bg-[#F5F7FA] p-3.5 rounded-[10px] border border-[#E2E8F0] text-xs text-[#718096] text-left space-y-1">
              <div className="flex items-center gap-1.5 text-[#23845B] font-medium">
                <Lock className="w-3.5 h-3.5" />
                <span>Privacy-Preserving Relay</span>
              </div>
              <p>
                The report is now available to the authorized operations workflow. No emergency contacts were notified.
              </p>
            </div>

            <button
              onClick={() => {
                setConfirmedId(null);
                setDescription('');
                onClose();
              }}
              className="w-full py-2.5 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-[14px] font-medium transition-colors"
            >
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            <div>
              <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
                Incident Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as RoutineIncidentCategory)}
                className="w-full text-xs p-2.5 rounded-[8px] border border-[#E2E8F0] bg-white focus:outline-none focus:border-[#142B4A] text-[#172B43]"
              >
                <option value="parking_bump">Parking Bump / Scrape / Minor Damage</option>
                <option value="vehicle_obstruction">Vehicle Blocking Driveway / Roadway</option>
                <option value="flat_tire_or_breakdown">Flat Tire / Leak / Visible Hazard</option>
                <option value="lights_left_on">Headlights or Dome Lights Left On</option>
                <option value="other">Other Message for Vehicle Owner</option>
              </select>
            </div>

            <div>
              <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
                Details for the Owner <span className="text-[#D93636]">*</span>
              </label>
              <textarea
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="Describe what occurred, exact location details, or parking bay number..."
                className="w-full text-xs p-2.5 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A] text-[#172B43]"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
                  Your Name (Optional)
                </label>
                <input
                  type="text"
                  value={reporterName}
                  onChange={(e) => setReporterName(e.target.value)}
                  placeholder="e.g. Fellow driver"
                  className="w-full text-xs p-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A] text-[#172B43]"
                />
              </div>

              <div>
                <label className="block text-[13px] font-medium text-[#172B43] mb-1.5">
                  Phone (Optional)
                </label>
                <input
                  type="tel"
                  value={reporterPhone}
                  onChange={(e) => setReporterPhone(e.target.value)}
                  placeholder="+1 (555) 000-0000"
                  className="w-full text-xs p-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A] text-[#172B43]"
                />
              </div>
            </div>

            <div className="bg-[#F5F7FA] p-2.5 rounded-[8px] border border-[#E2E8F0] flex items-center gap-2 text-[11px] text-[#718096]">
              <Lock className="w-3.5 h-3.5 text-[#142B4A] shrink-0" />
              <span>Safe-QR relay preserves your privacy and the driver's private contact.</span>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting || !description.trim()}
                className="w-full py-3 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-[15px] font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-50 shadow-xs"
              >
                <Send className="w-4 h-4" />
                <span>{isSubmitting ? 'Sending Notice...' : 'Send Incident Notice'}</span>
              </button>
            </div>
            {error && <p role="alert" className="text-xs text-[#D93636]">{error}</p>}
          </form>
        )}
      </div>
    </div>
  );
};
