export type ClaimPathId =
  | 'own_damage'
  | 'cashless_repair'
  | 'reimbursement_repair'
  | 'third_party_property'
  | 'third_party_injury_death'
  | 'theft'
  | 'total_loss'
  | 'addons_roadside'
  | 'hit_and_run'
  | 'not_sure';

export type ChecklistStatus = 'core' | 'conditional' | 'insurer_specific';
export type ChecklistMark = 'have' | 'missing' | 'not_applicable' | 'ask_insurer';
export type ClaimRole = 'owner_driver' | 'other_driver_witness';

export interface ClaimChecklistItem {
  id: string;
  label: string;
  status: ChecklistStatus;
  why: string;
  appliesWhen?: string;
}

export interface ClaimPath {
  id: ClaimPathId;
  title: string;
  whenThisApplies: string;
  steps: string[];
  checklist: ClaimChecklistItem[];
  cautions: string[];
}

export interface ClaimGuide {
  lastVerified: string;
  sources: { label: string; url: string }[];
  paths: ClaimPath[];
  trackerStates: string[];
}

export interface ClaimDraft {
  step: number;
  safetyConfirmed: boolean;
  role?: ClaimRole;
  pathId?: ClaimPathId;
  injured: boolean;
  thirdPartyDamage: boolean;
  theft: boolean;
  approximateDate: string;
  locationText: string;
  gps?: { latitude: number; longitude: number; accuracy: number };
  vehicleMovable: 'yes' | 'no' | 'unsure';
  otherVehicleInvolved: boolean;
  otherVehicleDetails: string;
  thirdPartyInjury: boolean;
  thirdPartyPropertyDamage: boolean;
  description: string;
  checklist: Record<string, ChecklistMark>;
  insurerNotified: boolean;
  claimReference: string;
  insurerNotifiedAt?: string;
}
