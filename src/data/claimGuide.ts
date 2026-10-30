import { ClaimGuide, ClaimPath } from '../types/claims';

const commonChecklist = [
  { id: 'policy', label: 'Policy number or policy document', status: 'core' as const, why: 'It helps the insurer locate the policy.' },
  { id: 'rc', label: 'Vehicle Registration Certificate (RC)', status: 'core' as const, why: 'It establishes the registered vehicle details.' },
  { id: 'licence', label: 'Driver licence', status: 'core' as const, why: 'It confirms who was driving.' },
  { id: 'photos', label: 'Photos or video of the scene and damage', status: 'core' as const, why: 'They preserve contemporaneous evidence.' },
  { id: 'description', label: 'Factual incident description', status: 'core' as const, why: 'The insurer needs your account of what happened.' },
  { id: 'fir', label: 'FIR or police record', status: 'conditional' as const, why: 'Police records may be needed for theft, injury, or other applicable incidents.', appliesWhen: 'injury, theft, or third-party damage' },
  { id: 'kyc', label: 'KYC, PAN, and bank details', status: 'insurer_specific' as const, why: 'The insurer may request these for identity or payment processing.' },
];

const path = (
  id: ClaimPath['id'],
  title: string,
  whenThisApplies: string,
  steps: string[],
  extra: ClaimPath['checklist'] = [],
  cautions: string[] = [],
): ClaimPath => ({
  id,
  title,
  whenThisApplies,
  steps,
  checklist: [...commonChecklist, ...extra],
  cautions,
});

