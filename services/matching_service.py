"""
UniPilot — University Matching Engine (Backend)
Pure Python scoring + classification logic that mirrors the frontend engine.
This is the authoritative server-side implementation.
"""
from __future__ import annotations
import math
from datetime import datetime, date
from typing import Dict, List, Tuple

from schemas.models import (
    StudentProfile, UniversityMatchOut, MatchingResponse,
    MatchReason, DimensionGap, MatchTier, Outlook,
)

# ── Static university data ─────────────────────────────────────────────────────
UNIVERSITIES = [
    dict(
        id="mit", name="Massachusetts Institute of Technology", shortName="MIT",
        country="United States", countryCode="US", city="Cambridge, MA",
        ranking=1, acceptanceRate=4.0, type="Private", researchOutput="Very High",
        tags=["STEM","Research","Tech","Top-3"],
        programs=[dict(
            id="mit-cs", name="Computer Science & Engineering", degree="BS",
            major="CS", tuitionUSD=59750, duration=4,
            deadlines=dict(earlyAction="2026-11-01", regularDecision="2027-01-01"),
            requirements=dict(minGPA=3.9, minSAT=1550, minACT=35, minIELTS=7.0, minTOEFL=100,
                              portfolioRequired=False, researchRequired=True),
            scholarships=[dict(id="mit-need", name="MIT Need-Based Aid",
                               amount=55000, currency="USD", eligibility=["Need-based"], renewable=True)],
        )],
    ),
    dict(
        id="stanford", name="Stanford University", shortName="Stanford",
        country="United States", countryCode="US", city="Stanford, CA",
        ranking=3, acceptanceRate=4.0, type="Private", researchOutput="Very High",
        tags=["STEM","Research","Entrepreneurship","Top-5"],
        programs=[dict(
            id="stanford-cs", name="Computer Science", degree="BS",
            major="CS", tuitionUSD=62484, duration=4,
            deadlines=dict(earlyAction="2026-11-01", regularDecision="2027-01-02"),
            requirements=dict(minGPA=3.9, minSAT=1540, minACT=35, minIELTS=7.0, minTOEFL=100,
                              portfolioRequired=False, researchRequired=True),
            scholarships=[dict(id="stanford-need", name="Stanford Financial Aid",
                               amount=58000, currency="USD", eligibility=["Need-based"], renewable=True)],
        )],
    ),
    dict(
        id="cmu", name="Carnegie Mellon University", shortName="CMU",
        country="United States", countryCode="US", city="Pittsburgh, PA",
        ranking=25, acceptanceRate=11.0, type="Private", researchOutput="Very High",
        tags=["CS","AI","Robotics","Tech"],
        programs=[dict(
            id="cmu-cs", name="Computer Science", degree="BS",
            major="CS", tuitionUSD=61344, duration=4,
            deadlines=dict(earlyDecision="2026-11-01", regularDecision="2027-01-01"),
            requirements=dict(minGPA=3.7, minSAT=1500, minACT=34, minIELTS=6.5, minTOEFL=90,
                              portfolioRequired=False, researchRequired=False),
            scholarships=[dict(id="cmu-merit", name="CMU Merit Scholarship",
                               amount=20000, currency="USD", eligibility=["Merit-based"], renewable=True)],
        )],
    ),
    dict(
        id="gatech", name="Georgia Institute of Technology", shortName="Georgia Tech",
        country="United States", countryCode="US", city="Atlanta, GA",
        ranking=33, acceptanceRate=17.0, type="Public", researchOutput="Very High",
        tags=["Engineering","CS","AI","Affordable"],
        programs=[dict(
            id="gatech-cs", name="Computer Science", degree="BS",
            major="CS", tuitionUSD=33794, duration=4,
            deadlines=dict(earlyAction="2026-10-15", regularDecision="2027-01-04"),
            requirements=dict(minGPA=3.6, minSAT=1420, minACT=32, minIELTS=6.5, minTOEFL=90,
                              portfolioRequired=False, researchRequired=False),
            scholarships=[dict(id="gt-intl", name="Georgia Tech International Award",
                               amount=10000, currency="USD", eligibility=["International"], renewable=True)],
        )],
    ),
    dict(
        id="imperial", name="Imperial College London", shortName="Imperial",
        country="United Kingdom", countryCode="GB", city="London",
        ranking=8, acceptanceRate=14.0, type="Public", researchOutput="Very High",
        tags=["Engineering","STEM","London","Top-10"],
        programs=[dict(
            id="imperial-cs", name="Computing", degree="BEng",
            major="CS", tuitionUSD=42500, duration=3,
            deadlines=dict(regularDecision="2027-01-15"),
            requirements=dict(minGPA=3.8, minSAT=1480, minACT=33, minIELTS=6.5, minTOEFL=92,
                              portfolioRequired=False, researchRequired=False),
            scholarships=[dict(id="imperial-intl", name="President's Scholarship",
                               amount=15000, currency="GBP", eligibility=["International","Merit"], renewable=False)],
        )],
    ),
    dict(
        id="waterloo", name="University of Waterloo", shortName="Waterloo",
        country="Canada", countryCode="CA", city="Waterloo, ON",
        ranking=149, acceptanceRate=53.0, type="Public", researchOutput="High",
        tags=["CS","Co-op","Affordable","Canada"],
        programs=[dict(
            id="waterloo-cs", name="Computer Science", degree="BSc",
            major="CS", tuitionUSD=36000, duration=4,
            deadlines=dict(regularDecision="2027-04-01"),
            requirements=dict(minGPA=3.5, minSAT=1350, minIELTS=6.5, minTOEFL=90,
                              portfolioRequired=False, researchRequired=False),
            scholarships=[dict(id="uwaterloo-merit", name="Waterloo Merit Scholarship",
                               amount=12000, currency="CAD", eligibility=["Merit"], renewable=False)],
        )],
    ),
    dict(
        id="nus", name="National University of Singapore", shortName="NUS",
        country="Singapore", countryCode="SG", city="Singapore",
        ranking=19, acceptanceRate=8.0, type="Public", researchOutput="Very High",
        tags=["Asia","Research","Affordable","Top-20"],
        programs=[dict(
            id="nus-cs", name="Computer Science", degree="BSc",
            major="CS", tuitionUSD=16000, duration=4,
            deadlines=dict(regularDecision="2027-03-01"),
            requirements=dict(minGPA=3.7, minSAT=1450, minIELTS=6.5, minTOEFL=85,
                              portfolioRequired=False, researchRequired=False),
            scholarships=[dict(id="nus-scholar", name="NUS Global Merit Scholarship",
                               amount=14000, currency="USD", eligibility=["International","Merit"], renewable=True)],
        )],
    ),
    dict(
        id="toronto", name="University of Toronto", shortName="U of T",
        country="Canada", countryCode="CA", city="Toronto, ON",
        ranking=25, acceptanceRate=43.0, type="Public", researchOutput="Very High",
        tags=["Research","Canada","CS","AI"],
        programs=[dict(
            id="uoft-cs", name="Computer Science", degree="BSc",
            major="CS", tuitionUSD=38000, duration=4,
            deadlines=dict(regularDecision="2027-01-13"),
            requirements=dict(minGPA=3.6, minSAT=1400, minIELTS=6.5, minTOEFL=89,
                              portfolioRequired=False, researchRequired=False),
            scholarships=[],
        )],
    ),
    dict(
        id="tum", name="Technical University of Munich", shortName="TU Munich",
        country="Germany", countryCode="DE", city="Munich",
        ranking=37, acceptanceRate=8.0, type="Public", researchOutput="Very High",
        tags=["Engineering","Europe","Affordable","Research"],
        programs=[dict(
            id="tum-cs", name="Informatics", degree="BSc",
            major="CS", tuitionUSD=3000, duration=3,
            deadlines=dict(regularDecision="2027-05-31"),
            requirements=dict(minGPA=3.5, minIELTS=6.5, minTOEFL=88,
                              portfolioRequired=False, researchRequired=False),
            scholarships=[dict(id="tum-daad", name="DAAD Scholarship",
                               amount=8640, currency="EUR", eligibility=["International"], renewable=True)],
        )],
    ),
]

