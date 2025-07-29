import strawberry
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


@strawberry.type
class SpecialRequirement:
    key: str
    value: str

@strawberry.input  
class TransferCreditInput:
    course_code: str
    credits: int

@strawberry.type  
class TransferCredit:
    course_code: str
    credits: int

@strawberry.enum
class RequirementType(Enum):
    CORE = "core"
    CONCENTRATION = "concentration"
    SUPPORTING = "supporting"
    ELECTIVE = "elective"
    WRITING = "writing"
    NUPATH = "nupath"
    UNIVERSITY = "university"


@strawberry.enum
class Semester(Enum):
    FALL = "fall"
    SPRING = "spring"
    SUMMER1 = "summer1"
    SUMMER2 = "summer2"


@strawberry.enum
class CoopPattern(Enum):
    SPRING_SUMMER = "spring_summer"
    SUMMER_FALL = "summer_fall"
    FALL_SPRING = "fall_spring"
    NO_COOP = "no_coop"


@strawberry.type
class Course:
    code: str
    title: str
    credits: int
    prerequisites: List[str]
    corequisites: List[str]
    offered_semesters: List[Semester]
    description: Optional[str] = None
    nupath_requirements: List[str] = strawberry.field(default_factory=list)


@strawberry.type
class RequirementGroup:
    id: str
    name: str
    type: RequirementType
    description: Optional[str] = None
    required_courses: List[str] = strawberry.field(default_factory=list)
    elective_options: List[str] = strawberry.field(default_factory=list)
    credits_required: Optional[int] = None
    courses_required: Optional[int] = None
    min_gpa: Optional[float] = None
    is_completed: bool = False
    progress_percentage: float = 0.0


@strawberry.type
class Concentration:
    id: str
    name: str
    description: Optional[str] = None
    requirements: List[RequirementGroup]
    special_notes: List[str] = strawberry.field(default_factory=list)
    recommended_coop_pattern: Optional[CoopPattern] = None


@strawberry.type
class Major:
    id: str
    name: str
    college: str
    degree_type: str
    total_credits: int
    core_requirements: List[RequirementGroup]
    concentrations: List[Concentration] = strawberry.field(default_factory=list)
    supporting_requirements: List[RequirementGroup] = strawberry.field(default_factory=list)
    elective_requirements: List[RequirementGroup] = strawberry.field(default_factory=list)
    special_requirements: List[SpecialRequirement] = strawberry.field(default_factory=list)
    available_coop_patterns: List[CoopPattern] = strawberry.field(default_factory=list)


@strawberry.type
class SemesterPlan:
    semester: Semester
    year: int
    courses: List[str]
    credits: int
    is_coop: bool = False
    notes: Optional[str] = None
    conflicts: List["ScheduleConflict"] = strawberry.field(default_factory=list)


@strawberry.type
class SuggestedPlan:
    year: int
    term: str
    courses: List[str]
    credits: int = 0
    notes: Optional[str] = None


@strawberry.type
class AcademicPlan:
    id: str
    user_id: str
    name: str
    major_id: str
    concentration_id: Optional[str] = None
    combined_major_id: Optional[str] = None
    degree_type: str
    duration_years: int
    coop_pattern: CoopPattern
    start_year: int
    total_credits: int
    semesters: List[SemesterPlan]
    completed_courses: List[str] = strawberry.field(default_factory=list)
    transfer_credits: List[TransferCredit] = strawberry.field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    is_ai_generated: bool = False
    ai_confidence_score: Optional[float] = None


@strawberry.type
class PlannedCourse:
    id: str
    plan_id: str
    course_subject: str
    course_number: str
    course_title: Optional[str] = None
    credits: int
    year: int
    semester: str
    is_completed: bool = False
    grade: Optional[str] = None
    prerequisite_met: bool = True
    corequisite_courses: List[str] = strawberry.field(default_factory=list)


@strawberry.type
class ScheduleConflict:
    type: str  # "prerequisite", "time_conflict", "credit_overload", "not_offered"
    message: str
    courses_involved: List[str]
    severity: str = "warning"  # "error", "warning", "info"
    suggested_resolution: Optional[str] = None


@strawberry.type
class RequirementProgress:
    requirement_id: str
    requirement_name: str
    requirement_type: RequirementType
    completed_courses: List[str]
    remaining_courses: List[str]
    credits_completed: int
    credits_required: int
    courses_completed: int
    courses_required: int
    is_complete: bool
    progress_percentage: float


@strawberry.type
class PlanAnalysis:
    total_credits: int
    credits_completed: int
    credits_remaining: int
    graduation_feasible: bool
    estimated_graduation_date: Optional[str] = None
    requirements_progress: List[RequirementProgress]
    warnings: List[str] = strawberry.field(default_factory=list)
    recommendations: List[str] = strawberry.field(default_factory=list)
    gpa_requirements_met: bool = True


@strawberry.type
class CombinedMajor:
    id: str
    name: str
    primary_major_id: str
    secondary_major_id: str
    shared_requirements: List[str] = strawberry.field(default_factory=list)
    total_credits: int
    special_notes: List[str] = strawberry.field(default_factory=list)
    estimated_completion_years: int = 4


# Input types for mutations
@strawberry.input
class PlanGenerationInput:
    major_id: str
    concentration_id: Optional[str] = None
    combined_major_id: Optional[str] = None
    coop_pattern: CoopPattern = CoopPattern.NO_COOP
    start_year: int
    completed_courses: List[str] = strawberry.field(default_factory=list)
    transfer_credits: List[TransferCreditInput] = strawberry.field(default_factory=list)
    interest_areas: List[str] = strawberry.field(default_factory=list)
    preferences: Optional[str] = None  # JSON string for preferences
    use_ai_suggestions: bool = True


@strawberry.input
class CoursePreferenceInput:
    avoid_early_morning: bool = False
    avoid_friday_classes: bool = False
    preferred_days: List[str] = strawberry.field(default_factory=list)
    max_credits_per_semester: int = 18
    min_credits_per_semester: int = 12
    preferred_course_load: str = "balanced"  # "light", "balanced", "heavy"


@strawberry.input
class UpdatePlanInput:
    plan_id: str
    semester_changes: List["SemesterUpdateInput"] = strawberry.field(default_factory=list)
    notes: Optional[str] = None


@strawberry.input
class SemesterUpdateInput:
    year: int
    semester: Semester
    courses: List[str]
    is_coop: bool = False
    notes: Optional[str] = None


@strawberry.type
class PlanGenerationResult:
    success: bool
    plan: Optional[AcademicPlan] = None
    errors: List[str] = strawberry.field(default_factory=list)
    warnings: List[str] = strawberry.field(default_factory=list)
    ai_reasoning: Optional[str] = None


@strawberry.type
class ValidationResult:
    valid: bool
    errors: List[ScheduleConflict] = strawberry.field(default_factory=list)
    warnings: List[ScheduleConflict] = strawberry.field(default_factory=list)
    suggestions: List[str] = strawberry.field(default_factory=list)
    total_credits: int = 0


# Smart scheduling types
@strawberry.type
class SmartSuggestion:
    type: str  # "course_swap", "semester_adjustment", "prerequisite_fix"
    title: str
    description: str
    impact: str  # "low", "medium", "high"
    courses_affected: List[str] = strawberry.field(default_factory=list)
    implementation_steps: List[str] = strawberry.field(default_factory=list)


@strawberry.type
class OptimizationResult:
    optimized_plan: AcademicPlan
    improvements: List[str]
    suggestions: List[SmartSuggestion]
    efficiency_score: float  # 0-100
    reasoning: str