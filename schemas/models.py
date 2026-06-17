from __future__ import annotations
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ── Enums / Literals ───────────────────────────────────────────────────────────
Curriculum   = Literal["CBSE", "ICSE", "IB", "A_LEVELS", "AP", "OTHER"]
ECCategory   = Literal["Projects","Research","Olympiads","Competitions",
                        "Hackathons","Leadership","Clubs","Sports",
                        "Volunteering","Startups","Internships"]
MatchTier    = Literal["Reach", "Target", "Likely"]
Outlook      = Literal["Highly Ambitious","Ambitious","Competitive","Strong Fit","Very Strong Fit"]
BudgetRange  = Literal["under_20k","20k_40k","40k_60k","60k_plus","any"]
Leadership   = Literal["None","Member","Officer","President","Founder"]
ResearchOut  = Literal["Very High","High","Medium","Low"]
UniType      = Literal["Public","Private"]
DegreeType   = Literal["BS","BE","BTech","BEng","BA","BSc"]


# ── Sub-models ─────────────────────────────────────────────────────────────────
class AcademicProfile(BaseModel):
    curriculum:       Curriculum
    gpa:              float = Field(..., ge=0.0, le=4.0)
    percentage:       float = Field(..., ge=0.0, le=100.0)
    predictedGrades:  Optional[str] = None


class APScore(BaseModel):
    subject: str
    score:   int = Field(..., ge=1, le=5)


class TestScores(BaseModel):
    sat:       Optional[int]       = Field(None, ge=400, le=1600)
    act:       Optional[int]       = Field(None, ge=1,   le=36)
    ielts:     Optional[float]     = Field(None, ge=0.0, le=9.0)
    toefl:     Optional[int]       = Field(None, ge=0,   le=120)
    duolingo:  Optional[int]       = Field(None, ge=0,   le=160)
    apScores:  Optional[List[APScore]] = None
    jee:       Optional[int]       = None
    bitsat:    Optional[int]       = None


class Extracurricular(BaseModel):
    id:              str
    category:        ECCategory
    title:           str
    description:     str
    duration:        str
    impact:          str
    awards:          Optional[str] = None
    leadershipLevel: Leadership


class CareerGoals(BaseModel):
    intendedMajor:        str
    dreamUniversities:    List[str] = []
    preferredCountries:   List[str] = []
    financialAidRequired: bool = False


class StudentProfile(BaseModel):
    id:                   str
    name:                 str
    country:              str
    intakeYear:           int
    intendedMajor:        str
    preferredCountries:   List[str] = []
    budgetRange:          BudgetRange
    academics:            AcademicProfile
    testScores:           TestScores
    extracurriculars:     List[Extracurricular] = []
    careerGoals:          CareerGoals


# ── Matching request / response ────────────────────────────────────────────────
class MatchingRequest(BaseModel):
    profile:              StudentProfile
    preferredCountries:   List[str] = []
    budgetMax:            Optional[float] = None
    includeScholarships:  bool = True


class DimensionGap(BaseModel):
    dimension:    str
    studentScore: float
    requiredScore: float
    gap:          float


class MatchReason(BaseModel):
    dimension: str
    status:    Literal["strength", "gap", "neutral"]
    detail:    str


class UniversityMatchOut(BaseModel):
    id:                  str
    universityName:      str
    shortName:           str
    country:             str
    countryCode:         str
    city:                str
    ranking:             int
    programName:         str
    degree:              DegreeType
    tuitionUSD:          float
    acceptanceRate:      float
    tier:                MatchTier
    matchScore:          int
    outlook:             Outlook
    outlookExplanation:  str
    matchReasons:        List[MatchReason]
    dimensionGaps:       List[DimensionGap]
    earlyActionDeadline: Optional[str] = None
    regularDeadline:     str
    scholarships:        List[dict] = []
    tags:                List[str]


class MatchingResponse(BaseModel):
    reach:        List[UniversityMatchOut]
    target:       List[UniversityMatchOut]
    likely:       List[UniversityMatchOut]
    totalMatched: int
    generatedAt:  str
    aiInsight:    str
    dimensionScores: dict


# ── Profile evaluation ─────────────────────────────────────────────────────────
class DimensionScore(BaseModel):
    key:            str
    label:          str
    score:          float
    level:          str
    explanation:    str
    improvementTip: str


class ProfileEvaluationResponse(BaseModel):
    overallScore:   float
    dimensions:     List[DimensionScore]
    strengths:      List[str]
    weaknesses:     List[str]
    opportunities:  List[str]
    aiNarrative:    str


# ── Gap Analysis ───────────────────────────────────────────────────────────────
class GapAnalysisRequest(BaseModel):
    profile:       StudentProfile
    universityId:  str


class GapItem(BaseModel):
    dimension:      str
    studentValue:   float
    benchmarkValue: float
    delta:          float
    severity:       Literal["Critical", "Moderate", "Minor", "Positive"]


class GapAnalysisResponse(BaseModel):
    universityId:          str
    universityName:        str
    strengths:             List[GapItem]
    weaknesses:            List[GapItem]
    topGaps:               List[GapItem]
    admissionLikelihood:   float
    keyInsight:            str
    aiRecommendations:     List[str]


# ── AI narrative ───────────────────────────────────────────────────────────────
class AIInsightRequest(BaseModel):
    profile:       StudentProfile
    focusTopic:    Optional[str] = None


class AIInsightResponse(BaseModel):
    insight:       str
    actionItems:   List[str]
    generatedAt:   str
