import React, { useState, useEffect } from 'react';
import QRCode from 'qrcode';
import { useEmergency } from '../../context/EmergencyContext';
import { QrStickerModal } from './QrStickerModal';
import { EmergencyContact } from '../../types';
import {
  Car,
  QrCode,
  PhoneCall,
  HeartPulse,
  Lock,
  History,
  Download,
  Plus,
  Trash2,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  Edit2,
  Check,
  Clock,
  ChevronRight,
  Eye,
} from 'lucide-react';

interface Props {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const CustomerDashboard: React.FC<Props> = ({ activeTab, setActiveTab }) => {
  const {
    vehicle,
    updateVehicle,
    emergencyContacts,
    addEmergencyContact,
    deleteEmergencyContact,
    medicalInfo,
    updateMedicalInfo,
    privacyConsent,
    updatePrivacyConsent,
    incidents,
    setRole,
  } = useEmergency();

  const [qrCodeUrl, setQrCodeUrl] = useState<string>('');
  const [showDecalModal, setShowDecalModal] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState(false);
  const [vehicleForm, setVehicleForm] = useState(vehicle);

  // New Contact form
  const [isAddingContact, setIsAddingContact] = useState(false);
  const [newContact, setNewContact] = useState<Omit<EmergencyContact, 'id'>>({
    name: '',
    relationship: 'Family Member',
    phone: '',
    priority: 2,
    notifyOnSos: true,
    notifyOnRoutine: false,
  });

  // Medical form local state
  const [medForm, setMedForm] = useState(medicalInfo);
  const [isEditingMed, setIsEditingMed] = useState(false);

  // Generate QR code for this vehicle
  useEffect(() => {
    const payload = JSON.stringify({
      system: 'FixPoint Drive Safe-QR',
      vehicleId: vehicle.id,
      plate: vehicle.licensePlate,
    });
    QRCode.toDataURL(payload, {
      width: 200,
      margin: 1,
      color: { dark: '#142B4A', light: '#FFFFFF' },
    }).then(setQrCodeUrl);
  }, [vehicle]);

  const handleSaveVehicle = (e: React.FormEvent) => {
    e.preventDefault();
    updateVehicle(vehicleForm);
    setEditingVehicle(false);
  };

  const handleSaveMedical = (e: React.FormEvent) => {
    e.preventDefault();
    updateMedicalInfo(medForm);
    setIsEditingMed(false);
  };

