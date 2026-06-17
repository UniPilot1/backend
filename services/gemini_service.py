"""
UniPilot — AI Service
Wraps Google Gemini for profile analysis, roadmap generation, gap analysis.
Falls back gracefully if the API key is not set.
"""
import os
import json
import re
from typing import List, Dict, Any, Optional
from schemas.models import StudentProfile

_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

try:
    import google.generativeai as genai
    genai.configure(api_key=_GEMINI_KEY)
    _MODEL = genai.GenerativeModel(_MODEL_NAME)
    _GEMINI_AVAILABLE = bool(_GEMINI_KEY)
except ImportError:
    _MODEL = None
    _GEMINI_AVAILABLE = False


def _load_json_response(text: str) -> Any:
    cleaned = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(1))


def _profile_summary(profile: StudentProfile) -> str:
    ecs = "\n".join(
        f"  - {e.category}: {e.title} ({e.leadershipLevel}, {e.duration}, impact: {e.impact})"
        for e in profile.extracurriculars
    )
    return f"""Student: {profile.name} ({profile.country})
Intake: {profile.intakeYear} | Major: {profile.intendedMajor}
GPA: {profile.academics.gpa}/4.0 ({profile.academics.percentage}%)
Curriculum: {profile.academics.curriculum}
SAT: {profile.testScores.sat or "N/A"} | IELTS: {profile.testScores.ielts or "N/A"}
Extracurriculars:
{ecs or "  None listed"}
Dream universities: {", ".join(profile.careerGoals.dreamUniversities) or "None specified"}
Target countries: {", ".join(profile.preferredCountries) or "Any"}
Financial aid needed: {profile.careerGoals.financialAidRequired}""".strip()


async def generate_profile_narrative(
    profile: StudentProfile,
    dimension_scores: Dict[str, float],
) -> Dict[str, Any]:
    if not _GEMINI_AVAILABLE or _MODEL is None:
        return {
            "narrative": f"{profile.name} has solid academic foundations (GPA {profile.academics.gpa}/4.0) and a growing technical portfolio. Research and leadership are the highest-ROI gaps to address before applications.",
            "strengths": ["Academics", "Testing", "Tech Portfolio"],
            "weaknesses": ["Research", "Leadership"],
            "opportunities": ["Secure a research internship", "Take on a leadership role", "Ship an open-source project"],
            "keyMessage": "Focus on research first — it unlocks the most selective schools.",
        }
    prompt = f"""You are UniPilot, an expert university admissions strategist.
Analyse this student profile and provide honest, specific, actionable feedback.

PROFILE:
{_profile_summary(profile)}

COMPUTED DIMENSION SCORES (0–10):
{json.dumps(dimension_scores, indent=2)}

Respond in strict JSON:
{{
  "narrative": "<2–3 sentence overall evaluation — specific, not generic>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"],
  "opportunities": ["<specific action 1>", "<specific action 2>", "<specific action 3>"],
  "keyMessage": "<single most important thing this student should do in the next 30 days>"
}}
Return only valid JSON, no markdown fences."""
    try:
        resp = await _MODEL.generate_content_async(prompt)
        return _load_json_response(resp.text)
    except Exception:
        return {"narrative": "Profile analysis unavailable. Please retry.", "strengths": [], "weaknesses": [], "opportunities": [], "keyMessage": ""}


async def generate_roadmap(
    profile: StudentProfile,
    target_universities: List[str],
    months_available: int = 6,
) -> List[Dict[str, Any]]:
    if not _GEMINI_AVAILABLE or _MODEL is None:
        return []
    prompt = f"""You are UniPilot's Roadmap Engine. Generate a {months_available}-month personalised admissions roadmap.

STUDENT PROFILE:
{_profile_summary(profile)}

TARGET UNIVERSITIES: {", ".join(target_universities) or "Top CS schools"}

Rules:
1. Each month must have 2–3 concrete, actionable tasks.
2. Each task must reference specific universities it benefits.
3. Prioritise the student's biggest gaps first.

Respond in strict JSON array — return only valid JSON, no markdown fences:
[
  {{
    "month": "Jul 2026",
    "tasks": [
      {{
        "title": "<specific task title>",
        "description": "<what to do exactly>",
        "why": "<why this helps admissions>",
        "category": "<Projects|Research|Leadership|Application|Test Prep|Essays>",
        "difficulty": "<Easy|Medium|Hard>",
        "estimatedHours": <number>,
        "profileGain": <0.1–0.8>,
        "universitiesImpacted": ["MIT", "Stanford"]
      }}
    ]
  }}
]"""
    try:
        resp = await _MODEL.generate_content_async(prompt)
        return _load_json_response(resp.text)
    except Exception:
        return []


async def generate_gap_analysis_narrative(
    profile: StudentProfile,
    university_name: str,
    gaps: List[Dict],
) -> Dict[str, Any]:
    if not _GEMINI_AVAILABLE or _MODEL is None:
        return {"keyInsight": "Gap analysis unavailable — set GEMINI_API_KEY in backend/.env.", "recommendations": [], "admissionProbabilityNarrative": ""}
    gap_summary = "\n".join(
        f"  {g['dimension']}: student={g['studentScore']:.1f}, required={g['requiredScore']:.1f}, gap={g['gap']:+.1f}"
        for g in gaps
    )
    prompt = f"""You are UniPilot's Gap Analysis Engine.

STUDENT: {_profile_summary(profile)}
UNIVERSITY: {university_name}

DIMENSION GAPS:
{gap_summary}

Respond in strict JSON (no markdown fences):
{{
  "keyInsight": "<1–2 sentence most important finding>",
  "recommendations": ["<action 1>", "<action 2>", "<action 3>", "<action 4>"],
  "admissionProbabilityNarrative": "<honest 1-sentence assessment>"
}}"""
    try:
        resp = await _MODEL.generate_content_async(prompt)
        return _load_json_response(resp.text)
    except Exception:
        return {"keyInsight": "Analysis unavailable.", "recommendations": [], "admissionProbabilityNarrative": ""}


async def generate_ai_insight(
    profile: StudentProfile,
    dimension_scores: Dict[str, float],
    focus_topic: Optional[str] = None,
) -> Dict[str, Any]:
    if not _GEMINI_AVAILABLE or _MODEL is None:
        top_gap = min(dimension_scores, key=lambda k: dimension_scores[k])
        return {
            "insight": f"Your profile has strong academic foundations. Improving {top_gap} is the single highest-ROI action before applications.",
            "actionItems": [
                f"Reach out to a professor for a {top_gap}-related research opportunity",
                "Take on a measurable leadership role in an existing club",
                "Start drafting your Common App main essay using the 'challenge → growth' arc",
            ],
        }
    focus = f"\nFocus topic: {focus_topic}" if focus_topic else ""
    prompt = f"""You are UniPilot's admissions coach.{focus}

STUDENT: {_profile_summary(profile)}
SCORES: {json.dumps(dimension_scores)}

Respond in strict JSON (no markdown fences):
{{
  "insight": "<2–3 sentence coaching message — reference specific numbers>",
  "actionItems": [
    "<immediate action — this week>",
    "<medium-term action — this month>",
    "<application strategy tip>"
  ]
}}"""
    try:
        resp = await _MODEL.generate_content_async(prompt)
        return _load_json_response(resp.text)
    except Exception:
        return {"insight": "Your profile has strong academic foundations. Focus on research and leadership to differentiate.", "actionItems": ["Reach out to a professor for a research opportunity", "Take a leadership role in an existing club", "Start drafting your Common App main essay"]}
