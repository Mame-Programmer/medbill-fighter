"""Small reference tables used by the rule-based checks.

Keep these conservative. Every flag produced from them is a *question to ask
the provider or insurer*, never a claim that a bill is wrong.
"""

# Claim Adjustment Reason Codes (CARC) that commonly appear on denials (EOBs / remittances).
DENIAL_CODES = {
    "16": {
        "meaning": "Claim lacks information or has a submission/billing error.",
        "action": "Ask the provider's billing office what was missing and have them resubmit a corrected claim.",
    },
    "18": {
        "meaning": "Exact duplicate claim or service.",
        "action": "Confirm whether you were charged twice. If the service was only done once, dispute the duplicate.",
    },
    "29": {
        "meaning": "The time limit for filing the claim has expired.",
        "action": "Ask the provider to show proof of timely filing; providers often cannot bill you for their own late filing.",
    },
    "50": {
        "meaning": "Not deemed medically necessary by the payer.",
        "action": "Request the clinical criteria used, ask your doctor for a letter of medical necessity, and file an appeal.",
    },
    "96": {
        "meaning": "Non-covered charge(s).",
        "action": "Compare against your plan documents (Summary of Benefits). Appeal if the service should be covered.",
    },
    "97": {
        "meaning": "Payment is included in the allowance for another service already paid (bundled).",
        "action": "Ask whether the service was correctly bundled or whether a modifier should have been used.",
    },
    "197": {
        "meaning": "Precertification / prior authorization was absent.",
        "action": "Ask who was responsible for the authorization. Request a retro-authorization if the care was urgent.",
    },
    "204": {
        "meaning": "Service not covered under the patient's current benefit plan.",
        "action": "Verify your plan's covered benefits and ask for the specific plan provision that excludes it.",
    },
}

# An aggregate (panel) code and the component codes it already includes.
# Billing the components separately on the same date of service is a classic unbundling flag.
BUNDLES = {
    "80053": {
        "name": "Comprehensive metabolic panel",
        "components": {
            "82947": "Glucose", "82565": "Creatinine", "84132": "Potassium",
            "84295": "Sodium", "82310": "Calcium", "82435": "Chloride",
            "82374": "CO2", "84520": "BUN", "82040": "Albumin",
            "82247": "Bilirubin, total", "84075": "Alkaline phosphatase",
            "84460": "ALT", "84450": "AST", "84155": "Total protein",
        },
    },
    "85025": {
        "name": "CBC with automated differential",
        "components": {"85027": "CBC without differential"},
    },
}

# Evaluation & management office-visit codes: more than one on the same date is unusual.
EM_CODES = {"99202", "99203", "99204", "99205", "99211", "99212", "99213", "99214", "99215"}

# Charges above this get an "ask for itemized justification" note.
HIGH_CHARGE_THRESHOLD = 1000.00
