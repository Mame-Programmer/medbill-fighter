# MedBill Fighter: business plan and 10-day validation

## The problem
Medical bills and insurance denials are confusing, high-stakes, and often wrong or appealable. Most people pay or give up. They will pay for help when the saving is clear.

## Customer
US individuals and families holding a bill or denial worth at least a few hundred dollars. Secondary: small clinics and advocates who help patients.

## Offer and pricing (test, don't assume)
| Plan | Price | Includes |
|---|---|---|
| Free check | $0 | Findings only (lead magnet) |
| Case | $29-49 one time | Findings + dispute letter + checklist of next steps |
| Success option | 15-25% of confirmed savings | For large bills, billed only if money is saved |
| Pro | $99-199 / mo | For advocates and small practices: multiple cases, templates |

## Compliance guardrails (important)
- Position as an information and document-drafting tool, never legal, medical, or tax advice. Keep the disclaimer visible.
- Check state rules before charging a percentage of savings: some states regulate medical billing advocacy, public adjusters, or unauthorized practice of law.
- Users upload sensitive health information. Publish a clear privacy policy, minimize retention, encrypt in transit and at rest, and consult a lawyer about HIPAA applicability before partnering with any provider or insurer. Consumer-direct use is generally different from covered-entity use, but verify.
- Have a lawyer review the letter templates and terms of service before charging.

## 10-day validation plan
1. Day 1-2: Deploy this app (free tier host) and add a landing page with an email capture and the line "Upload your bill, see what to question."
2. Day 2-4: Post helpful, non-spammy answers in communities where people ask about surprise bills and denials (Reddit r/medicalbill style communities, local Facebook groups). Offer a free manual review to 10 people.
3. Day 4-8: Review each bill yourself using the tool. Record: what it caught, what it missed, how much the person could save.
4. Day 8-10: Offer a paid case ($29-49) to the people who got value. Goal: first 3 paying customers, or clear reasons why not.

## Success metrics
- 10 reviewed bills, at least 5 with a plausible finding
- 3 paid cases
- At least 1 documented saving you can turn into a (permissioned) case study

## Risks
- False positives erode trust: keep rules conservative, phrase as questions
- Rules cover a small slice of billing errors: expand with real bills and measure precision
- Distribution is the hard part, not code: spend most of your time talking to users
- Regulated area: get legal review early

## Later: how this becomes a bigger company
Case data (de-identified, with consent) reveals which providers and codes cause the most disputes. That supports a B2B product for employers, benefits platforms, and health plans, plus a patient-advocate marketplace.
