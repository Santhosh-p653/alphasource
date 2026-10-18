"""Tamil Nadu Government Scheme Eligibility Gate tools.

Two real schemes with accurate data, plus supporting mock data for districts,
documents and application centres. All data is in-memory so the demo runs
anywhere without external services.

Real data sources:
  - PM Kisan Samman Nidhi: https://pmkisan.gov.in
  - Kalaignar Magalir Urimai Thogai: https://cms.tn.gov.in
"""

from __future__ import annotations

from strands import tool

# ---------------------------------------------------------------------------
# Real scheme data
# ---------------------------------------------------------------------------

SCHEMES: dict[str, dict] = {
    "pm_kisan": {
        "name": "PM Kisan Samman Nidhi",
        "category": "agriculture",
        "government": "Central Government",
        "benefit": "Rs 6,000 per year (Rs 2,000 every 4 months) directly into Aadhaar-linked bank account",
        "eligibility": {
            "who": "Small and marginal farmer families who own cultivable land",
            "land_limit": "Must own cultivable land (no upper limit removed in 2019; originally up to 2 hectares)",
            "income": "No income ceiling after 2019 revision",
            "excluded": [
                "Institutional land holders",
                "Former or current holders of constitutional posts",
                "Former or serving central or state government employees (except Group D / multi-tasking staff)",
                "Professionals such as doctors, engineers, lawyers, chartered accountants registered with professional bodies",
                "Persons who paid income tax in the last assessment year",
                "Pensioners drawing Rs 10,000 or more per month (excluding multi-tasking staff)",
            ],
            "state": "All states including Tamil Nadu",
            "residence": "Must be Indian citizen with valid Aadhaar",
        },
        "documents_required": [
            "Aadhaar card",
            "Bank passbook (Aadhaar-linked account)",
            "Land ownership documents (patta, chitta)",
            "Mobile number linked to Aadhaar",
        ],
        "how_to_apply": "Visit pmkisan.gov.in, click 'Farmer Corner' > 'New Farmer Registration'. "
                        "Or visit the nearest Common Service Centre (CSC) or Krishi Vigyan Kendra.",
        "helpline": "PM-Kisan Helpline: 155261 / 1800115526 (toll-free)",
        "language_note": "பிரதமர் கிசான் திட்டம் - ஆண்டுக்கு ரூ.6,000 நேரடியாக வங்கிக் கணக்கில் வரவு வைக்கப்படும்.",
    },

    "magalir_urimai": {
        "name": "Kalaignar Magalir Urimai Thogai",
        "category": "women_welfare",
        "government": "Tamil Nadu State Government",
        "benefit": "Rs 1,000 per month (Rs 12,000 per year) deposited directly into the woman's bank account",
        "eligibility": {
            "who": "Women who are heads of household in Tamil Nadu",
            "age": "21 years and above",
            "residence": "Must be a resident of Tamil Nadu with a valid ration card",
            "aadhaar": "Must have an Aadhaar card linked to a bank account",
            "ration_card": "Must be listed as head of family in the ration card",
            "excluded": [
                "Women who are government employees or pensioners",
                "Women whose family income exceeds Rs 2.5 lakh per year",
                "Women who pay income tax",
                "Women who own four-wheelers (other than auto-rickshaws used for livelihood)",
                "Women who own more than 5 acres of wetland or 10 acres of dry land",
            ],
        },
        "documents_required": [
            "Aadhaar card",
            "Ration card (with name as head of family)",
            "Bank passbook (Aadhaar-linked, in applicant's name)",
            "Mobile number",
            "Voter ID or other address proof",
        ],
        "how_to_apply": "Apply online at https://magalirthogai.tn.gov.in or visit the nearest "
                        "Taluk office, Ration shop, or Common Service Centre (CSC) in Tamil Nadu.",
        "helpline": "Tamil Nadu Helpline: 14545 or 1800-425-0082 (toll-free)",
        "language_note": "கலைஞர் மகளிர் உரிமைத்தொகை - ஒவ்வொரு மாதமும் ரூ.1,000 நேரடியாக வங்கிக் கணக்கில் வரவு வைக்கப்படும். குடும்ப அட்டையில் குடும்பத்தலைவியாக இருக்க வேண்டும்.",
    },
}

