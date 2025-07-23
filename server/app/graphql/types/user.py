import strawberry
from typing import List, Optional
from datetime import datetime


@strawberry.type
class User:
    id: str
    email: str
    firstName: str = strawberry.field(name="first_name")
    lastName: str = strawberry.field(name="last_name")
    studentId: Optional[str] = strawberry.field(name="student_id", default=None)
    graduationYear: Optional[int] = strawberry.field(name="graduation_year", default=None)
    major: Optional[str] = None
    isVerified: bool = strawberry.field(name="is_verified", default=True)
    createdAt: datetime = strawberry.field(name="created_at")


@strawberry.type
class UserPreferences:
    id: str
    user_id: str
    interests: List[str]
    career_goals: List[str]
    ai_suggestions_enabled: bool = True


@strawberry.type
class AuthResponse:
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[User] = None


@strawberry.input
class RegisterInput:
    firstName: str
    lastName: str
    studentId: Optional[str] = None
    major: Optional[str] = None
    graduationYear: Optional[int] = None


@strawberry.input
class VerifyOTPInput:
    email: str
    code: str
    purpose: str
    registerData: Optional[RegisterInput] = strawberry.field(name="register_data", default=None)