WEIGHTS = dict(
    academics=0.25, testing=0.20, research=0.18,
    leadership=0.12, techPortfolio=0.10, community=0.08, initiative=0.07,
)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


# ── Dimension scoring ──────────────────────────────────────────────────────────
def compute_dimension_scores(profile: StudentProfile) -> Dict[str, float]:
    acad = profile.academics
    ts   = profile.testScores
    ecs  = profile.extracurriculars

    academics_score = _clamp((acad.gpa / 4.0) * 10, 0, 10)

    sat_score = _clamp(((ts.sat - 400) / 1200) * 10, 0, 10) if ts.sat else 0
    act_score = _clamp(((ts.act - 1) / 35) * 10, 0, 10) if ts.act else 0
    testing_score = max(sat_score, act_score)

    research_count = sum(1 for e in ecs if e.category in ["Research","Projects","Olympiads"])
    has_founder    = any(e.leadershipLevel in ["Founder","President"] for e in ecs)
    research_score = _clamp(research_count * 2 + (1 if has_founder else 0), 0, 10)

    leadership_pts = {
        "None": 0, "Member": 1, "Officer": 2, "President": 3.5, "Founder": 4,
    }
    total_leadership = sum(leadership_pts.get(e.leadershipLevel, 0) for e in ecs)
    leadership_score = _clamp(total_leadership * 0.8, 0, 10)

    tech_count = sum(1 for e in ecs if e.category in ["Projects","Hackathons","Startups"])
    tech_score = _clamp(tech_count * 1.8, 0, 10)

    community_count = sum(1 for e in ecs if e.category in ["Volunteering","Clubs","Sports"])
    community_score = _clamp(community_count * 1.5, 0, 10)

    initiative_score = _clamp(
        sum(3 for e in ecs if e.category == "Startups") +
        sum(2 for e in ecs if e.category == "Internships"),
        0, 10,
    )

    return {
        "academics":     round(academics_score, 1),
        "testing":       round(testing_score, 1),
        "research":      round(research_score, 1),
        "leadership":    round(leadership_score, 1),
        "techPortfolio": round(tech_score, 1),
        "community":     round(community_score, 1),
        "initiative":    round(initiative_score, 1),
    }


