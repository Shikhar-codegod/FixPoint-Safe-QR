import React, { useMemo, useState } from 'react';
import {
  AlertTriangle, ArrowLeft, ArrowRight, Check, ClipboardList,
  Copy, Crosshair, ExternalLink, FileCheck2, ShieldAlert, X,
} from 'lucide-react';
import { claimGuide } from '../../data/claimGuide';
import { useClaimDraft } from '../../hooks/useClaimDraft';
import { ChecklistMark, ClaimPathId } from '../../types/claims';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  qrCode: string;
  onOpenEmergency?: () => void;
}

const steps = ['Safety', 'Who are you?', 'What happened?', 'Quick facts', 'Checklist', 'Steps', 'Tell insurer', 'Summary'];
const chipLabels = { core: 'Core/common', conditional: 'Conditional', insurer_specific: 'Insurer-specific' };
const markLabels: Record<ChecklistMark, string> = {
  have: 'Have it',
  missing: "Don't have yet",
  not_applicable: 'Not applicable',
  ask_insurer: 'Ask insurer',
};

const fieldClass = 'w-full rounded-[8px] border border-[#E2E8F0] px-3 py-2 text-sm text-[#172B43] focus:outline-none focus:border-[#142B4A]';
const buttonClass = 'rounded-[8px] px-3 py-2 text-sm font-medium transition-colors';

