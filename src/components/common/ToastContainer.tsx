import React from 'react';
import { useEmergency } from '../../context/EmergencyContext';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useEmergency();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none px-4 sm:px-0">
      {toasts.map((toast) => {
        let borderClass = 'border-[#E2E8F0]';
        let bgClass = 'bg-white';
        let icon = <Info className="w-4 h-4 text-[#142B4A] shrink-0" />;

        if (toast.type === 'danger') {
          borderClass = 'border-[#D93636]';
          bgClass = 'bg-[#FFF5F5]';
          icon = <AlertCircle className="w-4 h-4 text-[#D93636] shrink-0" />;
        } else if (toast.type === 'success') {
          borderClass = 'border-[#23845B]';
          bgClass = 'bg-[#F2FAF6]';
          icon = <CheckCircle2 className="w-4 h-4 text-[#23845B] shrink-0" />;
        } else if (toast.type === 'warning') {
          borderClass = 'border-[#D99A27]';
          bgClass = 'bg-[#FFFBF0]';
          icon = <AlertCircle className="w-4 h-4 text-[#D99A27] shrink-0" />;
        }

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-[10px] shadow-sm border ${borderClass} ${bgClass} transition-all`}
          >
            {icon}
            <div className="flex-1 text-xs font-medium text-[#172B43] leading-snug">
              {toast.text}
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-[#718096] hover:text-[#172B43] shrink-0"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
