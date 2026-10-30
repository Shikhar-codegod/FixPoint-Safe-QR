import React, { useState } from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import { IncidentDetailModal } from './IncidentDetailModal';
import { IncidentAlert, IncidentType } from '../../types';
import {
  Activity,
  AlertOctagon,
  Car,
  CheckCircle2,
  Clock,
  Compass,
  FileText,
  Filter,
  MapPin,
  Navigation,
  Radio,
  Search,
  Shield,
  ShieldAlert,
  Users,
  Eye,
  RefreshCw,
} from 'lucide-react';

interface Props {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const OperationsDashboard: React.FC<Props> = ({ activeTab, setActiveTab }) => {
  const {
    incidents,
    vehicle,
    selectedIncidentId,
    setSelectedIncidentId,
    incidentsLoading,
    incidentsError,
    refreshIncidents,
  } = useEmergency();

  const [filterType, setFilterType] = useState<'all' | 'critical' | 'routine'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [mapZoom, setMapZoom] = useState(1);

  // Filtered incidents
  const filteredIncidents = incidents.filter((inc) => {
    if (filterType === 'critical') {
      if (inc.type !== 'emergency_sos' && inc.type !== 'ambulance') return false;
    } else if (filterType === 'routine') {
      if (inc.type !== 'routine_report') return false;
    }

    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      return (
        inc.id.toLowerCase().includes(q) ||
        inc.vehiclePlate.toLowerCase().includes(q) ||
        inc.description.toLowerCase().includes(q) ||
        inc.location.address.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const activeSosCount = incidents.filter(
    (i) => i.status === 'active_sos' || i.status === 'dispatched' || i.status === 'en_route'
  ).length;

  const resolvedCount = incidents.filter((i) => i.status === 'resolved').length;
  const routineCount = incidents.filter((i) => i.type === 'routine_report').length;
  const primaryIncident = incidents[0];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-[26px] sm:text-[28px] font-semibold text-[#172B43] tracking-tight">
              Operations Command Center
            </h1>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-[#23845B]/15 text-[#23845B] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#23845B] animate-pulse"></span>
              Live CAD Stream
            </span>
          </div>
          <p className="text-[14px] text-[#718096] mt-1">
            Automotive emergency triage, automated Safe-QR sensor alerts, and CAD multi-agency dispatch.
          </p>
        </div>

        {/* Server-backed operations controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => void refreshIncidents()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[8px] bg-[#142B4A] hover:bg-[#203D60] text-white text-xs font-semibold shadow-xs transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${incidentsLoading ? 'animate-spin' : ''}`} />
            <span>Refresh server queue</span>
          </button>
        </div>
      </div>
      {incidentsError && (
        <div role="alert" className="rounded-[8px] border border-[#D93636]/30 bg-[#FFF5F5] px-3 py-2 text-xs text-[#D93636]">
          {incidentsError}
        </div>
      )}

      {/* 5 Compact Metric Cards (Section 7 requirement) */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
        {/* Metric 1: Active Critical Alerts (Emergency Red Emphasis) */}
        <div className="p-4 rounded-[12px] bg-white border border-[#E2E8F0] shadow-xs relative overflow-hidden">
          {activeSosCount > 0 && (
            <div className="absolute top-0 right-0 w-16 h-16 bg-[#D93636]/10 rounded-bl-full pointer-events-none" />
          )}
          <div className="flex items-center justify-between text-[#718096]">
            <span className="text-[12px] font-semibold uppercase tracking-wider">
              Active SOS
            </span>
            <AlertOctagon
              className={`w-4 h-4 ${activeSosCount > 0 ? 'text-[#D93636] animate-pulse' : 'text-[#718096]'}`}
            />
          </div>
          <div className="mt-2 text-2xl font-bold text-[#D93636]">
            {activeSosCount}
          </div>
          <div className="mt-1 text-[11px] text-[#718096]">
            {activeSosCount > 0 ? 'Immediate responder routing' : 'No active emergencies'}
          </div>
        </div>

        {/* Metric 2: Dispatched Responders */}
        <div className="p-4 rounded-[12px] bg-white border border-[#E2E8F0] shadow-xs">
          <div className="flex items-center justify-between text-[#718096]">
            <span className="text-[12px] font-semibold uppercase tracking-wider">
              Dispatched Units
            </span>
            <Users className="w-4 h-4 text-[#142B4A]" />
          </div>
          <div className="mt-2 text-2xl font-bold text-[#142B4A]">
            {incidents.filter((i) => i.status === 'dispatched' || i.status === 'en_route').length}
          </div>
          <div className="mt-1 text-[11px] text-[#23845B] font-medium">
            Server-reported assignments
          </div>
        </div>

        {/* Metric 3: Routine Reports */}
        <div className="p-4 rounded-[12px] bg-white border border-[#E2E8F0] shadow-xs">
          <div className="flex items-center justify-between text-[#718096]">
            <span className="text-[12px] font-semibold uppercase tracking-wider">
              Routine Notices
            </span>
            <FileText className="w-4 h-4 text-[#718096]" />
          </div>
          <div className="mt-2 text-2xl font-bold text-[#172B43]">
            {routineCount}
          </div>
          <div className="mt-1 text-[11px] text-[#718096]">
            Parking, bumps & notices
          </div>
        </div>

        {/* Metric 4: Avg Response Time */}
        <div className="p-4 rounded-[12px] bg-white border border-[#E2E8F0] shadow-xs">
          <div className="flex items-center justify-between text-[#718096]">
            <span className="text-[12px] font-semibold uppercase tracking-wider">
              Avg Response
            </span>
            <Clock className="w-4 h-4 text-[#23845B]" />
          </div>
          <div className="mt-2 text-2xl font-bold text-[#23845B]">
            4.2m
          </div>
          <div className="mt-1 text-[11px] text-[#718096]">
            Safe-QR GPS acceleration
          </div>
        </div>

        {/* Metric 5: Safe-QR Fleet Active */}
        <div className="col-span-2 lg:col-span-1 p-4 rounded-[12px] bg-white border border-[#E2E8F0] shadow-xs">
          <div className="flex items-center justify-between text-[#718096]">
            <span className="text-[12px] font-semibold uppercase tracking-wider">
              Safe-QR Decals
            </span>
            <Shield className="w-4 h-4 text-[#142B4A]" />
          </div>
          <div className="mt-2 text-2xl font-bold text-[#172B43]">
            {incidents.length}
          </div>
          <div className="mt-1 text-[11px] text-[#23845B] font-medium">
            Records in current queue
          </div>
        </div>
      </div>

      {/* Main Content Layout: Split Map/Location Panel + Live Incidents */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Map & Location Radar (Section 7 requirement) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-4 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
              <div className="flex items-center gap-2">
                <Compass className="w-4 h-4 text-[#142B4A]" />
                <h3 className="text-[15px] font-semibold text-[#172B43]">
                  Location & Dispatch Radar
                </h3>
              </div>
              <div className="flex items-center gap-1.5 text-[11px] font-mono text-[#718096]">
                <span className="w-2 h-2 rounded-full bg-[#23845B]"></span>
                GPS Locked
              </div>
            </div>

            {/* Location radar based on the latest server record */}
            <div className="relative mt-3 h-72 w-full bg-[#142B4A] rounded-[10px] overflow-hidden border border-[#203D60] select-none flex items-center justify-center">
              {/* Grid overlay */}
              <div
                className="absolute inset-0 opacity-20"
                style={{
                  backgroundImage:
                    'radial-gradient(circle, #718096 1px, transparent 1px)',
                  backgroundSize: '24px 24px',
                }}
              />

              {/* Concentric distance radar rings */}
              <div className="absolute w-56 h-56 rounded-full border border-white/10" />
              <div className="absolute w-40 h-40 rounded-full border border-white/15" />
              <div className="absolute w-24 h-24 rounded-full border border-white/20" />

              {/* Center crosshair */}
              <div className="absolute w-full h-[1px] bg-white/10" />
              <div className="absolute h-full w-[1px] bg-white/10" />

              {primaryIncident && <div className="absolute z-10 flex flex-col items-center">
                <div className="relative flex items-center justify-center">
                  <span className="animate-ping absolute inline-flex h-8 w-8 rounded-full bg-[#D93636] opacity-75"></span>
                  <div className="w-6 h-6 rounded-full bg-[#D93636] border-2 border-white flex items-center justify-center shadow-lg">
                    <Car className="w-3.5 h-3.5 text-white" />
                  </div>
                </div>
                <div className="mt-1 px-1.5 py-0.5 rounded bg-black/80 backdrop-blur-xs text-[10px] font-mono text-white font-bold whitespace-nowrap border border-white/20">
                  {primaryIncident.vehiclePlate} (SOS)
                </div>
              </div>}

              {/* Radar controls */}
              <div className="absolute bottom-2 left-2 z-10 flex items-center gap-1.5 bg-black/60 backdrop-blur-xs px-2 py-1 rounded-[6px] text-[10px] text-white font-mono">
                <span>Perimeter: 5.0 km</span>
                <span>•</span>
                <span>Accuracy: 3.5m</span>
              </div>
            </div>

            {/* Telemetry metadata footer */}
            <div className="mt-3 p-2.5 bg-[#F5F7FA] rounded-[8px] border border-[#E2E8F0] text-xs space-y-1">
              <div className="flex justify-between text-[#172B43] font-medium">
                <span>Primary Target:</span>
                <span className="font-mono">{vehicle.licensePlate} ({vehicle.model})</span>
              </div>
              <div className="flex justify-between text-[#718096] text-[11px]">
                <span>Coordinates:</span>
                <span className="font-mono">
                  {primaryIncident ? `${primaryIncident.location.lat.toFixed(5)}°, ${primaryIncident.location.lng.toFixed(5)}°` : 'Unavailable'}
                </span>
              </div>
            </div>
          </div>

          {/* Real-time Notification Timeline (Section 7 requirement) */}
          <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-4 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-[#142B4A]" />
                <h3 className="text-[15px] font-semibold text-[#172B43]">
                  Live Notification Stream
                </h3>
              </div>
              <span className="text-[11px] text-[#718096]">Auto-refreshing</span>
            </div>

            <div className="mt-3 space-y-2.5 text-xs max-h-56 overflow-y-auto pr-1">
              {incidents.flatMap((inc) => inc.timeline).slice(0, 5).map((evt) => (
                <div key={evt.id} className="p-2 rounded-[8px] bg-[#F5F7FA] border border-[#E2E8F0]">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-[#172B43] truncate">{evt.title}</span>
                    <span className="text-[10px] text-[#718096] shrink-0 font-mono ml-2">
                      {new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-[11px] text-[#718096] mt-0.5 line-clamp-2">
                    {evt.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Professional Data Table (Section 7 requirement) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white rounded-[12px] border border-[#E2E8F0] p-5 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E2E8F0]">
              <div>
                <h3 className="text-[17px] font-semibold text-[#172B43]">
                  Incident Queue & Dispatch Console
                </h3>
                <p className="text-xs text-[#718096]">
                  Emergency alerts are strictly distinguished from routine parking notices.
                </p>
              </div>

              {/* Filters */}
              <div className="flex items-center gap-2">
                <div className="flex bg-[#F5F7FA] p-0.5 rounded-[8px] border border-[#E2E8F0]">
                  <button
                    onClick={() => setFilterType('all')}
                    className={`px-2.5 py-1 text-xs font-medium rounded-[6px] transition-colors ${
                      filterType === 'all'
                        ? 'bg-white text-[#142B4A] shadow-xs font-semibold'
                        : 'text-[#718096] hover:text-[#172B43]'
                    }`}
                  >
                    All ({incidents.length})
                  </button>
                  <button
                    onClick={() => setFilterType('critical')}
                    className={`px-2.5 py-1 text-xs font-medium rounded-[6px] transition-colors ${
                      filterType === 'critical'
                        ? 'bg-[#D93636] text-white shadow-xs font-semibold'
                        : 'text-[#D93636] hover:bg-[#D93636]/10'
                    }`}
                  >
                    Critical SOS ({activeSosCount})
                  </button>
                  <button
                    onClick={() => setFilterType('routine')}
                    className={`px-2.5 py-1 text-xs font-medium rounded-[6px] transition-colors ${
                      filterType === 'routine'
                        ? 'bg-white text-[#142B4A] shadow-xs font-semibold'
                        : 'text-[#718096] hover:text-[#172B43]'
                    }`}
                  >
                    Routine ({routineCount})
                  </button>
                </div>
              </div>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-[#718096] absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search by Plate, Incident ID, Address, or Keyword..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full text-xs pl-9 pr-3 py-2 rounded-[8px] border border-[#E2E8F0] focus:outline-none focus:border-[#142B4A] text-[#172B43]"
              />
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[#E2E8F0] text-[#718096] uppercase text-[11px] tracking-wider bg-[#F5F7FA]/60">
                    <th className="py-2.5 px-3 font-semibold">Alert Type</th>
                    <th className="py-2.5 px-3 font-semibold">Incident ID</th>
                    <th className="py-2.5 px-3 font-semibold">Vehicle</th>
                    <th className="py-2.5 px-3 font-semibold">Status</th>
                    <th className="py-2.5 px-3 font-semibold">Assigned Unit</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0]">
                  {filteredIncidents.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-[#718096]">
                        No incidents matching current criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredIncidents.map((inc) => {
                      const isSos = inc.type === 'emergency_sos' || inc.type === 'ambulance';

                      return (
                        <tr
                          key={inc.id}
                          className={`transition-colors ${
                            isSos
                              ? 'bg-[#FFF8F8]/80 hover:bg-[#FFF0F0]'
                              : 'hover:bg-[#F5F7FA]/60'
                          }`}
                        >
                          <td className="py-3 px-3">
                            {isSos ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] text-[11px] font-bold bg-[#D93636] text-white">
                                <AlertOctagon className="w-3 h-3" />
                                Critical SOS
                              </span>
                            ) : inc.type === 'police' ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] text-[11px] font-semibold bg-[#203D60] text-white">
                                <Shield className="w-3 h-3" />
                                Police Call
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] text-[11px] font-medium bg-[#E2E8F0] text-[#172B43]">
                                <FileText className="w-3 h-3 text-[#718096]" />
                                Routine
                              </span>
                            )}
                          </td>

                          <td className="py-3 px-3 font-mono font-semibold text-[#142B4A]">
                            {inc.id}
                          </td>

                          <td className="py-3 px-3">
                            <span className="font-mono font-bold text-[#172B43] block">
                              {inc.vehiclePlate}
                            </span>
                            <span className="text-[11px] text-[#718096] block truncate max-w-[120px]">
                              {inc.vehicleDescription}
                            </span>
                          </td>

                          <td className="py-3 px-3">
                            <span
                              className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                inc.status === 'resolved'
                                  ? 'bg-[#23845B]/10 text-[#23845B]'
                                  : inc.status === 'active_sos'
                                  ? 'bg-[#D93636] text-white font-bold'
                                  : inc.status === 'dispatched' || inc.status === 'en_route'
                                  ? 'bg-[#D99A27]/20 text-[#D99A27] font-semibold'
                                  : 'bg-[#142B4A]/10 text-[#142B4A]'
                              }`}
                            >
                              {inc.status.replace('_', ' ').toUpperCase()}
                            </span>
                          </td>

                          <td className="py-3 px-3 text-[#172B43]">
                            {inc.assignedResponder ? (
                              <span className="font-semibold text-xs block text-[#142B4A]">
                                {inc.assignedResponder.name.split(',')[0]}
                              </span>
                            ) : (
                              <span className="text-[#718096] text-[11px]">Unassigned</span>
                            )}
                          </td>

                          <td className="py-3 px-3 text-right">
                            <button
                              onClick={() => setSelectedIncidentId(inc.id)}
                              className="px-2.5 py-1 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[6px] text-xs font-medium transition-colors"
                            >
                              Dispatch CAD
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Incident Detail Modal */}
      <IncidentDetailModal
        incidentId={selectedIncidentId}
        onClose={() => setSelectedIncidentId(null)}
      />
    </div>
  );
};