def _research_target(research_output: str) -> float:
    return {"Very High": 7.0, "High": 5.0, "Medium": 3.0}.get(research_output, 3.0)


def _leadership_target(ranking: int) -> float:
    return 7.0 if ranking <= 10 else (5.0 if ranking <= 50 else 3.0)


def compute_match_score(
    dims: Dict[str, float],
    program: dict,
    uni: dict,
) -> int:
    req = program["requirements"]
    score = 0.0

    # Academics
    acad_target = _clamp((req.get("minGPA", 3.5) / 4.0) * 10, 0, 10)
    score += _clamp(dims["academics"] / acad_target, 0, 1.2) * WEIGHTS["academics"] * 100

    # Testing
    test_target = _clamp(((req.get("minSAT", 1300) - 400) / 1200) * 10, 0, 10) if req.get("minSAT") else 7.0
    score += _clamp(dims["testing"] / test_target, 0, 1.2) * WEIGHTS["testing"] * 100

    # Research
    score += _clamp(dims["research"] / _research_target(uni["researchOutput"]), 0, 1.2) * WEIGHTS["research"] * 100

    # Leadership
    score += _clamp(dims["leadership"] / _leadership_target(uni["ranking"]), 0, 1.2) * WEIGHTS["leadership"] * 100

    # Tech portfolio
    score += _clamp(dims["techPortfolio"] / 6.0, 0, 1.2) * WEIGHTS["techPortfolio"] * 100

    # Community
    score += _clamp(dims["community"] / 5.0, 0, 1.2) * WEIGHTS["community"] * 100

    # Initiative
    score += _clamp(dims["initiative"] / 4.0, 0, 1.2) * WEIGHTS["initiative"] * 100

    # Acceptance bonus
    accept_bonus = _clamp((uni["acceptanceRate"] / 100) * 15, 0, 15)
    score = _clamp(score + accept_bonus, 0, 99)
    return round(score)


def score_to_tier(score: int) -> MatchTier:
    if score >= 75: return "Likely"
    if score >= 50: return "Target"
    return "Reach"


def score_to_outlook(score: int) -> Outlook:
    if score >= 85: return "Very Strong Fit"
    if score >= 70: return "Strong Fit"
    if score >= 55: return "Competitive"
    if score >= 40: return "Ambitious"
    return "Highly Ambitious"


