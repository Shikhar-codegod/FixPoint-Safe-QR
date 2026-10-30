import { useEffect, useState } from 'react';
import { ClaimDraft } from '../types/claims';

const DRAFT_VERSION = 1;

export const emptyClaimDraft: ClaimDraft = {
  step: 1,
  safetyConfirmed: false,
  injured: false,
  thirdPartyDamage: false,
  theft: false,
  approximateDate: new Date().toISOString().slice(0, 16),
  locationText: '',
  vehicleMovable: 'unsure',
  otherVehicleInvolved: false,
  otherVehicleDetails: '',
  thirdPartyInjury: false,
  thirdPartyPropertyDamage: false,
  description: '',
  checklist: {},
  insurerNotified: false,
  claimReference: '',
};

export function useClaimDraft(qrCode: string) {
  const storageKey = `fixpoint-claim-draft:v${DRAFT_VERSION}:${qrCode || 'unknown'}`;
  const [draft, setDraft] = useState<ClaimDraft>(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      return saved ? { ...emptyClaimDraft, ...JSON.parse(saved) } : emptyClaimDraft;
    } catch {
      return emptyClaimDraft;
    }
  });

  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify(draft));
  }, [draft, storageKey]);

  const updateDraft = (patch: Partial<ClaimDraft>) => setDraft((current) => ({ ...current, ...patch }));
  const clearDraft = () => {
    localStorage.removeItem(storageKey);
    setDraft({ ...emptyClaimDraft, approximateDate: new Date().toISOString().slice(0, 16) });
  };
  return { draft, updateDraft, clearDraft };
}