export const claimGuide: ClaimGuide = {
  lastVerified: '2026-10-31',
  sources: [
    { label: 'Motor Vehicles Act — India Code', url: 'https://www.indiacode.nic.in/' },
    { label: 'SBI General', url: 'https://www.sbigeneral.in/' },
    { label: 'IFFCO-Tokio', url: 'https://www.iffcotokio.co.in/' },
    { label: 'ICICI Lombard', url: 'https://www.icicilombard.com/' },
    { label: 'IRDAI Bima Bharosa', url: 'https://bimabharosa.irdai.gov.in/' },
    { label: 'Council for Insurance Ombudsmen', url: 'https://www.cioins.co.in/' },
  ],
  trackerStates: [
    'Accident recorded', 'Evidence saved', 'Claim path selected',
    'Insurer notified (user-confirmed)', 'Claim reference saved',
    'Survey/inspection', 'Documents submitted', 'Repair/assessment',
    'Settlement pending', 'Settled/Disputed/Rejected',
  ],
  paths: [
    path('own_damage', 'Own damage', 'Damage to your vehicle where your policy may cover own damage.', [
      'Record the scene safely and preserve photos, documents, and factual notes.',
      'Check your policy wording and contact your insurer using its official channel.',
      'Ask the insurer about survey requirements before repair or dismantling.',
    ], [], ['A third-party-only policy does not pay for the owner’s own vehicle damage.', 'A number-plate photo can help in a third-party collision but is not required for every own-damage claim.']),
    path('cashless_repair', 'Cashless repair', 'You want to ask the insurer whether an approved network workshop can handle the repair.', [
      'Ask the insurer for an approved workshop and survey instructions.',
      'Confirm deductibles, depreciation, consumables, and any non-approved work before authorising repairs.',
      'Keep the repair estimate, survey outcome, and invoices.',
    ], [{ id: 'estimate', label: 'Repair estimate', status: 'insurer_specific', why: 'The insurer or workshop may need an estimate before approval.' }], ['Cashless does not mean zero payment.']),
    path('reimbursement_repair', 'Reimbursement repair', 'You may use a workshop and seek reimbursement subject to policy terms.', [
      'Ask the insurer whether the proposed workshop and repair process are acceptable.',
      'Keep original estimates, invoices, payment proof, and replaced-part records.',
      'Submit the documents requested by the insurer and retain copies.',
    ], [{ id: 'invoices', label: 'Original invoices and payment proof', status: 'core', why: 'They support the amount you are asking the insurer to assess.' }]),
    path('third_party_property', 'Third-party property', 'Another person’s vehicle or property was damaged.', [
      'Prioritise safety and exchange details only when safe.',
      'Preserve photos, witness details, and the other vehicle information without guessing.',
      'Notify your own insurer and forward any legal notice promptly.',
    ], [{ id: 'other_vehicle', label: 'Other vehicle or property details', status: 'conditional', why: 'They help identify the third-party damage claim.', appliesWhen: 'another vehicle or property is involved' }], ['Do not admit liability, promise compensation, or privately settle a third-party claim.']),
    path('third_party_injury_death', 'Third-party injury or death', 'A third party may have been injured or killed.', [
      'Seek urgent care and contact the competent emergency and police services.',
      'Notify your own insurer and preserve all notices and records.',
      'Forward legal notices or summons to the insurer promptly.',
    ], [{ id: 'medical', label: 'Medical or police records', status: 'conditional', why: 'They may be relevant to injury or death proceedings.', appliesWhen: 'third-party injury or death' }], ['This checklist does not replace a lawyer, police process, or insurer.']),
    path('theft', 'Theft', 'The vehicle is missing or stolen.', [
      'Report the theft to police first and obtain the relevant record.',
      'Notify the insurer and financier if the vehicle is financed; ask about RTO intimation and the current required list.',
      'Keep keys, purchase invoice, RC, and all correspondence available.',
    ], [
      { id: 'keys', label: 'All available vehicle keys', status: 'core', why: 'The insurer may request them for theft assessment.' },
      { id: 'invoice', label: 'Vehicle purchase invoice', status: 'conditional', why: 'It may support the vehicle and ownership record.', appliesWhen: 'theft claim' },
      { id: 'financier', label: 'Financier NOC or finance details', status: 'conditional', why: 'A financier may have an interest in the vehicle.', appliesWhen: 'vehicle is financed' },
    ]),
    path('total_loss', 'Total loss', 'Damage may be beyond economical repair or the vehicle may be treated as a total loss.', [
      'Preserve the vehicle and ask the insurer about survey and assessment.',
      'Review the policy wording and IDV with the insurer.',
      'Keep assessment, salvage, finance, and settlement correspondence.',
    ], [], ['One insurer describes constructive total loss as repair cost above 75% of IDV; check your policy wording.']),
    path('addons_roadside', 'Add-ons and roadside help', 'You want to check roadside assistance or add-on coverage.', [
      'Check the policy schedule for zero depreciation, engine protect, RSA, consumables, or personal accident cover.',
      'Ask the insurer which conditions and exclusions apply.',
      'Keep service records and receipts for any authorised assistance.',
    ], [{ id: 'addon_schedule', label: 'Policy schedule and add-on wording', status: 'insurer_specific', why: 'Add-on availability and conditions vary by policy.' }]),
    path('hit_and_run', 'Hit and run', 'The other vehicle is unidentified after a collision.', [
      'Prioritise safety and report the incident through the appropriate police process.',
      'Preserve available photos, witness details, and any partial registration information.',
      'Ask the insurer and competent authority about the available routes.',
    ], [{ id: 'witnesses', label: 'Witness details or CCTV leads', status: 'conditional', why: 'They may help identify the vehicle or event.', appliesWhen: 'available' }], ['An unidentified vehicle does not automatically make repairs reimbursable. Statutory hit-and-run compensation is a separate route; ask the competent authority about current eligibility.']),
    path('not_sure', 'Not sure', 'You are unsure which claim path fits.', [
      'Use the quick questions in this guide to narrow the situation.',
      'Preserve evidence and contact your own insurer through its official channel.',
      'Ask the insurer which claim path and documents apply.',
    ]),
  ],
};
