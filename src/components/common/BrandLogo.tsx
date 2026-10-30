import React from 'react';

interface BrandLogoProps {
  variant?: 'light' | 'dark';
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  variant = 'dark',
  size = 'md',
  showSubtitle = true,
}) => {
  const isLight = variant === 'light';

  const iconSizes = {
    sm: 'w-7 h-7',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
  };

  const titleSizes = {
    sm: 'text-base font-semibold',
    md: 'text-lg font-bold tracking-tight',
    lg: 'text-2xl font-bold tracking-tight',
  };

  return (
    <div className="flex items-center gap-2.5 select-none">
      <div
        className={`${iconSizes[size]} rounded-[9px] bg-[#142B4A] border border-[#203D60] flex items-center justify-center shrink-0 shadow-sm relative overflow-hidden`}
      >
        {/* Subtle automotive pinpoint geometry */}
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-5 h-5 text-white"
        >
          {/* Target ring */}
          <circle cx="16" cy="16" r="10" stroke="#718096" strokeWidth="1.5" strokeDasharray="3 2" opacity="0.6" />
          {/* Outer shield or radar cross */}
          <path
            d="M16 6V10M16 22V26M6 16H10M22 16H26"
            stroke="#FFFFFF"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
          {/* Central Safe-QR / SOS Node in Emergency Red */}
          <rect x="12" y="12" width="8" height="8" rx="2" fill="#D93636" />
          <circle cx="16" cy="16" r="1.5" fill="#FFFFFF" />
        </svg>
      </div>

      <div className="flex flex-col leading-tight">
        <div className="flex items-center gap-1.5">
          <span className={`${titleSizes[size]} ${isLight ? 'text-white' : 'text-[#172B43]'}`}>
            FixPoint
          </span>
          <span className={`${titleSizes[size]} text-[#D93636]`}>Drive</span>
        </div>
        {showSubtitle && (
          <span
            className={`text-[11px] font-medium tracking-wider uppercase ${
              isLight ? 'text-slate-300' : 'text-[#718096]'
            }`}
          >
            Safe-QR SOS Platform
          </span>
        )}
      </div>
    </div>
  );
};