  const handleAddContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContact.name || !newContact.phone) return;
    addEmergencyContact(newContact);
    setNewContact({
      name: '',
      relationship: 'Family Member',
      phone: '',
      priority: 2,
      notifyOnSos: true,
      notifyOnRoutine: false,
    });
    setIsAddingContact(false);
  };

  return (
    <div className="space-y-6">
      {/* Top Page Heading & Supporting description */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-[26px] sm:text-[28px] font-semibold text-[#172B43] tracking-tight">
            Vehicle & Safe-QR Overview
          </h1>
          <p className="text-[14px] text-[#718096] mt-1">
            Manage your automotive emergency profile, Safe-QR decals, contacts, and telemetry consents.
          </p>
        </div>

        {/* Quick action: Test Public Scan */}
        <button
          onClick={() => setRole('public-qr')}
          className="flex items-center gap-2 px-3.5 py-2 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-[13px] font-medium transition-colors shadow-xs shrink-0"
        >
          <Eye className="w-4 h-4" />
          <span>Test Public Scanner View</span>
        </button>
      </div>

      {/* Main Grid: Overview & Safe-QR Card */}
      {(activeTab === 'overview' || activeTab === 'all') && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Prominent Safe-QR Card (Section 8 requirement) */}
          <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-6 shadow-xs flex flex-col items-center text-center justify-between">
            <div className="w-full flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
              <span className="text-[12px] font-semibold tracking-wider text-[#718096] uppercase">
                Active Safe-QR Decal
              </span>
              <span className="flex items-center gap-1 text-[11px] font-semibold text-[#23845B] bg-[#23845B]/10 px-2 py-0.5 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-[#23845B]"></span>
                Live
              </span>
            </div>

            <div className="my-5 p-3 bg-[#F5F7FA] rounded-[10px] border border-[#E2E8F0] shadow-2xs">
              {qrCodeUrl ? (
                <img
                  src={qrCodeUrl}
                  alt="Vehicle Safe-QR"
                  className="w-44 h-44 object-contain rounded"
                />
              ) : (
                <div className="w-44 h-44 bg-slate-100 animate-pulse rounded" />
              )}
            </div>

            <div className="w-full space-y-2">
              <div className="font-mono text-sm font-bold text-[#142B4A]">
                {vehicle.licensePlate}
              </div>
              <div className="text-xs text-[#718096]">
                Safe-QR ID: <span className="font-mono font-medium">{vehicle.safeQrCode}</span>
              </div>
              <div className="text-[11px] text-[#718096]">
                Lifetime Scans: <strong>{vehicle.qrScanCount}</strong> • Last: {vehicle.lastScannedAt ? new Date(vehicle.lastScannedAt).toLocaleDateString() : 'Never'}
              </div>
            </div>

            <div className="w-full pt-4 mt-2 border-t border-[#E2E8F0] flex gap-2">
              <button
                onClick={() => setShowDecalModal(true)}
                className="w-full py-2 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-[13px] font-medium flex items-center justify-center gap-2 transition-colors shadow-xs"
              >
                <Download className="w-4 h-4" />
                <span>Download Print Decals</span>
              </button>
            </div>
          </div>

          {/* Vehicle Profile Summary Card */}
          <div className="lg:col-span-2 bg-white rounded-[12px] border border-[#E2E8F0] p-6 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
              <div className="flex items-center gap-2.5">
                <Car className="w-5 h-5 text-[#142B4A]" />
                <h2 className="text-[17px] font-semibold text-[#172B43]">
                  Vehicle Information
                </h2>
              </div>
              <button
                onClick={() => {
                  setVehicleForm(vehicle);
                  setEditingVehicle(!editingVehicle);
                }}
                className="text-xs font-medium text-[#142B4A] hover:text-[#203D60] flex items-center gap-1"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>{editingVehicle ? 'Cancel' : 'Edit Specs'}</span>
              </button>
            </div>

            {editingVehicle ? (
              <form onSubmit={handleSaveVehicle} className="py-4 space-y-3.5">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[12px] font-medium text-[#718096] mb-1">Make</label>
                    <input
                      type="text"
                      value={vehicleForm.make}
                      onChange={(e) => setVehicleForm({ ...vehicleForm, make: e.target.value })}
                      className="w-full text-xs p-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A]"
                    />
                  </div>
                  <div>
                    <label className="block text-[12px] font-medium text-[#718096] mb-1">Model</label>
                    <input
                      type="text"
                      value={vehicleForm.model}
                      onChange={(e) => setVehicleForm({ ...vehicleForm, model: e.target.value })}
                      className="w-full text-xs p-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A]"
                    />
                  </div>
                  <div>
                    <label className="block text-[12px] font-medium text-[#718096] mb-1">Year</label>
                    <input
                      type="number"
                      value={vehicleForm.year}
                      onChange={(e) => setVehicleForm({ ...vehicleForm, year: Number(e.target.value) })}
                      className="w-full text-xs p-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A]"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[12px] font-medium text-[#718096] mb-1">Plate Number</label>
                    <input
                      type="text"
                      value={vehicleForm.licensePlate}
                      onChange={(e) => setVehicleForm({ ...vehicleForm, licensePlate: e.target.value })}
                      className="w-full text-xs p-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A]"
                    />
                  </div>
                  <div>
                    <label className="block text-[12px] font-medium text-[#718096] mb-1">Color</label>
                    <input
                      type="text"
                      value={vehicleForm.color}
                      onChange={(e) => setVehicleForm({ ...vehicleForm, color: e.target.value })}
                      className="w-full text-xs p-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A]"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[12px] font-medium text-[#718096] mb-1">Insurance Provider</label>
                    <input
                      type="text"
                      value={vehicleForm.insuranceProvider}
                      onChange={(e) => setVehicleForm({ ...vehicleForm, insuranceProvider: e.target.value })}
                      className="w-full text-xs p-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A]"
                    />
                  </div>
                  <div>
                    <label className="block text-[12px] font-medium text-[#718096] mb-1">Policy Number</label>
                    <input
                      type="text"
                      value={vehicleForm.policyNumber}
                      onChange={(e) => setVehicleForm({ ...vehicleForm, policyNumber: e.target.value })}
                      className="w-full text-xs p-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A]"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setEditingVehicle(false)}
                    className="px-3 py-1.5 rounded-[8px] border border-[#E2E8F0] text-xs font-medium text-[#172B43]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 bg-[#142B4A] text-white rounded-[8px] text-xs font-medium"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            ) : (
              <div className="py-4 grid grid-cols-2 sm:grid-cols-3 gap-y-4 gap-x-6 text-xs">
                <div>
                  <span className="text-[#718096] text-[12px] block">Make & Model</span>
                  <span className="font-semibold text-[#172B43] text-sm mt-0.5 block">
                    {vehicle.year} {vehicle.make} {vehicle.model}
                  </span>
                </div>
                <div>
                  <span className="text-[#718096] text-[12px] block">License Plate</span>
                  <span className="font-mono font-bold text-[#142B4A] text-sm mt-0.5 block">
                    {vehicle.licensePlate}
                  </span>
                </div>
                <div>
                  <span className="text-[#718096] text-[12px] block">Color Finish</span>
                  <span className="font-medium text-[#172B43] text-sm mt-0.5 block">
                    {vehicle.color}
                  </span>
                </div>
                <div>
                  <span className="text-[#718096] text-[12px] block">VIN</span>
                  <span className="font-mono text-[#172B43] text-xs mt-0.5 block truncate">
                    {vehicle.vin}
                  </span>
                </div>
                <div>
                  <span className="text-[#718096] text-[12px] block">Registered Owner</span>
                  <span className="font-medium text-[#172B43] text-sm mt-0.5 block">
                    {vehicle.ownerName}
                  </span>
                </div>
                <div>
                  <span className="text-[#718096] text-[12px] block">Emergency Relay Phone</span>
                  <span className="font-medium text-[#172B43] text-sm mt-0.5 block">
                    {vehicle.ownerPhone}
                  </span>
                </div>
                <div>
                  <span className="text-[#718096] text-[12px] block">Insurance Provider</span>
                  <span className="font-medium text-[#172B43] text-xs mt-0.5 block">
                    {vehicle.insuranceProvider}
                  </span>
                </div>
                <div>
                  <span className="text-[#718096] text-[12px] block">Policy Number</span>
                  <span className="font-mono font-medium text-[#172B43] text-xs mt-0.5 block">
                    {vehicle.policyNumber}
                  </span>
                </div>
                <div>
                  <span className="text-[#718096] text-[12px] block">Safe-QR Registered</span>
                  <span className="font-medium text-[#23845B] text-xs mt-0.5 block flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Verified Active
                  </span>
                </div>
              </div>
            )}

            {/* Quick Status Bar */}
            <div className="bg-[#F5F7FA] p-3 rounded-[10px] border border-[#E2E8F0] flex flex-wrap items-center justify-between text-xs gap-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#23845B]" />
                <span className="text-[#172B43] font-medium">
                  24/7 Roadside & SOS Dispatch Relay Active
                </span>
              </div>
              <span className="text-[#718096] text-[11px]">
                Subscription active until March 2027
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Emergency Contacts Section (Section 8 requirement) */}
      {(activeTab === 'contacts' || activeTab === 'all' || activeTab === 'overview') && (
        <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
            <div className="flex items-center gap-2.5">
              <PhoneCall className="w-5 h-5 text-[#142B4A]" />
              <div>
                <h2 className="text-[17px] font-semibold text-[#172B43]">
                  Emergency Contacts
                </h2>
                <p className="text-xs text-[#718096]">
                  Notified automatically via high-priority SMS upon any SOS activation.
                </p>
              </div>
            </div>

            <button
              onClick={() => setIsAddingContact(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-xs font-medium transition-colors shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Contact</span>
            </button>
          </div>

          {/* Add contact form if active */}
          {isAddingContact && (
            <form onSubmit={handleAddContactSubmit} className="bg-[#F5F7FA] p-4 rounded-[10px] border border-[#E2E8F0] space-y-3">
              <div className="text-xs font-semibold text-[#142B4A]">New Emergency Contact</div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
                <div>
                  <label className="block text-[11px] font-medium text-[#718096] mb-1">Full Name</label>
                  <input
                    required
                    type="text"
                    value={newContact.name}
                    onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                    placeholder="e.g. Maria Vance"
                    className="w-full p-2 bg-white rounded-[8px] border border-[#E2E8F0]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-[#718096] mb-1">Relationship</label>
                  <input
                    required
                    type="text"
                    value={newContact.relationship}
                    onChange={(e) => setNewContact({ ...newContact, relationship: e.target.value })}
                    placeholder="Spouse / Parent / Sibling"
                    className="w-full p-2 bg-white rounded-[8px] border border-[#E2E8F0]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-[#718096] mb-1">Mobile Phone</label>
                  <input
                    required
                    type="tel"
                    value={newContact.phone}
                    onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })}
                    placeholder="+1 (555) 000-0000"
                    className="w-full p-2 bg-white rounded-[8px] border border-[#E2E8F0]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-[#718096] mb-1">Priority Rank</label>
                  <select
                    value={newContact.priority}
                    onChange={(e) => setNewContact({ ...newContact, priority: Number(e.target.value) as 1 | 2 | 3 })}
                    className="w-full p-2 bg-white rounded-[8px] border border-[#E2E8F0]"
                  >
                    <option value={1}>Priority 1 (Primary)</option>
                    <option value={2}>Priority 2 (Secondary)</option>
                    <option value={3}>Priority 3 (Tertiary)</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <label className="flex items-center gap-2 text-xs text-[#172B43]">
                  <input
                    type="checkbox"
                    checked={newContact.notifyOnSos}
                    onChange={(e) => setNewContact({ ...newContact, notifyOnSos: e.target.checked })}
                    className="rounded text-[#142B4A]"
                  />
                  <span>Dispatch automated SMS immediately on critical SOS</span>
                </label>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setIsAddingContact(false)}
                    className="px-3 py-1.5 text-xs text-[#718096] hover:text-[#172B43]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 bg-[#142B4A] text-white rounded-[8px] text-xs font-medium"
                  >
                    Save Contact
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* Clean Contact Table (Section 4 & 8 requirement) */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#E2E8F0] text-[#718096] uppercase text-[11px] tracking-wider bg-[#F5F7FA]/60">
                  <th className="py-2.5 px-3 font-semibold">Priority</th>
                  <th className="py-2.5 px-3 font-semibold">Contact Name</th>
                  <th className="py-2.5 px-3 font-semibold">Relationship</th>
                  <th className="py-2.5 px-3 font-semibold">Phone Number</th>
                  <th className="py-2.5 px-3 font-semibold">SMS Alert Mode</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {emergencyContacts.map((contact) => (
                  <tr key={contact.id} className="hover:bg-[#F5F7FA]/50 transition-colors">
                    <td className="py-3 px-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-[4px] text-[11px] font-bold ${
                          contact.priority === 1
                            ? 'bg-[#142B4A] text-white'
                            : 'bg-[#E2E8F0] text-[#172B43]'
                        }`}
                      >
                        Priority {contact.priority}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-medium text-[#172B43] text-sm">
                      {contact.name}
                    </td>
                    <td className="py-3 px-3 text-[#718096]">
                      {contact.relationship}
                    </td>
                    <td className="py-3 px-3 font-mono font-medium text-[#172B43]">
                      {contact.phone}
                    </td>
                    <td className="py-3 px-3">
                      {contact.notifyOnSos ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-[#23845B]">
                          <Check className="w-3.5 h-3.5" />
                          Auto-SMS Enabled
                        </span>
                      ) : (
                        <span className="text-[11px] text-[#718096]">Manual only</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => deleteEmergencyContact(contact.id)}
                        disabled={emergencyContacts.length <= 1}
                        title={emergencyContacts.length <= 1 ? "At least one emergency contact is required" : "Remove contact"}
                        className="p-1 text-[#718096] hover:text-[#D93636] disabled:opacity-30 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Medical Information Forms (Section 8 requirement) */}
      {(activeTab === 'medical' || activeTab === 'all' || activeTab === 'overview') && (
        <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
            <div className="flex items-center gap-2.5">
              <HeartPulse className="w-5 h-5 text-[#D93636]" />
              <div>
                <h2 className="text-[17px] font-semibold text-[#172B43]">
                  Emergency Medical Information
                </h2>
                <p className="text-xs text-[#718096]">
                  Critical medical data accessible only to verified responders or per your privacy consent.
                </p>
              </div>
            </div>

            <button
              onClick={() => {
                setMedForm(medicalInfo);
                setIsEditingMed(!isEditingMed);
              }}
              className="text-xs font-medium text-[#142B4A] hover:text-[#203D60] flex items-center gap-1"
            >
              <Edit2 className="w-3.5 h-3.5" />
              <span>{isEditingMed ? 'Cancel' : 'Edit Medical Profile'}</span>
            </button>
          </div>

          {isEditingMed ? (
            <form onSubmit={handleSaveMedical} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[12px] font-medium text-[#172B43] mb-1">Blood Type</label>
                  <select
                    value={medForm.bloodType}
                    onChange={(e) => setMedForm({ ...medForm, bloodType: e.target.value })}
                    className="w-full p-2.5 bg-white rounded-[8px] border border-[#E2E8F0]"
                  >
                    <option value="O-Positive (O+)">O-Positive (O+)</option>
                    <option value="O-Negative (O-)">O-Negative (O-)</option>
                    <option value="A-Positive (A+)">A-Positive (A+)</option>
                    <option value="A-Negative (A-)">A-Negative (A-)</option>
                    <option value="B-Positive (B+)">B-Positive (B+)</option>
                    <option value="B-Negative (B-)">B-Negative (B-)</option>
                    <option value="AB-Positive (AB+)">AB-Positive (AB+)</option>
                    <option value="AB-Negative (AB-)">AB-Negative (AB-)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[12px] font-medium text-[#172B43] mb-1">
                    Known Allergies (comma separated)
                  </label>
                  <input
                    type="text"
                    value={medForm.allergies.join(', ')}
                    onChange={(e) =>
                      setMedForm({
                        ...medForm,
                        allergies: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                      })
                    }
                    placeholder="e.g. Penicillin, Latex, Peanuts"
                    className="w-full p-2.5 rounded-[8px] border border-[#E2E8F0]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[12px] font-medium text-[#172B43] mb-1">
                    Pre-Existing Medical Conditions
                  </label>
                  <input
                    type="text"
                    value={medForm.medicalConditions.join(', ')}
                    onChange={(e) =>
                      setMedForm({
                        ...medForm,
                        medicalConditions: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                      })
                    }
                    placeholder="e.g. Asthma, Diabetes, Hypertension"
                    className="w-full p-2.5 rounded-[8px] border border-[#E2E8F0]"
                  />
                </div>

                <div>
                  <label className="block text-[12px] font-medium text-[#172B43] mb-1">
                    Current Medications
                  </label>
                  <input
                    type="text"
                    value={medForm.medications.join(', ')}
                    onChange={(e) =>
                      setMedForm({
                        ...medForm,
                        medications: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                      })
                    }
                    placeholder="e.g. Albuterol, Insulin, Lisinopril"
                    className="w-full p-2.5 rounded-[8px] border border-[#E2E8F0]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[12px] font-medium text-[#172B43] mb-1">Primary Physician</label>
                  <input
                    type="text"
                    value={medForm.physicianName}
                    onChange={(e) => setMedForm({ ...medForm, physicianName: e.target.value })}
                    className="w-full p-2 rounded-[8px] border border-[#E2E8F0]"
                  />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-[#172B43] mb-1">Physician Phone</label>
                  <input
                    type="text"
                    value={medForm.physicianPhone}
                    onChange={(e) => setMedForm({ ...medForm, physicianPhone: e.target.value })}
                    className="w-full p-2 rounded-[8px] border border-[#E2E8F0]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[12px] font-medium text-[#172B43] mb-1">
                  Additional Medical Instructions
                </label>
                <textarea
                  value={medForm.additionalNotes}
                  onChange={(e) => setMedForm({ ...medForm, additionalNotes: e.target.value })}
                  rows={2}
                  className="w-full p-2 rounded-[8px] border border-[#E2E8F0]"
                />
              </div>

              <div className="flex gap-4">
                <label className="flex items-center gap-2 text-xs text-[#172B43]">
                  <input
                    type="checkbox"
                    checked={medForm.organDonor}
                    onChange={(e) => setMedForm({ ...medForm, organDonor: e.target.checked })}
                    className="rounded text-[#142B4A]"
                  />
                  <span>Registered Organ Donor</span>
                </label>

                <label className="flex items-center gap-2 text-xs text-[#172B43]">
                  <input
                    type="checkbox"
                    checked={medForm.dnrStatus}
                    onChange={(e) => setMedForm({ ...medForm, dnrStatus: e.target.checked })}
                    className="rounded text-[#142B4A]"
                  />
                  <span>Do Not Resuscitate (DNR) Directives on file</span>
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsEditingMed(false)}
                  className="px-3 py-1.5 rounded-[8px] border border-[#E2E8F0] text-xs font-medium text-[#172B43]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-[#142B4A] text-white rounded-[8px] text-xs font-medium"
                >
                  Save Medical Details
                </button>
              </div>
            </form>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-3.5 bg-[#F5F7FA] rounded-[10px] border border-[#E2E8F0]">
                <span className="text-[11px] font-semibold text-[#718096] uppercase tracking-wider block">
                  Blood Group
                </span>
                <span className="text-xl font-bold text-[#D93636] mt-1 block">
                  {medicalInfo.bloodType}
                </span>
                <span className="text-[11px] text-[#718096] mt-0.5 block">
                  {medicalInfo.organDonor ? 'Registered Organ Donor' : 'Standard Donor Status'}
                </span>
              </div>

              <div className="p-3.5 bg-[#F5F7FA] rounded-[10px] border border-[#E2E8F0]">
                <span className="text-[11px] font-semibold text-[#718096] uppercase tracking-wider block">
                  Severe Allergies
                </span>
                <div className="mt-1.5 space-y-1">
                  {medicalInfo.allergies.map((allg, idx) => (
                    <span
                      key={idx}
                      className="inline-block mr-1.5 mb-1 px-2 py-0.5 rounded-[4px] bg-[#FFF5F5] border border-[#D93636]/30 text-[#D93636] font-medium text-[11px]"
                    >
                      {allg}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-3.5 bg-[#F5F7FA] rounded-[10px] border border-[#E2E8F0]">
                <span className="text-[11px] font-semibold text-[#718096] uppercase tracking-wider block">
                  Active Conditions
                </span>
                <div className="mt-1.5 space-y-1">
                  {medicalInfo.medicalConditions.map((cond, idx) => (
                    <span
                      key={idx}
                      className="inline-block mr-1.5 mb-1 px-2 py-0.5 rounded-[4px] bg-white border border-[#E2E8F0] text-[#172B43] font-medium text-[11px]"
                    >
                      {cond}
                    </span>
                  ))}
                </div>
              </div>

              <div className="md:col-span-3 p-3.5 bg-[#F8FAFC] rounded-[10px] border border-[#E2E8F0] flex flex-wrap items-center justify-between gap-3">
                <div className="text-xs">
                  <span className="font-semibold text-[#172B43]">Medications & Notes: </span>
                  <span className="text-[#718096]">
                    {medicalInfo.medications.join(', ')} • {medicalInfo.additionalNotes}
                  </span>
                </div>
                <div className="text-xs text-[#718096]">
                  Physician: <strong className="text-[#172B43]">{medicalInfo.physicianName}</strong> ({medicalInfo.physicianPhone})
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Privacy and Consent Controls (Section 8 requirement) */}
      {(activeTab === 'privacy' || activeTab === 'all' || activeTab === 'overview') && (
        <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-[#E2E8F0]">
            <Lock className="w-5 h-5 text-[#142B4A]" />
            <div>
              <h2 className="text-[17px] font-semibold text-[#172B43]">
                Privacy & Emergency Consent Controls
              </h2>
              <p className="text-xs text-[#718096]">
                Granular consent switches dictate exactly what information is revealed during public scans vs verified first responder CAD access.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="flex items-start justify-between p-3.5 rounded-[10px] border border-[#E2E8F0] bg-[#F5F7FA]">
              <div className="pr-3">
                <span className="font-semibold text-[#172B43] block">
                  Disclose Blood Type on Public SOS Scan
                </span>
                <span className="text-[11px] text-[#718096] block mt-0.5">
                  Allows immediate transfusion prep by EMTs before patient ID is manually searched.
                </span>
              </div>
              <input
                type="checkbox"
                checked={privacyConsent.shareBloodTypeOnSos}
                onChange={(e) => updatePrivacyConsent({ shareBloodTypeOnSos: e.target.checked })}
                className="mt-1 h-4 w-4 rounded text-[#142B4A]"
              />
            </div>

            <div className="flex items-start justify-between p-3.5 rounded-[10px] border border-[#E2E8F0] bg-[#F5F7FA]">
              <div className="pr-3">
                <span className="font-semibold text-[#172B43] block">
                  Broadcast Critical Allergies on SOS Scan
                </span>
                <span className="text-[11px] text-[#718096] block mt-0.5">
                  Protects against accidental fatal administration of contraindicated antibiotics.
                </span>
              </div>
              <input
                type="checkbox"
                checked={privacyConsent.shareAllergiesOnSos}
                onChange={(e) => updatePrivacyConsent({ shareAllergiesOnSos: e.target.checked })}
                className="mt-1 h-4 w-4 rounded text-[#142B4A]"
              />
            </div>

            <div className="flex items-start justify-between p-3.5 rounded-[10px] border border-[#E2E8F0] bg-[#F5F7FA]">
              <div className="pr-3">
                <span className="font-semibold text-[#172B43] block">
                  Full Medical History to Verified Responders
                </span>
                <span className="text-[11px] text-[#718096] block mt-0.5">
                  Requires 2FA officer badge credential check before detailed EHR decryption.
                </span>
              </div>
              <input
                type="checkbox"
                checked={privacyConsent.shareFullMedicalToVerifiedResponder}
                onChange={(e) => updatePrivacyConsent({ shareFullMedicalToVerifiedResponder: e.target.checked })}
                className="mt-1 h-4 w-4 rounded text-[#142B4A]"
              />
            </div>

            <div className="flex items-start justify-between p-3.5 rounded-[10px] border border-[#E2E8F0] bg-[#F5F7FA]">
              <div className="pr-3">
                <span className="font-semibold text-[#172B43] block">
                  Auto-Notify Emergency Contacts via SMS
                </span>
                <span className="text-[11px] text-[#718096] block mt-0.5">
                  Sends live vehicle coordinates & event notice immediately to priority contacts.
                </span>
              </div>
              <input
                type="checkbox"
                checked={privacyConsent.autoNotifyContactsSms}
                onChange={(e) => updatePrivacyConsent({ autoNotifyContactsSms: e.target.checked })}
                className="mt-1 h-4 w-4 rounded text-[#142B4A]"
              />
            </div>
          </div>
        </div>
      )}

      {/* Clear Alert History Section (Section 8 requirement) */}
      {(activeTab === 'history' || activeTab === 'all' || activeTab === 'overview') && (
        <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
            <div className="flex items-center gap-2.5">
              <History className="w-5 h-5 text-[#142B4A]" />
              <div>
                <h2 className="text-[17px] font-semibold text-[#172B43]">
                  Vehicle Safe-QR Incident History
                </h2>
                <p className="text-xs text-[#718096]">
                  Past scans, automated SOS alerts, and routine owner notices.
                </p>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#E2E8F0] text-[#718096] uppercase text-[11px] tracking-wider bg-[#F5F7FA]/60">
                  <th className="py-2.5 px-3 font-semibold">Incident ID</th>
                  <th className="py-2.5 px-3 font-semibold">Type</th>
                  <th className="py-2.5 px-3 font-semibold">Status</th>
                  <th className="py-2.5 px-3 font-semibold">Date & Time</th>
                  <th className="py-2.5 px-3 font-semibold">Location</th>
                  <th className="py-2.5 px-3 font-semibold">Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {incidents.map((inc) => {
                  let badge = (
                    <span className="px-2 py-0.5 rounded-[4px] text-[11px] font-bold bg-[#D93636] text-white">
                      Critical SOS
                    </span>
                  );
                  if (inc.type === 'routine_report') {
                    badge = (
                      <span className="px-2 py-0.5 rounded-[4px] text-[11px] font-medium bg-[#142B4A]/10 text-[#142B4A]">
                        Routine Report
                      </span>
                    );
                  } else if (inc.type === 'ambulance') {
                    badge = (
                      <span className="px-2 py-0.5 rounded-[4px] text-[11px] font-medium bg-[#D93636]/15 text-[#D93636]">
                        Ambulance (EMS)
                      </span>
                    );
                  } else if (inc.type === 'police') {
                    badge = (
                      <span className="px-2 py-0.5 rounded-[4px] text-[11px] font-medium bg-[#203D60]/15 text-[#203D60]">
                        Police Call
                      </span>
                    );
                  }

                  return (
                    <tr key={inc.id} className="hover:bg-[#F5F7FA]/50 transition-colors">
                      <td className="py-3 px-3 font-mono font-semibold text-[#142B4A]">
                        {inc.id}
                      </td>
                      <td className="py-3 px-3">{badge}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            inc.status === 'resolved'
                              ? 'bg-[#23845B]/10 text-[#23845B]'
                              : inc.status === 'active_sos'
                              ? 'bg-[#D93636] text-white'
                              : 'bg-[#D99A27]/15 text-[#D99A27]'
                          }`}
                        >
                          {inc.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-[#718096]">
                        {new Date(inc.createdAt).toLocaleString()}
                      </td>
                      <td className="py-3 px-3 text-[#172B43] max-w-xs truncate">
                        {inc.location.address}
                      </td>
                      <td className="py-3 px-3 text-[#718096] max-w-xs truncate">
                        {inc.description}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Decal Print Modal */}
      <QrStickerModal
        isOpen={showDecalModal}
        onClose={() => setShowDecalModal(false)}
      />
    </div>
  );
};