export const PublicClaimHelpModal: React.FC<Props> = ({ isOpen, onClose, qrCode, onOpenEmergency }) => {
  const { draft, updateDraft, clearDraft } = useClaimDraft(qrCode);
  const [copyState, setCopyState] = useState('');
  const [gpsState, setGpsState] = useState('');
  // Public claim guidance must not expose the vehicle owner's private insurance or contact data.

  const selectedPath = useMemo(
    () => claimGuide.paths.find((candidate) => candidate.id === draft.pathId) || claimGuide.paths[0],
    [draft.pathId],
  );
  const checklist = selectedPath.checklist.filter((item) => {
    if (!item.appliesWhen) return true;
    return draft.thirdPartyInjury || draft.thirdPartyPropertyDamage || draft.theft || draft.otherVehicleInvolved;
  });
  const progress = Math.round(((draft.step - 1) / (steps.length - 1)) * 100);
  const suggestedPath = draft.thirdPartyInjury
    ? 'third_party_injury_death'
    : draft.theft
      ? 'theft'
      : draft.thirdPartyPropertyDamage
        ? 'third_party_property'
        : 'own_damage';

  if (!isOpen) return null;

  const setStep = (step: number) => updateDraft({ step: Math.max(1, Math.min(8, step)) });
  const next = () => setStep(draft.step + 1);
  const previous = () => setStep(draft.step - 1);
  const choosePath = (pathId: ClaimPathId) => updateDraft({ pathId, step: 4 });

  const useGps = () => {
    if (!navigator.geolocation) {
      setGpsState('GPS unavailable');
      return;
    }
    setGpsState('Requesting location…');
    navigator.geolocation.getCurrentPosition(
      (position) => {
        updateDraft({
          gps: {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
          },
        });
        setGpsState(`Accuracy ±${Math.round(position.coords.accuracy)} metres`);
      },
      () => setGpsState('GPS unavailable'),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  };

  const summary = [
    `FixPoint Safe-QR insurance guidance summary`,
    `Path: ${selectedPath.title}`,
    `Role: ${draft.role === 'owner_driver' ? 'Owner/driver' : 'Other driver/witness'}`,
    `Approximate date/time: ${draft.approximateDate || 'Not available'}`,
    `Location: ${draft.locationText || (draft.gps ? `${draft.gps.latitude}, ${draft.gps.longitude} (±${Math.round(draft.gps.accuracy)}m)` : 'Not available')}`,
    `Vehicle movable: ${draft.vehicleMovable}`,
    `Other vehicle details: ${draft.otherVehicleDetails || 'Not available'}`,
    `Description: ${draft.description || 'Not available'}`,
    `Insurer notified by user: ${draft.insurerNotified ? `Yes (${draft.insurerNotifiedAt || 'time not recorded'})` : 'No'}`,
    `Claim reference: ${draft.claimReference || 'Not available'}`,
  ].join('\n');

  const copySummary = async () => {
    try {
      await navigator.clipboard.writeText(summary);
      setCopyState('Copied');
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = summary;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      textarea.remove();
      setCopyState('Copied');
    }
    window.setTimeout(() => setCopyState(''), 1800);
  };

  const renderSafety = () => (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold">Is anyone injured or in danger?</h4>
      <p className="text-sm text-[#718096]">Safety comes before paperwork. Choose the option that reflects the situation now.</p>
      {!draft.safetyConfirmed ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <button type="button" onClick={() => updateDraft({ injured: true, safetyConfirmed: true })} className={`${buttonClass} bg-[#FFF5F5] border border-[#D93636]/40 text-[#D93636]`}>Yes, urgent help may be needed</button>
          <button type="button" onClick={() => updateDraft({ injured: false, safetyConfirmed: true })} className={`${buttonClass} bg-[#F5F7FA] border border-[#E2E8F0] text-[#142B4A]`}>No, everyone is safe</button>
        </div>
      ) : draft.injured ? (
        <div className="space-y-3 rounded-[10px] border border-[#D93636]/40 bg-[#FFF5F5] p-4">
          <div className="flex items-start gap-2 text-[#D93636]"><ShieldAlert className="w-5 h-5 shrink-0" /><strong>People first. Do not delay urgent care for paperwork.</strong></div>
          <div className="grid grid-cols-2 gap-2">
            <a href="tel:112" className={`${buttonClass} bg-[#142B4A] text-center text-white`}>Call 112</a>
            <a href="tel:108" className={`${buttonClass} bg-[#D93636] text-center text-white`}>Call 108</a>
          </div>
          {onOpenEmergency && <button type="button" onClick={() => { onClose(); onOpenEmergency(); }} className={`${buttonClass} w-full border border-[#D93636]/40 text-[#D93636]`}>Open Emergency Alert</button>}
          <button type="button" onClick={() => updateDraft({ injured: false })} className={`${buttonClass} w-full bg-white border border-[#E2E8F0] text-[#172B43]`}>Everyone is safe, continue</button>
        </div>
      ) : (
        <div className="rounded-[10px] bg-[#F5F7FA] p-4 text-sm text-[#172B43]"><Check className="mr-2 inline h-4 w-4 text-[#23845B]" />Everyone is safe. Continue when ready.</div>
      )}
    </div>
  );

  const renderRole = () => (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold">Who are you?</h4>
      <div className="grid gap-3">
        <button type="button" onClick={() => updateDraft({ role: 'owner_driver' })} className={`${buttonClass} text-left ${draft.role === 'owner_driver' ? 'bg-[#142B4A] text-white' : 'border border-[#E2E8F0]'}`}>I own or drive this vehicle</button>
        <button type="button" onClick={() => updateDraft({ role: 'other_driver_witness' })} className={`${buttonClass} text-left ${draft.role === 'other_driver_witness' ? 'bg-[#142B4A] text-white' : 'border border-[#E2E8F0]'}`}>I'm the other driver or a witness</button>
      </div>
      {draft.role === 'other_driver_witness' && <div className="rounded-[10px] border border-[#E2E8F0] bg-[#F5F7FA] p-3 text-sm text-[#172B43]">Collect evidence when safe and notify <strong>your own insurer</strong>. This screen does not show the vehicle owner's insurer, policy, or phone.</div>}
    </div>
  );

  const renderPath = () => (
    <div className="space-y-3">
      <h4 className="text-lg font-semibold">What happened?</h4>
      <div className="grid gap-2 sm:grid-cols-2">
        {claimGuide.paths.map((pathOption) => (
          <button key={pathOption.id} type="button" onClick={() => choosePath(pathOption.id)} className={`${buttonClass} border text-left ${draft.pathId === pathOption.id ? 'border-[#142B4A] bg-[#F5F7FA]' : 'border-[#E2E8F0]'}`}>
            <span className="block font-semibold text-[#172B43]">{pathOption.title}</span>
            <span className="mt-1 block text-xs text-[#718096]">{pathOption.whenThisApplies}</span>
          </button>
        ))}
      </div>
      {selectedPath.id === 'not_sure' && <div className="space-y-2 rounded-[10px] border border-[#E2E8F0] p-3 text-sm"><p>Answer these three questions in Quick facts: injured people, third-party damage, or theft.</p><p className="text-[#718096]">Current suggestion: <strong className="text-[#172B43]">{claimGuide.paths.find((candidate) => candidate.id === suggestedPath)?.title}</strong></p></div>}
    </div>
  );

  const renderFacts = () => (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold">Quick facts <span className="text-sm font-normal text-[#718096]">(all optional)</span></h4>
      <label className="block text-sm">Date and time (approximate)<input aria-label="Approximate date and time" type="datetime-local" value={draft.approximateDate} onChange={(e) => updateDraft({ approximateDate: e.target.value })} className={`${fieldClass} mt-1`} /></label>
      <div><label className="block text-sm">Location</label><div className="mt-1 flex gap-2"><input aria-label="Location description" value={draft.locationText} onChange={(e) => updateDraft({ locationText: e.target.value })} placeholder="Manual location or landmark" className={fieldClass} /><button type="button" onClick={useGps} className={`${buttonClass} whitespace-nowrap border border-[#E2E8F0]`}><Crosshair className="mr-1 inline h-4 w-4" />Use GPS</button></div><p className="mt-1 text-xs text-[#718096]">{gpsState || (draft.gps ? `GPS saved: ±${Math.round(draft.gps.accuracy)} metres` : 'GPS unavailable until permission is granted; no accuracy is guessed.')}</p></div>
      <div><span className="block text-sm">Vehicle movable?</span><div className="mt-1 flex gap-2">{(['yes', 'no', 'unsure'] as const).map((value) => <button key={value} type="button" onClick={() => updateDraft({ vehicleMovable: value })} className={`${buttonClass} border ${draft.vehicleMovable === value ? 'border-[#142B4A] bg-[#F5F7FA]' : 'border-[#E2E8F0]'}`}>{value}</button>)}</div></div>
      <label className="block text-sm">Other vehicle involved?<input type="checkbox" checked={draft.otherVehicleInvolved} onChange={(e) => updateDraft({ otherVehicleInvolved: e.target.checked })} className="ml-2" /></label>
      {draft.otherVehicleInvolved && <textarea aria-label="Other vehicle details" value={draft.otherVehicleDetails} onChange={(e) => updateDraft({ otherVehicleDetails: e.target.value })} placeholder="Partial plate, make/model/colour, driver/contact, insurer if known, witnesses. Only when safe; never guess a registration number." rows={3} className={fieldClass} />}
      <div className="grid gap-2 sm:grid-cols-2 text-sm"><label><input type="checkbox" checked={draft.thirdPartyInjury} onChange={(e) => updateDraft({ thirdPartyInjury: e.target.checked, injured: e.target.checked || draft.injured })} className="mr-2" />Third-party injury or death</label><label><input type="checkbox" checked={draft.thirdPartyPropertyDamage} onChange={(e) => updateDraft({ thirdPartyPropertyDamage: e.target.checked, thirdPartyDamage: e.target.checked })} className="mr-2" />Third-party property damage</label><label><input type="checkbox" checked={draft.theft} onChange={(e) => updateDraft({ theft: e.target.checked })} className="mr-2" />Theft</label></div>
      <label className="block text-sm">Short factual description<textarea value={draft.description} onChange={(e) => updateDraft({ description: e.target.value })} rows={3} className={`${fieldClass} mt-1`} /></label>
    </div>
  );

  const renderChecklist = () => (
    <div className="space-y-3">
      <h4 className="text-lg font-semibold">Checklist</h4>
      <div className="flex flex-wrap gap-2 text-xs"><span>Legend:</span>{Object.entries(chipLabels).map(([key, label]) => <span key={key} className="rounded-full bg-[#F5F7FA] px-2 py-1 text-[#172B43]">{label}</span>)}</div>
      {checklist.map((item) => <div key={item.id} className="rounded-[10px] border border-[#E2E8F0] p-3"><div className="flex flex-wrap items-start justify-between gap-2"><div><strong className="text-sm">{item.label}</strong><span className="ml-2 rounded-full bg-[#F5F7FA] px-2 py-1 text-[10px]">{chipLabels[item.status]}</span><p className="mt-1 text-xs text-[#718096]">{item.why}</p></div><select aria-label={`${item.label} status`} value={draft.checklist[item.id] || ''} onChange={(e) => updateDraft({ checklist: { ...draft.checklist, [item.id]: e.target.value as ChecklistMark } })} className="rounded border border-[#E2E8F0] p-1 text-xs"><option value="">Choose</option>{Object.entries(markLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div></div>)}
      <div className="h-2 overflow-hidden rounded-full bg-[#E2E8F0]"><div className="h-full bg-[#23845B]" style={{ width: `${Math.round((Object.keys(draft.checklist).length / checklist.length) * 100)}%` }} /></div>
      <p className="text-xs text-[#718096]">Checklist progress is guidance only. Missing items never block you.</p>
    </div>
  );

  const renderSteps = () => (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold">{selectedPath.title}: steps and cautions</h4>
      <ol className="list-decimal space-y-2 pl-5 text-sm">{selectedPath.steps.map((item) => <li key={item}>{item}</li>)}</ol>
      <div className="rounded-[10px] border border-[#D93636]/30 bg-[#FFF5F5] p-3"><strong className="text-[#D93636]">Do not</strong><ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{['Admit liability, promise compensation, or privately settle a third-party claim.', 'Sign blank forms or release documents.', 'Repair or dismantle before asking the insurer about survey.', 'Ignore legal notices or summons; forward them to the insurer promptly.'].concat(selectedPath.cautions).map((item) => <li key={item}>{item}</li>)}</ul></div>
    </div>
  );

  const renderNotify = () => (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold">Tell the insurer</h4>
      <p className="text-sm text-[#718096]">Use the number or app on the policy document, or the insurer's official website. FixPoint does not invent insurer contact details.</p>
      <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={draft.insurerNotified} onChange={(e) => updateDraft({ insurerNotified: e.target.checked, insurerNotifiedAt: e.target.checked ? new Date().toISOString() : undefined })} className="mt-1" />I have notified my insurer</label>
      {draft.insurerNotified && <div className="rounded-[8px] bg-[#F5F7FA] p-3 text-sm text-[#23845B]"><Check className="mr-1 inline h-4 w-4" />Insurer notified (reported by you) at {new Date(draft.insurerNotifiedAt || '').toLocaleString()}</div>}
      <label className="block text-sm">Claim reference (optional)<input value={draft.claimReference} onChange={(e) => updateDraft({ claimReference: e.target.value })} className={`${fieldClass} mt-1`} /></label>
      <div className="space-y-1">{claimGuide.trackerStates.map((state, index) => <div key={state} className="flex items-center gap-2 text-sm"><span className={`h-2.5 w-2.5 rounded-full ${index === 0 || (index === 2 && draft.pathId) || (index === 3 && draft.insurerNotified) || (index === 4 && draft.claimReference) ? 'bg-[#23845B]' : 'bg-[#E2E8F0]'}`} /><span>{state}</span><span className="text-xs text-[#718096]">{index === 3 && draft.insurerNotified ? 'reported by you' : index < 3 ? 'generated by FixPoint' : 'confirmed by insurer'}</span></div>)}</div>
    </div>
  );

  const renderSummary = () => (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold">Summary and grievance</h4>
      <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-[10px] bg-[#F5F7FA] p-3 text-xs text-[#172B43]">{summary}</pre>
      <button type="button" onClick={copySummary} className={`${buttonClass} border border-[#E2E8F0]`}><Copy className="mr-1 inline h-4 w-4" />{copyState || 'Copy summary'}</button>
      <div className="rounded-[10px] border border-[#E2E8F0] p-3 text-sm"><strong>Grievance route</strong><p className="mt-1 text-[#718096]">Write to the insurer's Grievance Redressal Officer, then IRDAI Bima Bharosa, then the Insurance Ombudsman. Verify the current procedure first.</p><div className="mt-2 flex flex-wrap gap-3"><a className="text-[#142B4A] underline" href="https://bimabharosa.irdai.gov.in/" target="_blank" rel="noreferrer">Bima Bharosa <ExternalLink className="inline h-3 w-3" /></a><a className="text-[#142B4A] underline" href="https://www.cioins.co.in/" target="_blank" rel="noreferrer">Insurance Ombudsman <ExternalLink className="inline h-3 w-3" /></a></div></div>
      <button type="button" onClick={clearDraft} className={`${buttonClass} border border-[#E2E8F0] text-[#D93636]`}>Clear saved draft</button>
    </div>
  );

  const panels = [renderSafety, renderRole, renderPath, renderFacts, renderChecklist, renderSteps, renderNotify, renderSummary];
  const isSafetyEmergency = draft.step === 1 && draft.injured;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
      <div className="flex max-h-[92vh] w-full max-w-md flex-col overflow-hidden rounded-[14px] border border-[#E2E8F0] bg-white shadow-xl">
        <div className="flex items-center justify-between bg-[#142B4A] p-4 text-white">
          <div className="flex items-center gap-3"><ClipboardList className="h-6 w-6" /><div><h3 className="font-semibold">{draft.injured ? 'Emergency help' : 'Accident & Insurance Claim Help'}</h3><p className="text-xs text-slate-300">{draft.injured ? 'People first' : 'Guidance only • no claim filing'}</p></div></div>
          <button aria-label="Close claims help" onClick={onClose} className="p-1 text-slate-300 hover:text-white"><X className="h-5 w-5" /></button>
        </div>
        {!isSafetyEmergency && <div className="border-b border-[#E2E8F0] px-5 pt-4"><div className="rounded-[8px] border border-[#D99A27]/30 bg-[#FFF9E8] p-2 text-xs text-[#172B43]"><AlertTriangle className="mr-1 inline h-4 w-4 text-[#D99A27]" />Guidance only. FixPoint does not register your claim with any insurer, decide coverage, or give legal advice. No outcome is guaranteed.</div><div className="mt-3 flex items-center justify-between text-xs text-[#718096]"><span>Step {draft.step} of 8: {steps[draft.step - 1]}</span><span>{progress}%</span></div><div className="mt-2 h-1.5 rounded-full bg-[#E2E8F0]"><div className="h-full bg-[#142B4A]" style={{ width: `${progress}%` }} /></div></div>}
        <div className="flex-1 overflow-y-auto p-5">{panels[draft.step - 1]()}</div>
        {!isSafetyEmergency && <><div className="flex items-center justify-between border-t border-[#E2E8F0] bg-white p-4">
          <button type="button" onClick={previous} disabled={draft.step === 1} className={`${buttonClass} border border-[#E2E8F0] disabled:opacity-40`}><ArrowLeft className="mr-1 inline h-4 w-4" />Back</button>
          {draft.step < 8 ? <button type="button" onClick={next} className={`${buttonClass} bg-[#142B4A] text-white`}>Next<ArrowRight className="ml-1 inline h-4 w-4" /></button> : <button type="button" onClick={onClose} className={`${buttonClass} bg-[#142B4A] text-white`}><FileCheck2 className="mr-1 inline h-4 w-4" />Done</button>}
        </div>
        <div className="border-t border-[#E2E8F0] px-5 py-2 text-[10px] text-[#718096]">Sources and last verified: {claimGuide.lastVerified} · {claimGuide.sources.map((source) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer" className="mr-1 underline">{source.label}</a>)}</div></>}
      </div>
    </div>
  );
};
