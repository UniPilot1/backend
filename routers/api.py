"""
UniPilot — API Routers
All endpoints for matching, profile evaluation, gap analysis, roadmap, AI insights.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
from typing import List

from schemas.models import (
    MatchingRequest, MatchingResponse,
    ProfileEvaluationResponse, DimensionScore,
    GapAnalysisRequest, GapAnalysisResponse, GapItem,
    AIInsightRequest, AIInsightResponse,
    StudentProfile,
)
from services.matching_service import (
    run_matching_engine, compute_dimension_scores,
    _research_target, _leadership_target,
)
from services import gemini_service

# ── Matching ───────────────────────────────────────────────────────────────────
matching_router = APIRouter(prefix="/match", tags=["University Matching"])

@matching_router.post("/", response_model=MatchingResponse)
async def match_universities(req: MatchingRequest):
    """
    Core matching engine endpoint.
    Classifies all universities as Reach / Target / Likely for this student profile.
    """
    try:
        result = run_matching_engine(
            profile=req.profile,
            preferred_countries=req.preferredCountries or req.profile.preferredCountries,
            budget_max=req.budgetMax,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Profile Evaluation ─────────────────────────────────────────────────────────
profile_router = APIRouter(prefix="/profile", tags=["Profile Evaluation"])

DIMENSION_META = {
    "academics":     {"label": "Academics",      "tip": "Maintain upward grade trend; take the most rigorous courses."},
    "testing":       {"label": "Testing",        "tip": "A score above 1520 SAT eliminates testing as a differentiator."},
    "research":      {"label": "Research",       "tip": "A published paper or formal lab experience has outsized admissions impact."},
    "leadership":    {"label": "Leadership",     "tip": "Found or lead a club, project, or community initiative."},
    "techPortfolio": {"label": "Tech portfolio", "tip": "Document projects on GitHub with clear problem statements and impact metrics."},
    "community":     {"label": "Community",      "tip": "Sustained volunteering over 12+ months reads better than multiple short stints."},
    "initiative":    {"label": "Initiative",     "tip": "Starting something signals ownership — a startup, open-source project, or newsletter."},
}

SCORE_WEIGHTS = dict(
    academics=0.25, testing=0.20, research=0.18,
    leadership=0.12, techPortfolio=0.10, community=0.08, initiative=0.07,
)

def _level(score: float) -> str:
    if score >= 9:   return "Exceptional"
    if score >= 7.5: return "Strong"
    if score >= 6:   return "Above Average"
    if score >= 4.5: return "Average"
    if score >= 3:   return "Below Average"
    return "Weak"


@profile_router.post("/evaluate", response_model=ProfileEvaluationResponse)
async def evaluate_profile(profile: StudentProfile):
    """
    Score a student profile across 7 dimensions and return AI narrative.
    """
    dims = compute_dimension_scores(profile)

    dimensions = [
        DimensionScore(
            key=k,
            label=DIMENSION_META[k]["label"],
            score=v,
            level=_level(v),
            explanation=f"Score: {v}/10 — {_level(v)}",
            improvementTip=DIMENSION_META[k]["tip"],
        )
        for k, v in dims.items()
    ]

    overall = round(sum(dims[k] * SCORE_WEIGHTS[k] for k in dims), 1)
    sorted_dims = sorted(dims.items(), key=lambda x: -x[1])
    strengths  = [DIMENSION_META[k]["label"] for k, _ in sorted_dims[:3]]
    weaknesses = [DIMENSION_META[k]["label"] for k, _ in sorted_dims[-3:]]

    # AI narrative (Gemini)
    ai_data = await gemini_service.generate_profile_narrative(profile, dims)

    return ProfileEvaluationResponse(
        overallScore=overall,
        dimensions=dimensions,
        strengths=strengths,
        weaknesses=weaknesses,
        opportunities=ai_data.get("opportunities", []),
        aiNarrative=ai_data.get("narrative", ""),
    )


# ── Gap Analysis ───────────────────────────────────────────────────────────────
gap_router = APIRouter(prefix="/gap", tags=["Gap Analysis"])

# Benchmark data for each university (typical admitted student profile)
BENCHMARKS = {
    "mit":       dict(academics=9.5, testing=9.2, research=8.0, leadership=7.5, techPortfolio=8.0, community=7.0),
    "stanford":  dict(academics=9.4, testing=9.1, research=7.8, leadership=8.0, techPortfolio=7.5, community=7.5),
    "cmu":       dict(academics=8.8, testing=8.5, research=7.0, leadership=6.5, techPortfolio=8.5, community=6.0),
    "gatech":    dict(academics=8.2, testing=8.0, research=5.5, leadership=6.0, techPortfolio=7.5, community=5.5),
    "imperial":  dict(academics=8.8, testing=8.3, research=6.5, leadership=6.0, techPortfolio=7.0, community=5.5),
    "waterloo":  dict(academics=7.5, testing=7.0, research=4.5, leadership=5.0, techPortfolio=7.0, community=5.0),
    "nus":       dict(academics=8.5, testing=8.2, research=6.5, leadership=6.5, techPortfolio=7.0, community=6.0),
    "toronto":   dict(academics=8.0, testing=7.8, research=5.5, leadership=6.0, techPortfolio=6.5, community=6.0),
    "tum":       dict(academics=8.0, testing=7.5, research=6.0, leadership=5.5, techPortfolio=6.5, community=5.5),
}

UNI_NAMES = {
    "mit": "MIT", "stanford": "Stanford", "cmu": "Carnegie Mellon",
    "gatech": "Georgia Tech", "imperial": "Imperial College London",
    "waterloo": "University of Waterloo", "nus": "NUS Singapore",
    "toronto": "University of Toronto", "tum": "TU Munich",
}

@gap_router.post("/", response_model=GapAnalysisResponse)
async def gap_analysis(req: GapAnalysisRequest):
    """
    Compare student profile vs admitted-student benchmark for a specific university.
    """
    uni_id = req.universityId.lower()
    benchmark = BENCHMARKS.get(uni_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail=f"University '{uni_id}' not found in benchmark data.")

    dims = compute_dimension_scores(req.profile)
    uni_name = UNI_NAMES.get(uni_id, uni_id)

    label_map = dict(
        academics="Academics", testing="Testing", research="Research",
        leadership="Leadership", techPortfolio="Tech Portfolio", community="Community",
    )

    gaps: List[GapItem] = []
    for key, bench_val in benchmark.items():
        student_val = dims.get(key, 0.0)
        delta = student_val - bench_val
        severity = (
            "Positive"  if delta >= 0 else
            "Minor"     if delta >= -1 else
            "Moderate"  if delta >= -2.5 else
            "Critical"
        )
        gaps.append(GapItem(
            dimension=label_map.get(key, key),
            studentValue=student_val,
            benchmarkValue=bench_val,
            delta=round(delta, 1),
            severity=severity,
        ))

    strengths  = sorted([g for g in gaps if g.delta >= 0], key=lambda x: -x.delta)
    weaknesses = sorted([g for g in gaps if g.delta < 0],  key=lambda x:  x.delta)
    top_gaps   = weaknesses[:3]

    # Admission likelihood: weighted average of (student/benchmark) ratios
    likelihood = round(min(99, sum(
        min(1.0, dims.get(k, 0) / v) * SCORE_WEIGHTS.get(k, 0.1) * 100
        for k, v in benchmark.items()
    )), 1)

    # AI recommendations
    ai_data = await gemini_service.generate_gap_analysis_narrative(
        req.profile, uni_name, [g.model_dump() for g in gaps]
    )

    return GapAnalysisResponse(
        universityId=uni_id,
        universityName=uni_name,
        strengths=strengths,
        weaknesses=weaknesses,
        topGaps=top_gaps,
        admissionLikelihood=likelihood,
        keyInsight=ai_data.get("keyInsight", ""),
        aiRecommendations=ai_data.get("recommendations", []),
    )


# ── AI Insights ────────────────────────────────────────────────────────────────
ai_router = APIRouter(prefix="/ai", tags=["AI Insights"])

@ai_router.post("/insight", response_model=AIInsightResponse)
async def get_ai_insight(req: AIInsightRequest):
    """
    Generate a personalised AI coaching insight for the student.
    """
    dims = compute_dimension_scores(req.profile)
    ai_data = await gemini_service.generate_ai_insight(
        req.profile, dims, req.focusTopic
    )
    return AIInsightResponse(
        insight=ai_data.get("insight", ""),
        actionItems=ai_data.get("actionItems", []),
        generatedAt=datetime.utcnow().isoformat(),
    )


@ai_router.post("/roadmap")
async def generate_roadmap(profile: StudentProfile, months: int = 6):
    """
    Generate a personalised month-by-month admissions roadmap.
    """
    target_unis = profile.careerGoals.dreamUniversities or ["Top CS schools"]
    roadmap = await gemini_service.generate_roadmap(profile, target_unis, months)
    return {"roadmap": roadmap, "generatedAt": datetime.utcnow().isoformat()}