def build_match_reasons(
    dims: Dict[str, float],
    uni: dict,
    program: dict,
) -> Tuple[List[MatchReason], List[DimensionGap]]:
    checks = [
        ("academics",     "Academics",      _clamp(((program["requirements"].get("minGPA", 3.5)) / 4.0) * 10, 0, 10)),
        ("testing",       "Test scores",    _clamp((((program["requirements"].get("minSAT", 1300)) - 400) / 1200) * 10, 0, 10) if program["requirements"].get("minSAT") else 7.0),
        ("research",      "Research",       _research_target(uni["researchOutput"])),
        ("leadership",    "Leadership",     _leadership_target(uni["ranking"])),
        ("techPortfolio", "Tech portfolio", 5.0),
        ("community",     "Community",      4.0),
    ]
    reasons, gaps = [], []
    for key, label, required in checks:
        val  = dims.get(key, 0)
        diff = val - required
        gaps.append(DimensionGap(
            dimension=label, studentScore=val,
            requiredScore=required, gap=round(diff, 1),
        ))
        if diff >= 1.5:
            reasons.append(MatchReason(
                dimension=label, status="strength",
                detail=f"Your {label.lower()} ({val:.1f}) exceeds the typical admitted profile.",
            ))
        elif diff <= -2.0:
            reasons.append(MatchReason(
                dimension=label, status="gap",
                detail=f"{label} is below the typical {uni['shortName']} admit threshold. Improving here has the highest ROI.",
            ))
        else:
            reasons.append(MatchReason(
                dimension=label, status="neutral",
                detail=f"{label} is within the competitive range for {uni['shortName']}.",
            ))
    return reasons, gaps


def build_outlook_explanation(outlook: str, uni: dict, dims: Dict[str, float]) -> str:
    lowest_key = min(dims, key=lambda k: dims[k])
    explanations = {
        "Highly Ambitious":
            f"Your profile is well below the typical {uni['shortName']} admit. Significant improvement in {lowest_key} and research is needed.",
        "Ambitious":
            f"Your academics are competitive, but {lowest_key} and leadership fall below the {uni['shortName']} admit median.",
        "Competitive":
            f"Your profile aligns with the lower end of admitted students at {uni['shortName']}. Strengthening research and leadership could meaningfully improve your chances.",
        "Strong Fit":
            f"Solid match for {uni['shortName']}. A strong application essay and recommendations will be decisive.",
        "Very Strong Fit":
            f"Your profile closely mirrors the top quartile of {uni['shortName']} admits. Focus on essay quality and strong letters of recommendation.",
    }
    return explanations.get(outlook, "")


# ── Main entry point ───────────────────────────────────────────────────────────
def run_matching_engine(
    profile: StudentProfile,
    preferred_countries: List[str] | None = None,
    budget_max: float | None = None,
) -> MatchingResponse:
    dims = compute_dimension_scores(profile)
    all_matches: List[UniversityMatchOut] = []

    for uni in UNIVERSITIES:
        if preferred_countries and "Any" not in preferred_countries:
            if uni["country"] not in preferred_countries:
                continue

        for prog in uni["programs"]:
            if budget_max and prog["tuitionUSD"] > budget_max:
                continue

            match_score = compute_match_score(dims, prog, uni)
            tier        = score_to_tier(match_score)
            outlook     = score_to_outlook(match_score)
            reasons, gaps = build_match_reasons(dims, uni, prog)

            all_matches.append(UniversityMatchOut(
                id=f"{uni['id']}-{prog['id']}",
                universityName=uni["name"],
                shortName=uni["shortName"],
                country=uni["country"],
                countryCode=uni["countryCode"],
                city=uni["city"],
                ranking=uni["ranking"],
                programName=prog["name"],
                degree=prog["degree"],
                tuitionUSD=prog["tuitionUSD"],
                acceptanceRate=uni["acceptanceRate"],
                tier=tier,
                matchScore=match_score,
                outlook=outlook,
                outlookExplanation=build_outlook_explanation(outlook, uni, dims),
                matchReasons=reasons,
                dimensionGaps=gaps,
                earlyActionDeadline=prog["deadlines"].get("earlyAction"),
                regularDeadline=prog["deadlines"]["regularDecision"],
                scholarships=prog.get("scholarships", []),
                tags=uni["tags"],
            ))

    all_matches.sort(key=lambda m: -m.matchScore)
    reach  = [m for m in all_matches if m.tier == "Reach"]
    target = [m for m in all_matches if m.tier == "Target"]
    likely = [m for m in all_matches if m.tier == "Likely"]

    top_gap = min(dims, key=lambda k: dims[k])
    reach_count = len(reach)

    return MatchingResponse(
        reach=reach,
        target=target,
        likely=likely,
        totalMatched=len(all_matches),
        generatedAt=datetime.utcnow().isoformat(),
        aiInsight=(
            f"Improving {top_gap} would unlock {reach_count} more Reach schools. "
            f"Your testing score is your strongest asset — lead with it in every application."
        ),
        dimensionScores=dims,
    )
