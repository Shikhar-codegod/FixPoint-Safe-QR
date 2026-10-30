import React from 'react';
import { useEmergency, AppRole } from '../../context/EmergencyContext';
import { BrandLogo } from './BrandLogo';
import {
  QrCode,
  User,
  Activity,
  ShieldAlert,
  Smartphone,
  RotateCcw,
  Radio,
} from 'lucide-react';

export const Header: React.FC = () => {
  const {
    role,
    setRole,
    incidents,
    isMobileFrame,
    setIsMobileFrame,
    resetDemoData,
  } = useEmergency();

  const activeSosCount = incidents.filter(
    (i) => i.status === 'active_sos' || i.status === 'dispatched' || i.status === 'en_route'
  ).length;

  const rolesList: { id: AppRole; label: string; icon: React.ReactNode; badge?: number }[] = [
    {
      id: 'public-qr',
      label: 'Public QR Screen',
      icon: <QrCode className="w-4 h-4" />,
    },
    {
      id: 'customer',
      label: 'Customer Dashboard',
      icon: <User className="w-4 h-4" />,
    },
    {
      id: 'operations',
      label: 'Operations Command',
      icon: <Activity className="w-4 h-4" />,
      badge: activeSosCount > 0 ? activeSosCount : undefined,
    },
    {
      id: 'responder',
      label: 'Responder Portal',
      icon: <ShieldAlert className="w-4 h-4" />,
    },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-[#E2E8F0] shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Left: Brand */}
        <div className="flex items-center gap-6">
          <BrandLogo size="sm" showSubtitle={false} />
          
          <div className="hidden lg:flex items-center gap-2 pl-4 border-l border-[#E2E8F0]">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#23845B] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#23845B]"></span>
            </span>
            <span className="text-xs font-medium text-[#718096]">
              Safe-QR Network Online
            </span>
          </div>
        </div>

        {/* Center: Role Switcher */}
        <nav className="flex items-center bg-[#F5F7FA] p-1 rounded-[10px] border border-[#E2E8F0] overflow-x-auto max-w-full">
          {rolesList.map((tab) => {
            const isActive = role === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setRole(tab.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-[8px] text-xs font-medium transition-colors whitespace-nowrap ${
                  isActive
                    ? 'bg-[#142B4A] text-white shadow-xs'
                    : 'text-[#172B43] hover:text-[#142B4A] hover:bg-slate-200/60'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
                {tab.badge !== undefined && (
                  <span
                    className={`ml-0.5 px-1.5 py-0.2 rounded-full text-[11px] font-bold ${
                      isActive ? 'bg-[#D93636] text-white' : 'bg-[#D93636]/15 text-[#D93636]'
                    }`}
                  >
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-2">
          {role === 'public-qr' && (
            <button
              onClick={() => setIsMobileFrame(!isMobileFrame)}
              title={isMobileFrame ? 'Expand to Full Screen View' : 'Switch to Mobile Frame'}
              className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-[8px] text-xs font-medium border border-[#E2E8F0] text-[#172B43] bg-white hover:bg-[#F5F7FA] transition-colors"
            >
              <Smartphone className="w-3.5 h-3.5 text-[#718096]" />
              <span>{isMobileFrame ? 'Phone Frame' : 'Full Canvas'}</span>
            </button>
          )}

          <button
            onClick={resetDemoData}
            title="Reset demo data to initial state"
            className="p-1.5 text-[#718096] hover:text-[#172B43] hover:bg-[#F5F7FA] rounded-[8px] border border-transparent hover:border-[#E2E8F0] transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
