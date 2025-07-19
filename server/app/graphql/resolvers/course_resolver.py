import strawberry
from typing import List, Optional
from app.neu_api.searchneu_client import SearchNEUClient
from app.services.html_parser import HTMLParser
from app.graphql.types.course import Course, Class, Term, Subject


@strawberry.type
class CourseQuery:
    @strawberry.field
    async def get_terms(self, max_results: int = 20) -> List[Term]:
        """Get available academic terms"""
        client = SearchNEUClient()
        data = await client.get_terms(max_results=max_results)

        if not isinstance(data, list):
            return []

        return [
            Term(
                id=term.get("code", ""),
                name=term.get("description", ""),
            )
            for term in data
        ]

    @strawberry.field
    async def get_subjects(self, term: str, search_term: str = "") -> List[Subject]:
        """Get subjects for a specific term"""
        client = SearchNEUClient()
        data = await client.get_subjects(term, search_term=search_term)

        if not isinstance(data, list):
            return []

        return [
            Subject(
                code=subject.get("code", ""),
                name=subject.get("description", ""),
            )
            for subject in data
        ]

    @strawberry.field
    async def search_courses(
        self,
        term: str,
        subject: Optional[str] = "",
        course_number: Optional[str] = "",
        page_size: Optional[int] = 20,
    ) -> List[Class]:
        """Search for course sections"""
        client = SearchNEUClient()
        data = await client.search_courses(
            term=term,
            subject=subject or "",
            course_number=course_number or "",
            page_max_size=page_size or 20,
        )

        if not isinstance(data, dict) or not data.get("success"):
            return []

        courses_data = data.get("data", [])
        classes = []

        for course in courses_data:
            # Get meeting times
            meetings = course.get("meetingsFaculty", [])
            meeting_info = meetings[0].get("meetingTime", {}) if meetings else {}

            # Format meeting days
            days = []
            for day, is_meeting in [
                ("Monday", meeting_info.get("monday", False)),
                ("Tuesday", meeting_info.get("tuesday", False)),
                ("Wednesday", meeting_info.get("wednesday", False)),
                ("Thursday", meeting_info.get("thursday", False)),
                ("Friday", meeting_info.get("friday", False)),
                ("Saturday", meeting_info.get("saturday", False)),
                ("Sunday", meeting_info.get("sunday", False)),
            ]:
                if is_meeting:
                    days.append(day[:3])  # Mon, Tue, etc.

            # Format meeting times
            begin_time = meeting_info.get("beginTime", "")
            end_time = meeting_info.get("endTime", "")
            time_str = ""
            if begin_time and end_time:
                # Convert from 24hr format like "0915" to "9:15 AM"
                try:
                    begin_hour = int(begin_time[:2])
                    begin_min = begin_time[2:]
                    end_hour = int(end_time[:2])
                    end_min = end_time[2:]

                    begin_ampm = "AM" if begin_hour < 12 else "PM"
                    end_ampm = "AM" if end_hour < 12 else "PM"

                    if begin_hour > 12:
                        begin_hour -= 12
                    if end_hour > 12:
                        end_hour -= 12

                    time_str = f"{begin_hour}:{begin_min} {begin_ampm} - {end_hour}:{end_min} {end_ampm}"
                except:
                    time_str = f"{begin_time} - {end_time}"

            # Get instructor names
            faculty = course.get("faculty", [])
            instructor_names = [f.get("displayName", "") for f in faculty]

            classes.append(
                Class(
                    crn=str(course.get("courseReferenceNumber", "")),
                    title=course.get("courseTitle", ""),
                    subject=course.get("subject", ""),
                    course_number=course.get("courseNumber", ""),
                    instructor=(
                        ", ".join(instructor_names) if instructor_names else None
                    ),
                    meeting_days=", ".join(days) if days else None,
                    meeting_times=time_str if time_str else None,
                    location=f"{meeting_info.get('buildingDescription', '')} {meeting_info.get('room', '')}".strip()
                    or None,
                    enrollment=course.get("enrollment", 0),
                    enrollment_cap=course.get("maximumEnrollment", 0),
                    waitlist=course.get("waitCount", 0),
                    credits=course.get("creditHourLow", 0),
                )
            )

        return classes

    @strawberry.field
    async def get_course_details(self, term: str, crn: str) -> Optional[Course]:
        """Get detailed course information"""
        client = SearchNEUClient()
        parser = HTMLParser()

        try:
            # Get course description
            description_html = await client.get_course_description(term, crn)
            description = parser.parse_course_description(description_html)

            # Get class details
            details_html = await client.get_class_details(term, crn)
            details = parser.parse_class_details(details_html)

            # Get prerequisites
            prereq_html = await client.get_prerequisites(term, crn)
            prerequisites = parser.parse_prerequisites(prereq_html)

            # Get corequisites
            coreq_html = await client.get_corequisites(term, crn)
            corequisites = parser.parse_corequisites(coreq_html)

            return Course(
                subject=details.get("subject", ""),
                course_number=details.get("course_number", ""),
                title=details.get("title", ""),
                description=description,
                credits=(
                    int(details.get("credit_hours", "0").split()[0])
                    if details.get("credit_hours")
                    else None
                ),
                prerequisites=[
                    f"{p['subject']} {p['course_number']}" for p in prerequisites
                ],
                corequisites=[
                    f"{c['subject']} {c['course_number']}" for c in corequisites
                ],
            )

        except Exception as e:
            print(f"Error getting course details: {e}")
            return None
