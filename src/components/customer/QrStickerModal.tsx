import React, { useEffect, useState } from 'react';
import QRCode from 'qrcode';
import { useEmergency } from '../../context/EmergencyContext';
import { BrandLogo } from '../common/BrandLogo';
import { Download, Printer, Shield, X, Check, Car } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const QrStickerModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { vehicle } = useEmergency();
  const [qrDataUrl, setQrDataUrl] = useState<string>('');
  const [decalFormat, setDecalFormat] = useState<'windshield' | 'rear_glass' | 'card'>('windshield');
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    const qrPayload = JSON.stringify({
      system: 'FixPoint Drive Safe-QR SOS',
      vehicleId: vehicle.id,
      plate: vehicle.licensePlate,
      vin: vehicle.vin,
      scanUrl: window.location.origin,
    });

    QRCode.toDataURL(qrPayload, {
      width: 320,
      margin: 1,
      color: {
        dark: '#142B4A',
        light: '#FFFFFF',
      },
    })
      .then((url) => setQrDataUrl(url))
      .catch((err) => console.error('Failed to generate QR', err));
  }, [isOpen, vehicle]);

  if (!isOpen) return null;

  const handleDownload = () => {
    if (!qrDataUrl) return;
    const link = document.createElement('a');
    link.href = qrDataUrl;
    link.download = `FixPoint-SafeQR-${vehicle.licensePlate}.png`;
    link.click();
    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 2500);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-[14px] border border-[#E2E8F0] shadow-xl w-full max-w-lg overflow-hidden">
        {/* Header */}
        <div className="bg-[#142B4A] text-white p-4.5 flex items-center justify-between">
          <div>
            <h3 className="text-[17px] font-semibold text-white">
              Official Safe-QR Decal Print Pack
            </h3>
            <p className="text-xs text-slate-300">
              Vehicle: {vehicle.licensePlate} • High-Durability Automotive Spec
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-300 hover:text-white p-1 rounded-md"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Format Selector */}
          <div className="flex gap-2 p-1 bg-[#F5F7FA] rounded-[10px] border border-[#E2E8F0]">
            <button
              onClick={() => setDecalFormat('windshield')}
              className={`flex-1 py-1.5 text-xs font-medium rounded-[8px] transition-colors ${
                decalFormat === 'windshield'
                  ? 'bg-white text-[#142B4A] shadow-xs font-semibold'
                  : 'text-[#718096] hover:text-[#172B43]'
              }`}
            >
              Windshield (Corner)
            </button>
            <button
              onClick={() => setDecalFormat('rear_glass')}
              className={`flex-1 py-1.5 text-xs font-medium rounded-[8px] transition-colors ${
                decalFormat === 'rear_glass'
                  ? 'bg-white text-[#142B4A] shadow-xs font-semibold'
                  : 'text-[#718096] hover:text-[#172B43]'
              }`}
            >
              Rear Window Decal
            </button>
            <button
              onClick={() => setDecalFormat('card')}
              className={`flex-1 py-1.5 text-xs font-medium rounded-[8px] transition-colors ${
                decalFormat === 'card'
                  ? 'bg-white text-[#142B4A] shadow-xs font-semibold'
                  : 'text-[#718096] hover:text-[#172B43]'
              }`}
            >
              Glovebox Card
            </button>
          </div>

          {/* Printable Decal Preview */}
          <div className="border-2 border-dashed border-[#142B4A]/30 p-5 rounded-[14px] bg-[#F8FAFC] flex flex-col items-center text-center">
            <div className="w-full max-w-[280px] bg-white p-4 rounded-[12px] border border-[#E2E8F0] shadow-sm flex flex-col items-center">
              <BrandLogo size="sm" showSubtitle={false} />

              <div className="my-3 p-2 bg-white rounded-lg border border-[#E2E8F0]">
                {qrDataUrl ? (
                  <img
                    src={qrDataUrl}
                    alt="FixPoint Safe-QR"
                    className="w-44 h-44 object-contain"
                  />
                ) : (
                  <div className="w-44 h-44 bg-slate-100 animate-pulse rounded" />
                )}
              </div>

              <div className="w-full text-center border-t border-[#E2E8F0] pt-2">
                <div className="font-mono text-xs font-bold text-[#142B4A] tracking-wider">
                  {vehicle.licensePlate}
                </div>
                <div className="text-[10px] text-[#D93636] font-semibold uppercase mt-0.5 tracking-wide">
                  Emergency Scan For Assistance
                </div>
                <div className="text-[9px] text-[#718096] mt-0.5">
                  FixPoint Drive • ID: {vehicle.safeQrCode}
                </div>
              </div>
            </div>
          </div>

          {/* Placement Instructions */}
          <div className="text-xs text-[#718096] space-y-1 bg-[#F5F7FA] p-3 rounded-[10px] border border-[#E2E8F0]">
            <div className="font-medium text-[#172B43] flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-[#142B4A]" />
              <span>Recommended Decal Placement</span>
            </div>
            <p>
              Affix to the lower passenger side of the front windshield or rear quarter glass. Clean surface with isopropyl alcohol prior to application.
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleDownload}
              className="flex-1 py-2.5 bg-[#142B4A] hover:bg-[#203D60] text-white rounded-[8px] text-[14px] font-medium flex items-center justify-center gap-2 transition-colors shadow-xs"
            >
              {downloadSuccess ? (
                <>
                  <Check className="w-4 h-4 text-[#23845B]" />
                  <span>Downloaded!</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Download High-Res PNG</span>
                </>
              )}
            </button>

            <button
              onClick={handlePrint}
              className="px-4 py-2.5 bg-white hover:bg-[#F5F7FA] text-[#172B43] border border-[#E2E8F0] rounded-[8px] text-[14px] font-medium flex items-center gap-2 transition-colors"
            >
              <Printer className="w-4 h-4 text-[#718096]" />
              <span>Print Sheet</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
