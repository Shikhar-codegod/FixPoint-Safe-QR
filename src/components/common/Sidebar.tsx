import React from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import { BrandLogo } from './BrandLogo';
import {
  Shield,
  PhoneCall,
  HeartPulse,
  Lock,
  History,
  Activity,
  MapPin,
  Users,
  Radio,
  FileText,
  Clock,
  Car,
  ChevronRight,
  LogOut,
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tabId: string) => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  mobileOpen,
  onCloseMobile,
}) => {
  const { role, vehicle, responderUser, incidents } = useEmergency();

  const activeSosCount = incidents.filter(
    (i) => i.status === 'active_sos' || i.status === 'dispatched' || i.status === 'en_route'
  ).length;

  // Define nav items according to the active role
  let navItems: { id: string; label: string; icon: React.ReactNode; badge?: number }[] = [];
  let userProfile = {
    name: 'User',
    roleLabel: 'Member',
    subLabel: '',
  };

  if (role === 'customer') {
    navItems = [
      { id: 'overview', label: 'Overview & Safe-QR', icon: <Car className="w-4 h-4" /> },
      { id: 'contacts', label: 'Emergency Contacts', icon: <PhoneCall className="w-4 h-4" /> },
      { id: 'medical', label: 'Medical Information', icon: <HeartPulse className="w-4 h-4" /> },
      { id: 'privacy', label: 'Privacy & Consents', icon: <Lock className="w-4 h-4" /> },
      { id: 'history', label: 'Incident History', icon: <History className="w-4 h-4" /> },
    ];
    userProfile = {
      name: vehicle.ownerName,
      roleLabel: 'Vehicle Owner',
      subLabel: vehicle.licensePlate,
    };
  } else if (role === 'operations') {
    navItems = [
      {
        id: 'live_incidents',
        label: 'Live Incidents',
        icon: <Activity className="w-4 h-4" />,
        badge: activeSosCount > 0 ? activeSosCount : undefined,
      },
      { id: 'radar_map', label: 'Map & Fleet Radar', icon: <MapPin className="w-4 h-4" /> },
      { id: 'responders', label: 'Responder Units', icon: <Users className="w-4 h-4" /> },
      { id: 'vehicles', label: 'Safe-QR Fleet', icon: <Car className="w-4 h-4" /> },
      { id: 'audit_logs', label: 'Audit Trail', icon: <FileText className="w-4 h-4" /> },
    ];
    userProfile = {
      name: 'Dispatch Console #04',
      roleLabel: 'Operations Command',
      subLabel: 'Regional Highway Authority',
    };
  } else if (role === 'responder') {
    navItems = [
      { id: 'assigned', label: 'Assigned Incidents', icon: <Activity className="w-4 h-4" />, badge: 1 },
      { id: 'triage', label: 'Incident Triage', icon: <Radio className="w-4 h-4" /> },
      { id: 'patient_medical', label: 'Authorized Medical', icon: <HeartPulse className="w-4 h-4" /> },
      { id: 'responder_logs', label: 'Action & Scene Logs', icon: <Clock className="w-4 h-4" /> },
    ];
    userProfile = {
      name: responderUser.name,
      roleLabel: responderUser.unitId,
      subLabel: `Badge: ${responderUser.badgeNumber}`,
    };
  }

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white border-r border-[#E2E8F0]">
      {/* Top Branding */}
      <div className="p-5 border-b border-[#E2E8F0]">
        <BrandLogo size="md" />
        <div className="mt-2 text-[12px] font-medium text-[#718096]">
          {role === 'customer' && 'Vehicle Owner Portal'}
          {role === 'operations' && 'Central Operations Command'}
          {role === 'responder' && 'Verified First Responder CAD'}
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => {
                onSelectTab(item.id);
                onCloseMobile();
              }}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-[8px] text-[14px] font-medium transition-colors text-left ${
                isActive
                  ? 'bg-[#142B4A] text-white shadow-xs'
                  : 'text-[#172B43] hover:text-[#142B4A] hover:bg-[#F5F7FA]'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className={isActive ? 'text-white' : 'text-[#718096]'}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && (
                <span
                  className={`px-1.5 py-0.5 rounded-full text-[11px] font-bold ${
                    isActive
                      ? 'bg-[#D93636] text-white'
                      : 'bg-[#D93636]/15 text-[#D93636]'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Role specific quick badge */}
      {role === 'responder' && (
        <div className="mx-3 mb-3 p-3 bg-[#F5F7FA] rounded-[10px] border border-[#E2E8F0]">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#23845B]">
            <span className="w-2 h-2 rounded-full bg-[#23845B]"></span>
            CAD Verification Active
          </div>
          <div className="text-[11px] text-[#718096] mt-0.5">
            Emergency token valid for 45 min
          </div>
        </div>
      )}

      {/* User Profile Section at Bottom */}
      <div className="p-3 border-t border-[#E2E8F0] bg-white">
        <div className="flex items-center gap-3 p-2 rounded-[8px] hover:bg-[#F5F7FA] transition-colors">
          <div className="w-9 h-9 rounded-full bg-[#142B4A] text-white flex items-center justify-center font-semibold text-xs shrink-0">
            {userProfile.name.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[13px] font-semibold text-[#172B43] truncate">
              {userProfile.name}
            </div>
            <div className="text-[11px] text-[#718096] truncate">
              {userProfile.roleLabel} • {userProfile.subLabel}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed Sidebar (approx 250px wide) */}
      <aside className="hidden md:block w-[250px] shrink-0 h-[calc(100vh-64px)] sticky top-16 z-20">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-xs"
            onClick={onCloseMobile}
          />
          <div className="relative w-[270px] max-w-[85vw] h-full shadow-xl z-10">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