# ---------------------------------------------------------------------------
# Supporting mock data
# ---------------------------------------------------------------------------

TN_DISTRICTS = [
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
    "Tirunelveli", "Vellore", "Erode", "Thoothukudi", "Dindigul",
    "Thanjavur", "Ranipet", "Sivaganga", "Virudhunagar", "Namakkal",
    "Cuddalore", "Kancheepuram", "Nilgiris", "Pudukkottai", "Ramanathapuram",
]

SCHEME_CATEGORIES = {
    "agriculture": ["pm_kisan"],
    "women_welfare": ["magalir_urimai"],
    "ration_food": [],   # placeholder for TNPDS (mock)
    "education_youth": [],  # placeholder for Chief Minister's Breakfast Scheme (mock)
    "housing_infrastructure": [],  # placeholder for PMAY (mock)
}

APPLICATION_CENTRES = {
    "Chennai": ["CSC at Anna Nagar, Adyar, T.Nagar, Tambaram", "Collectorate, Rajaji Salai"],
    "Madurai": ["CSC at Goripalayam, Anna Nagar, KK Nagar", "Collectorate, North Veli Street"],
    "Coimbatore": ["CSC at RS Puram, Gandhipuram, Singanallur", "Collectorate, Race Course Road"],
    "Tiruchirappalli": ["CSC at Srirangam, Ariyamangalam", "Collectorate, Collector Office Road"],
    "Thanjavur": ["CSC at Old Bus Stand, Medical College Road", "Collectorate, Palace Road"],
}

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def list_schemes(category: str = "") -> dict:
    """List available government schemes, optionally filtered by category.

    Categories: agriculture, women_welfare, ration_food, education_youth, housing_infrastructure.
    Leave category empty to list all schemes.
    """
    cat = category.lower().strip()
    if cat and cat not in SCHEME_CATEGORIES:
        return {
            "error": f"Unknown category '{cat}'.",
            "available_categories": list(SCHEME_CATEGORIES.keys()),
        }
    results = {}
    scheme_ids = SCHEME_CATEGORIES.get(cat, []) if cat else [sid for ids in SCHEME_CATEGORIES.values() for sid in ids]
    for sid in scheme_ids:
        s = SCHEMES[sid]
        results[sid] = {
            "name": s["name"],
            "category": s["category"],
            "government": s["government"],
            "benefit": s["benefit"],
        }
    return {"category": cat or "all", "schemes": results, "count": len(results)}


@tool
def get_scheme_details(scheme_id: str) -> dict:
    """Get full details of a scheme including eligibility, documents and how to apply.

    Scheme IDs: pm_kisan, magalir_urimai.
    """
    s = SCHEMES.get(scheme_id.lower().strip())
    if not s:
        return {
            "error": f"No scheme with id '{scheme_id}'.",
            "available": list(SCHEMES.keys()),
        }
    return {"scheme_id": scheme_id, **s}


