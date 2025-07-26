import strawberry
from typing import List, Optional
from app.neu_api.searchneu_client import SearchNEUClient
from app.graphql.types.course import Course, Class, Term, Subject


@strawberry.type
class CourseQuery:
    @strawberry.field
    async def get_terms(self, max_results: int = 50) -> List[Term]:
        """Get available academic terms"""
        try:
            client = SearchNEUClient()
            data = await client.get_terms(max_results=max_results)

            print(
                f"Terms data received: {type(data)}, length: {len(data) if isinstance(data, list) else 'N/A'}"
            )

            if not isinstance(data, list):
                print(f"Expected list, got: {type(data)}")
                return []

            terms = []
            for term in data:
                if isinstance(term, dict) and "code" in term and "description" in term:
                    terms.append(
                        Term(
                            id=term.get("code", ""),
                            name=term.get("description", ""),
                        )
                    )

            print(f"Processed {len(terms)} terms")
            return terms

        except Exception as e:
            print(f"Error in get_terms: {e}")
            return []

    @strawberry.field
    async def get_subjects(self, term: str, search_term: str = "") -> List[Subject]:
        """Get subjects for a specific term"""
        try:
            client = SearchNEUClient()
            data = await client.get_subjects(term, search_term=search_term)

            print(
                f"Subjects data received: {type(data)}, length: {len(data) if isinstance(data, list) else 'N/A'}"
            )

            if not isinstance(data, list):
                return []

            subjects = []
            for subject in data:
                if isinstance(subject, dict) and "code" in subject:
                    subjects.append(
                        Subject(
                            code=subject.get("code", ""),
                            name=subject.get("description", ""),
                        )
                    )

            print(f"Processed {len(subjects)} subjects")
            return subjects

        except Exception as e:
            print(f"Error in get_subjects: {e}")
            return []

    @strawberry.field
    async def search_courses(
        self,
        term: str,
        subject: Optional[str] = "",
        course_number: Optional[str] = "",
        page_size: Optional[int] = 20,
    ) -> List[Class]:
        """Search for course sections"""
        try:
            client = SearchNEUClient()
            print(
                f"Searching courses - Term: {term}, Subject: {subject}, Course: {course_number}"
            )

            data = await client.search_courses(
                term=term,
                subject=subject or "",
                course_number=course_number or "",
                page_max_size=page_size or 20,
            )

            print(f"Search result: {type(data)}")
            print(f"Success: {data.get('success', 'N/A')}")
            print(f"Total count: {data.get('totalCount', 'N/A')}")

            if not isinstance(data, dict):
                print("Expected dict response")
                return []

            if not data.get("success", False):
                print(f"Search not successful: {data.get('message', 'Unknown error')}")
                return []

            courses_data = data.get("data", [])
            if not courses_data:
                print("No courses data found")
                return []

            print(f"Processing {len(courses_data)} courses")
            classes = []

            for i, course in enumerate(courses_data):
                try:
                    # Debug first course
                    if i == 0:
                        print(f"Sample course data: {list(course.keys())}")

                    # Get meeting times - NU Banner structure
                    meetings = course.get("meetingsFaculty", [])
                    meeting_info = {}
                    if meetings and len(meetings) > 0:
                        meeting_info = meetings[0].get("meetingTime", {})

                    # Format meeting days
                    days = []
                    if meeting_info:
                        day_mapping = [
                            ("monday", "Mon"),
                            ("tuesday", "Tue"),
                            ("wednesday", "Wed"),
                            ("thursday", "Thu"),
                            ("friday", "Fri"),
                            ("saturday", "Sat"),
                            ("sunday", "Sun"),
                        ]

                        for day_key, day_abbr in day_mapping:
                            if meeting_info.get(day_key, False):
                                days.append(day_abbr)

                    # Format meeting times
                    begin_time = meeting_info.get("beginTime", "")
                    end_time = meeting_info.get("endTime", "")
                    time_str = ""

                    if begin_time and end_time:
                        try:
                            # Convert from 24hr format like "0915" to "9:15 AM"
                            if len(begin_time) == 4 and len(end_time) == 4:
                                begin_hour = int(begin_time[:2])
                                begin_min = begin_time[2:]
                                end_hour = int(end_time[:2])
                                end_min = end_time[2:]

                                # Convert to 12-hour format
                                begin_ampm = "AM" if begin_hour < 12 else "PM"
                                end_ampm = "AM" if end_hour < 12 else "PM"

                                if begin_hour == 0:
                                    begin_hour = 12
                                elif begin_hour > 12:
                                    begin_hour -= 12

                                if end_hour == 0:
                                    end_hour = 12
                                elif end_hour > 12:
                                    end_hour -= 12

                                time_str = f"{begin_hour}:{begin_min} {begin_ampm} - {end_hour}:{end_min} {end_ampm}"
                        except ValueError:
                            time_str = f"{begin_time} - {end_time}"

                    # Get instructor names
                    faculty = course.get("faculty", [])
                    instructor_names = []
                    for f in faculty:
                        display_name = f.get("displayName", "")
                        if display_name:
                            instructor_names.append(display_name)

                    # Build location string
                    location = ""
                    if meeting_info:
                        building = meeting_info.get("buildingDescription", "")
                        room = meeting_info.get("room", "")
                        if building and room:
                            location = f"{building} {room}"
                        elif building:
                            location = building

                    # Create Class object
                    class_obj = Class(
                        crn=str(course.get("courseReferenceNumber", "")),
                        title=course.get("courseTitle", ""),
                        subject=course.get("subject", ""),
                        course_number=course.get("courseNumber", ""),
                        instructor=(
                            ", ".join(instructor_names) if instructor_names else None
                        ),
                        meeting_days=", ".join(days) if days else None,
                        meeting_times=time_str if time_str else None,
                        location=location if location else None,
                        enrollment=course.get("enrollment", 0),
                        enrollment_cap=course.get("maximumEnrollment", 0),
                        waitlist=course.get("waitCount", 0),
                        credits=course.get("creditHourLow", 0)
                        or course.get("creditHours", 0),
                    )

                    classes.append(class_obj)

                except Exception as e:
                    print(f"Error processing course {i}: {e}")
                    continue

            print(f"Successfully processed {len(classes)} classes")
            return classes

        except Exception as e:
            print(f"Error in search_courses: {e}")
            import traceback

            traceback.print_exc()
            return []
