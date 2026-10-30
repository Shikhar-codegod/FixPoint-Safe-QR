/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { EmergencyProvider, useEmergency } from './context/EmergencyContext';
import { Header } from './components/common/Header';
import { Sidebar } from './components/common/Sidebar';
import { ToastContainer } from './components/common/ToastContainer';
import { PublicQrScreen } from './components/public/PublicQrScreen';
import { CustomerDashboard } from './components/customer/CustomerDashboard';
import { OperationsDashboard } from './components/operations/OperationsDashboard';
import { ResponderDashboard } from './components/responder/ResponderDashboard';
import { Menu } from 'lucide-react';

const MainAppContent: React.FC = () => {
  const { role } = useEmergency();
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // If role changes, reset tab to reasonable default
  React.useEffect(() => {
    if (role === 'customer') setCurrentTab('overview');
    else if (role === 'operations') setCurrentTab('live_incidents');
    else if (role === 'responder') setCurrentTab('assigned');
  }, [role]);

  return (
    <div className="min-h-screen bg-[#F5F7FA] text-[#172B43] flex flex-col font-sans">
      {/* Universal Top Header with Role Switcher & System Status */}
      <Header />

      {/* Main Container */}
      {role === 'public-qr' ? (
        <main className="flex-1">
          <PublicQrScreen />
        </main>
      ) : (
        <div className="flex-1 flex max-w-7xl w-full mx-auto">
          {/* Section 6: Fixed left sidebar approximately 250px wide */}
          <Sidebar
            currentTab={currentTab}
            onSelectTab={setCurrentTab}
            mobileOpen={mobileMenuOpen}
            onCloseMobile={() => setMobileMenuOpen(false)}
          />

          {/* Main content area */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* Mobile Top Bar to open drawer */}
            <div className="md:hidden flex items-center justify-between px-4 py-3 bg-white border-b border-[#E2E8F0]">
              <button
                onClick={() => setMobileMenuOpen(true)}
                className="flex items-center gap-2 text-xs font-semibold text-[#142B4A] p-1.5 rounded-[6px] border border-[#E2E8F0]"
              >
                <Menu className="w-4 h-4" />
                <span>Navigation Menu</span>
              </button>
              <span className="text-xs font-medium text-[#718096] capitalize">
                {role} Mode
              </span>
            </div>

            {/* Dashboard Content Area */}
            <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
              {role === 'customer' && (
                <CustomerDashboard
                  activeTab={currentTab}
                  setActiveTab={setCurrentTab}
                />
              )}

              {role === 'operations' && (
                <OperationsDashboard
                  activeTab={currentTab}
                  setActiveTab={setCurrentTab}
                />
              )}

              {role === 'responder' && (
                <ResponderDashboard
                  activeTab={currentTab}
                  setActiveTab={setCurrentTab}
                />
              )}
            </main>
          </div>
        </div>
      )}

      {/* Toast Notifications */}
      <ToastContainer />
    </div>
  );
};

export default function App() {
  return (
    <EmergencyProvider>
      <MainAppContent />
    </EmergencyProvider>
  );
}