@tool
def check_eligibility(scheme_id: str, profile: dict) -> dict:
    """Check whether a citizen profile meets the eligibility criteria for a scheme.

    scheme_id: pm_kisan or magalir_urimai.
    profile: dict with keys such as 'is_farmer', 'land_acres', 'gender', 'age',
             'is_govt_employee', 'annual_income', 'has_aadhaar', 'has_ration_card',
             'is_head_of_family', 'state', 'owns_car'.
    Returns eligible (bool), reasons (list), and missing_info (list of fields not provided).
    """
    s = SCHEMES.get(scheme_id.lower().strip())
    if not s:
        return {"error": f"No scheme '{scheme_id}'. Use list_schemes to find valid ids."}

    reasons: list[str] = []
    missing: list[str] = []
    eligible = True

    if scheme_id == "pm_kisan":
        if not profile.get("is_farmer"):
            eligible = False
            reasons.append("Must be a farmer who owns cultivable land.")
        if profile.get("is_govt_employee"):
            eligible = False
            reasons.append("Government employees (above Group D) are excluded.")
        if profile.get("annual_income") and profile["annual_income"] > 0:
            if profile.get("pays_income_tax"):
                eligible = False
                reasons.append("Persons who paid income tax in the last assessment year are excluded.")
        if not profile.get("has_aadhaar"):
            missing.append("has_aadhaar")
        if not profile.get("has_bank_account"):
            missing.append("has_bank_account (Aadhaar-linked)")

    elif scheme_id == "magalir_urimai":
        if profile.get("gender", "").lower() not in ("female", "woman", "f"):
            eligible = False
            reasons.append("Scheme is for women only.")
        if profile.get("age") and int(profile["age"]) < 21:
            eligible = False
            reasons.append("Applicant must be 21 years or older.")
        if profile.get("state", "").lower() not in ("tamil nadu", "tn", "tamilnadu"):
            eligible = False
            reasons.append("Scheme is only for Tamil Nadu residents.")
        if profile.get("is_govt_employee"):
            eligible = False
            reasons.append("Government employees and pensioners are excluded.")
        if profile.get("annual_income") and int(profile["annual_income"]) > 250000:
            eligible = False
            reasons.append("Family income must not exceed Rs 2.5 lakh per year.")
        if profile.get("owns_car"):
            eligible = False
            reasons.append("Women who own four-wheelers (other than autos for livelihood) are excluded.")
        if not profile.get("is_head_of_family"):
            eligible = False
            reasons.append("Applicant must be listed as head of family in the ration card.")
        if not profile.get("has_aadhaar"):
            missing.append("has_aadhaar")
        if not profile.get("has_ration_card"):
            missing.append("has_ration_card")

    if eligible and not reasons:
        reasons.append("Profile meets all known eligibility criteria.")

    return {
        "scheme_id": scheme_id,
        "scheme_name": s["name"],
        "eligible": eligible,
        "reasons": reasons,
        "missing_info": missing,
        "note": "This is an indicative check based on the information provided. "
                "Final eligibility is determined by the concerned government authority.",
    }


@tool
def get_required_documents(scheme_id: str) -> dict:
    """List the documents required to apply for a scheme."""
    s = SCHEMES.get(scheme_id.lower().strip())
    if not s:
        return {"error": f"No scheme '{scheme_id}'."}
    return {
        "scheme_id": scheme_id,
        "scheme_name": s["name"],
        "documents": s["documents_required"],
        "how_to_apply": s["how_to_apply"],
        "helpline": s["helpline"],
    }


@tool
def find_application_centres(district: str) -> dict:
    """Find Common Service Centres and government offices where citizens can apply for schemes.

    District must be a Tamil Nadu district name (e.g. Madurai, Coimbatore, Chennai).
    """
    d = district.strip().title()
    centres = APPLICATION_CENTRES.get(d)
    if not centres:
        return {
            "district": district,
            "note": f"Specific centres for {district} are not in the mock database. "
                    "Visit https://locator.csccloud.in to find your nearest CSC, "
                    "or contact the district Collectorate.",
            "known_districts": list(APPLICATION_CENTRES.keys()),
        }
    return {
        "district": d,
        "centres": centres,
        "note": "Call ahead to confirm opening hours. Bring original documents and photocopies.",
    }


@tool
def translate_scheme_summary(scheme_id: str, language: str = "tamil") -> dict:
    """Get a brief scheme summary in Tamil or English.

    scheme_id: pm_kisan or magalir_urimai.
    language: 'tamil' or 'english'.
    """
    s = SCHEMES.get(scheme_id.lower().strip())
    if not s:
        return {"error": f"No scheme '{scheme_id}'."}
    if language.lower() in ("tamil", "ta"):
        return {
            "scheme_id": scheme_id,
            "language": "tamil",
            "summary": s.get("language_note", "தமிழ் சுருக்கம் கிடைக்கவில்லை."),
            "benefit": s["benefit"],
        }
    return {
        "scheme_id": scheme_id,
        "language": "english",
        "summary": f"{s['name']} — {s['benefit']}",
        "eligibility_short": s["eligibility"].get("who", ""),
    }


TOOLS = [
    list_schemes,
    get_scheme_details,
    check_eligibility,
    get_required_documents,
    find_application_centres,
    translate_scheme_summary,
]
