import strawberry
from typing import List, Optional
from datetime import datetime


@strawberry.type
class Course:
    subject: str
    course_number: str
    title: str
    description: Optional[str] = None
    credits: Optional[int] = None
    prerequisites: Optional[List[str]] = None
    corequisites: Optional[List[str]] = None


@strawberry.type
class Class:
    crn: str
    title: str
    subject: str
    course_number: str
    instructor: Optional[str] = None
    meeting_days: Optional[str] = None
    meeting_times: Optional[str] = None
    location: Optional[str] = None
    enrollment: Optional[int] = None
    enrollment_cap: Optional[int] = None
    waitlist: Optional[int] = None
    credits: Optional[int] = None


@strawberry.type
class Term:
    id: str
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@strawberry.type
class CatalogEntry:
    subject: str
    course_number: str
    title: str
    description: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    credits: Optional[int] = None


@strawberry.type
class Instructor:
    name: str
    email: Optional[str] = None
    department: Optional[str] = None


@strawberry.type
class Subject:
    code: str
    name: str
    college: Optional[str] = None
