from typing import List, Dict, Set

INFECTIOUS_KEYWORDS: Set[str] = {
    "flu", "influenza", "covid", "sars-cov-2", "measles", "rubeola",
    "dengue", "tb", "tuberculosis", "malaria", "chikungunya"
}

SYMPTOM_POINTS = {
    "fever": 20,
    "cough": 10,
    "fatigue": 5,
    "rash": 15,
    "breathlessness": 25,
    "sore_throat": 10,
    "body_ache": 8,
    "headache": 8,
}

CHRONIC_POINTS = {
    "diabetes_uncontrolled": 15,
    "hypertension": 10,
    "asthma": 10,
    "copd": 15,
    "ckd": 20,
}

MED_FLAGS = {"azithromycin", "amoxicillin", "paracetamol", "acetaminophen", "ibuprofen"}


def _clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))


def _classify(score: int) -> str:
    if score <= 20:
        return "Healthy"
    if score <= 50:
        return "Moderate"
    return "High-Risk"


def score_worker(
    symptoms: List[str],
    chronic_conditions: List[str],
    vaccinated: bool,
    extracted_text: str,
) -> Dict[str, object]:
    score = 0

    for s in symptoms or []:
        score += SYMPTOM_POINTS.get((s or "").strip().lower(), 0)

    for c in chronic_conditions or []:
        key = (c or "").strip().lower()
        if "diabetes" in key and "controlled" not in key:
            score += CHRONIC_POINTS["diabetes_uncontrolled"]
        score += CHRONIC_POINTS.get(key, 0)

    text = (extracted_text or "").lower()
    inf_hits = {k for k in INFECTIOUS_KEYWORDS if k in text}
    if inf_hits:
        score += min(40, 25 * len(inf_hits))

    if any(m in text for m in MED_FLAGS) and not inf_hits:
        score += 10

    if vaccinated:
        score -= 10

    score = _clamp(score)
    return {
        "score": score,
        "bucket": _classify(score),
        "infectious_hits": sorted(list(inf_hits)),
    }


