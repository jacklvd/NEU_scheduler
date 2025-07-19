import strawberry
from typing import List, Optional
from datetime import datetime
import uuid


@strawberry.type
class SuggestedPlan:
    year: int
    term: str
    courses: List[str]


@strawberry.type
class AcademicPlan:
    id: str
    user_id: str
    name: str
    degree_type: str
    duration_years: int
    created_at: datetime
    updated_at: datetime


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


@strawberry.type
class ScheduleConflict:
    type: str  # "prerequisite", "time_conflict", "credit_overload"
    message: str
    courses_involved: List[str]
