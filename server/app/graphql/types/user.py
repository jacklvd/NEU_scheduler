import strawberry
from typing import List, Optional
from datetime import datetime


@strawberry.type
class User:
    id: str
    email: str
    first_name: str
    last_name: str
    student_id: Optional[str] = None
    graduation_year: Optional[int] = None
    major: Optional[str] = None
    created_at: datetime


@strawberry.type
class UserPreferences:
    id: str
    user_id: str
    interests: List[str]
    career_goals: List[str]
    ai_suggestions_enabled: bool = True
