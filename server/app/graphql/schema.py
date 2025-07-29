# app/graphql/schema.py
import strawberry
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio

from app.graphql.resolvers.course_resolver import CourseQuery
from app.graphql.resolvers.auth_resolver import AuthMutation, AuthQuery
from app.graphql.resolvers.health_resolver import HealthQuery
from app.graphql.resolvers.schedule_resolver import ScheduleQuery, ScheduleMutation
from app.graphql.types.schedule import (
    SuggestedPlan, AcademicPlan, PlannedCourse, ScheduleConflict,
    PlanGenerationInput, PlanGenerationResult, ValidationResult,
    Major, Concentration, Course, RequirementProgress, PlanAnalysis,
    Semester, CoopPattern, RequirementType
)

@strawberry.type
class CourseDataStatus:
    subjects_cached: int
    total_courses: int
    last_updated: Optional[str]
    cache_health: str
from app.worker.tasks import (
    generate_ai_suggestion, generate_smart_academic_plan,
    fetch_dynamic_course_data, validate_course_prerequisites,
    get_course_recommendations, MAJOR_REQUIREMENTS
)


@strawberry.type
class Query(CourseQuery, AuthQuery, HealthQuery, ScheduleQuery):
    
    # =============================================================================
    # EXISTING FUNCTIONALITY (Enhanced)
    # =============================================================================
    
    @strawberry.field
    async def suggest_plan(self, interest: str, years: int = 2) -> List[SuggestedPlan]:
        """Generate AI-powered course plan suggestions (Enhanced with real course data)"""
        try:
            print(f"Starting AI suggestion for interest: '{interest}', years: {years}")
            result = generate_ai_suggestion.delay(interest, years)
            print(f"Celery task submitted with ID: {result.id}")
            
            # Get the result with extended timeout
            suggestions = result.get(timeout=180)  # 3 minutes timeout
            print(f"Celery task completed. Suggestions count: {len(suggestions) if suggestions else 0}")
            
            if not suggestions:
                print("No suggestions returned from Celery task, returning hardcoded fallback")
                # Return hardcoded fallback if Celery fails
                return [
                    SuggestedPlan(
                        year=1,
                        term="Fall",
                        courses=["CS1800 - Discrete Structures", "CS2500 - Fundamentals of CS", "MATH1341 - Calculus I", "ENGW1111 - Writing"],
                        credits=16,
                        notes=f"Fallback plan for {interest} (Year 1 Fall)"
                    ),
                    SuggestedPlan(
                        year=1,
                        term="Spring", 
                        courses=["CS2510 - Fundamentals of CS 2", "CS3000 - Algorithms", "MATH1365 - Mathematical Reasoning", "Science Elective"],
                        credits=16,
                        notes=f"Fallback plan for {interest} (Year 1 Spring)"
                    )
                ]
            
            # Convert suggestions to SuggestedPlan objects
            suggested_plans = []
            for suggestion in suggestions:
                print(f"Processing suggestion: {suggestion}")
                plan = SuggestedPlan(
                    year=suggestion.get("year", 1),
                    term=suggestion.get("term", "Fall"),
                    courses=suggestion.get("courses", []),
                    credits=suggestion.get("credits", 0),
                    notes=suggestion.get("notes")
                )
                suggested_plans.append(plan)
            
            print(f"Returning {len(suggested_plans)} suggested plans")
            return suggested_plans
            
        except Exception as e:
            print(f"Error generating AI suggestion: {e}")
            print(f"Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
            # Return hardcoded fallback on any error
            print("Returning hardcoded fallback due to error")
            return [
                SuggestedPlan(
                    year=1,
                    term="Fall",
                    courses=["CS1800 - Discrete Structures", "CS2500 - Fundamentals of CS", "MATH1341 - Calculus I", "ENGW1111 - Writing"],
                    credits=16,
                    notes=f"Fallback plan for {interest} (Error Recovery)"
                ),
                SuggestedPlan(
                    year=1,
                    term="Spring", 
                    courses=["CS2510 - Fundamentals of CS 2", "CS3000 - Algorithms", "MATH1365 - Mathematical Reasoning", "Science Elective"],
                    credits=16,
                    notes=f"Fallback plan for {interest} (Error Recovery)"
                )
            ]

    @strawberry.field
    async def health_check(self) -> str:
        """Simple health check endpoint"""
        return "GraphQL API is running with NU Banner integration!"

    @strawberry.field
    async def api_status(self) -> str:
        """API status with more details"""
        try:
            from app.neu_api.searchneu_client import SearchNEUClient

            client = SearchNEUClient()
            terms = await client.get_terms(max_results=1)
            if terms:
                return f"✅ API operational - NU Banner accessible ({len(terms)} terms)"
            else:
                return "⚠️ API operational - NU Banner returns no data"
        except Exception as e:
            return f"❌ API issues - NU Banner error: {str(e)}"
    
    # =============================================================================
    # NEW ENHANCED ACADEMIC PLANNING FEATURES
    # =============================================================================
    
    @strawberry.field
    async def get_available_majors(self) -> List[Major]:
        """Get all available majors with their requirements"""
        majors = []
        
        for major_id, config in MAJOR_REQUIREMENTS.items():
            # Build concentrations
            concentrations = []
            for conc_id, conc_config in config.get("concentrations", {}).items():
                concentration = Concentration(
                    id=conc_id,
                    name=conc_config["name"],
                    description=conc_config.get("description", ""),
                    requirements=[],  # Simplified for now
                    special_notes=[],
                    recommended_coop_pattern=None
                )
                concentrations.append(concentration)
            
            major = Major(
                id=major_id,
                name=config["name"],
                college="Khoury College of Computer Sciences",
                degree_type="BSCS",
                total_credits=config["total_credits"],
                core_requirements=[],  # Would build from config in full implementation
                concentrations=concentrations,
                supporting_requirements=[],
                elective_requirements=[],
                special_requirements=config.get("special_requirements", {}),
                available_coop_patterns=[CoopPattern.SPRING_SUMMER, CoopPattern.SUMMER_FALL]
            )
            majors.append(major)
        
        return majors
    
    @strawberry.field
    async def get_major_details(self, major_id: str) -> Optional[Major]:
        """Get detailed information about a specific major"""
        if major_id not in MAJOR_REQUIREMENTS:
            return None
        
        config = MAJOR_REQUIREMENTS[major_id]
        
        # Build concentrations with more detail
        concentrations = []
        for conc_id, conc_config in config.get("concentrations", {}).items():
            concentration = Concentration(
                id=conc_id,
                name=conc_config["name"],
                description=conc_config.get("description", ""),
                requirements=[],
                special_notes=[f"Requires {conc_config['required']} courses from this concentration"],
                recommended_coop_pattern=None
            )
            concentrations.append(concentration)
        
        return Major(
            id=major_id,
            name=config["name"],
            college="Khoury College of Computer Sciences",
            degree_type="BSCS",
            total_credits=config["total_credits"],
            core_requirements=[],
            concentrations=concentrations,
            supporting_requirements=[],
            elective_requirements=[],
            special_requirements=config.get("special_requirements", {}),
            available_coop_patterns=[CoopPattern.SPRING_SUMMER, CoopPattern.SUMMER_FALL]
        )
    
    @strawberry.field
    async def get_course_info(self, course_code: str, term_code: Optional[str] = None) -> Optional[Course]:
        """Get detailed information about a specific course"""
        try:
            # Use the validation task to get course info
            validation_task = validate_course_prerequisites.delay([course_code], term_code)
            result = validation_task.get(timeout=30)
            
            if result.get("success") and course_code in result.get("validations", {}):
                course_data = result["validations"][course_code]
                
                if course_data.get("valid"):
                    return Course(
                        code=course_code,
                        title=course_data.get("title", ""),
                        credits=course_data.get("credits", 4),
                        prerequisites=[],  # Would need additional API call for full details
                        corequisites=[],
                        offered_semesters=[],
                        description="",
                        nupath_requirements=[]
                    )
            
            return None
            
        except Exception as e:
            print(f"Error fetching course info for {course_code}: {e}")
            return None
    
    @strawberry.field
    async def get_course_recommendations(
        self,
        completed_courses: List[str],
        interest_areas: List[str],
        semester_target: str = "fall",
        max_results: int = 10
    ) -> List[Course]:
        """Get personalized course recommendations based on interests and completed courses"""
        try:
            task_result = get_course_recommendations.delay(
                completed_courses, interest_areas, semester_target, max_results
            )
            result = task_result.get(timeout=60)
            
            if result.get("success"):
                recommendations = []
                for rec in result.get("recommendations", []):
                    course = Course(
                        code=rec["course_code"],
                        title=rec["title"],
                        credits=rec["credits"],
                        prerequisites=[],
                        corequisites=[],
                        offered_semesters=[semester_target],
                        description="",
                        nupath_requirements=rec.get("nupath_attributes", [])
                    )
                    recommendations.append(course)
                
                return recommendations
            
            return []
            
        except Exception as e:
            print(f"Error getting course recommendations: {e}")
            return []
    
    @strawberry.field
    async def validate_semester_schedule(
        self,
        courses: List[str],
        semester: str,
        year: int,
        term_code: Optional[str] = None
    ) -> ValidationResult:
        """Validate a semester schedule for conflicts and prerequisites"""
        try:
            task_result = validate_course_prerequisites.delay(courses, term_code)
            result = task_result.get(timeout=45)
            
            errors = []
            warnings = []
            suggestions = []
            total_credits = 0
            
            if result.get("success"):
                validations = result.get("validations", {})
                
                for course, validation in validations.items():
                    if validation.get("valid"):
                        total_credits += validation.get("credits", 4)
                        
                        # Check availability
                        if not validation.get("available", True):
                            warnings.append(ScheduleConflict(
                                type="availability",
                                message=f"{course} has no available seats",
                                courses_involved=[course],
                                severity="warning"
                            ))
                    else:
                        errors.append(ScheduleConflict(
                            type="course_not_found",
                            message=f"{course}: {validation.get('error', 'Course not found')}",
                            courses_involved=[course],
                            severity="error"
                        ))
                
                # Check credit load
                if total_credits > 20:
                    warnings.append(ScheduleConflict(
                        type="credit_overload",
                        message=f"Heavy course load: {total_credits} credits",
                        courses_involved=courses,
                        severity="warning"
                    ))
                    suggestions.append("Consider reducing course load")
                elif total_credits < 12 and total_credits > 0:
                    warnings.append(ScheduleConflict(
                        type="underload",
                        message=f"Low course load: {total_credits} credits",
                        courses_involved=courses,
                        severity="warning"
                    ))
            else:
                errors.append(ScheduleConflict(
                    type="validation_error",
                    message=result.get("error", "Failed to validate courses"),
                    courses_involved=courses,
                    severity="error"
                ))
            
            return ValidationResult(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                total_credits=total_credits
            )
            
        except Exception as e:
            print(f"Error validating semester schedule: {e}")
            return ValidationResult(
                valid=False,
                errors=[ScheduleConflict(
                    type="system_error",
                    message=f"System error during validation: {str(e)}",
                    courses_involved=courses,
                    severity="error"
                )],
                warnings=[],
                suggestions=[],
                total_credits=0
            )
    
    @strawberry.field
    async def get_current_course_data_status(self) -> CourseDataStatus:
        """Get information about cached course data"""
        try:
            from app.config import settings
            import redis
            
            redis_client = redis.Redis.from_url(settings.redis_url)
            
            # Check cache status
            cache_keys = redis_client.keys("subject_courses:*")
            subjects_cached = len(cache_keys)
            
            # Count total courses
            total_courses = subjects_cached  # Simplified for now
            
            return CourseDataStatus(
                subjects_cached=subjects_cached,
                total_courses=total_courses,
                last_updated=None,
                cache_health="operational" if subjects_cached > 0 else "no_cache"
            )
            
        except Exception as e:
            return CourseDataStatus(
                subjects_cached=0,
                total_courses=0,
                last_updated=None,
                cache_health="error"
            )


@strawberry.type
class Mutation(AuthMutation, ScheduleMutation):
    
    # =============================================================================
    # EXISTING FUNCTIONALITY (Enhanced)
    # =============================================================================
    
    @strawberry.mutation
    async def save_schedule(
        self, user_id: str, year: int, term: str, courses: List[str]
    ) -> bool:
        """Save a user's course schedule"""
        try:
            schedule_data = {
                "user_id": user_id,
                "year": year,
                "term": term,
                "courses": courses,
                "saved_at": datetime.now().isoformat()
            }
            print(f"Saving schedule: {schedule_data}")
            # TODO: Implement actual saving to R2 or database
            return True
        except Exception as e:
            print(f"Error saving schedule: {e}")
            return False

    @strawberry.mutation
    async def reset_course_cache(self) -> bool:
        """Reset the course search cache"""
        try:
            from app.neu_api.searchneu_client import SearchNEUClient

            client = SearchNEUClient()
            if client.redis_client:
                # Delete all course-related cache keys
                patterns = ["courses:*", "terms:*", "subjects:*", "subject_courses:*", "academic_plan:*"]
                
                deleted_count = 0
                for pattern in patterns:
                    keys = client.redis_client.keys(pattern)
                    if keys:
                        client.redis_client.delete(*keys)
                        deleted_count += len(keys)
                
                print(f"Deleted {deleted_count} cache keys")
                return True
            return False
        except Exception as e:
            print(f"Error resetting cache: {e}")
            return False
    
    # =============================================================================
    # NEW ENHANCED ACADEMIC PLANNING MUTATIONS
    # =============================================================================
    
    @strawberry.mutation
    async def generate_academic_plan(self, input: PlanGenerationInput) -> PlanGenerationResult:
        """Generate a comprehensive academic plan using real NEU course data"""
        try:
            # Convert strawberry input to dict for celery task
            task_data = {
                "major_id": input.major_id,
                "concentration_id": input.concentration_id,
                "start_year": input.start_year,
                "completed_courses": input.completed_courses,
                "transfer_credits": input.transfer_credits,
                "interest_areas": input.interest_areas,
                "coop_pattern": input.coop_pattern.value,
                "preferences": input.preferences,
                "use_ai_optimization": input.use_ai_suggestions
            }
            
            # Submit task to celery
            task_result = generate_smart_academic_plan.delay(**task_data)
            result = task_result.get(timeout=180)  # 3 minute timeout
            
            if result.get("success"):
                plan_data = result.get("plan", {})
                
                # Convert semester data to GraphQL types
                semesters = []
                for sem_data in plan_data.get("semesters", []):
                    from app.graphql.types.schedule import SemesterPlan
                    
                    semester_enum = {
                        "fall": Semester.FALL,
                        "spring": Semester.SPRING,
                        "summer": Semester.SUMMER1,
                        "summer1": Semester.SUMMER1,
                        "summer2": Semester.SUMMER2
                    }.get(sem_data.get("semester", "fall").lower(), Semester.FALL)
                    
                    # Build conflicts
                    conflicts = []
                    credits = sem_data.get("credits", 0)
                    if credits > 20:
                        conflicts.append(ScheduleConflict(
                            type="credit_overload",
                            message=f"Heavy load: {credits} credits",
                            courses_involved=sem_data.get("courses", []),
                            severity="warning"
                        ))
                    
                    semester_plan = SemesterPlan(
                        semester=semester_enum,
                        year=sem_data.get("year", input.start_year),
                        courses=sem_data.get("courses", []),
                        credits=credits,
                        is_coop=sem_data.get("is_coop", False),
                        notes=sem_data.get("notes"),
                        conflicts=conflicts
                    )
                    semesters.append(semester_plan)
                
                # Create the academic plan
                academic_plan = AcademicPlan(
                    id=plan_data.get("id", f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                    user_id="current_user",  # Would get from auth context
                    name=f"{input.major_id.upper()} Academic Plan",
                    major_id=input.major_id,
                    concentration_id=input.concentration_id,
                    combined_major_id=input.combined_major_id,
                    degree_type="BSCS",
                    duration_years=4,
                    coop_pattern=input.coop_pattern,
                    start_year=input.start_year,
                    total_credits=plan_data.get("total_credits", 0),
                    semesters=semesters,
                    completed_courses=input.completed_courses,
                    transfer_credits=input.transfer_credits,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    is_ai_generated=True,
                    ai_confidence_score=result.get("ai_insights", {}).get("optimization_score", 85) / 100.0
                )
                
                return PlanGenerationResult(
                    success=True,
                    plan=academic_plan,
                    errors=[],
                    warnings=result.get("warnings", []),
                    ai_reasoning=json.dumps(result.get("ai_insights", {}), indent=2)
                )
            else:
                return PlanGenerationResult(
                    success=False,
                    plan=None,
                    errors=[result.get("error", "Unknown error occurred")],
                    warnings=[],
                    ai_reasoning=None
                )
                
        except Exception as e:
            print(f"Error in generate_academic_plan: {e}")
            return PlanGenerationResult(
                success=False,
                plan=None,
                errors=[f"Failed to generate plan: {str(e)}"],
                warnings=[],
                ai_reasoning=None
            )
    
    @strawberry.mutation
    async def refresh_course_data(self, term_code: Optional[str] = None, subjects: Optional[List[str]] = None) -> bool:
        """Refresh course data from NEU Banner API"""
        try:
            if not subjects:
                subjects = ["CS", "DS", "MATH", "PHYS", "CHEM", "BIOL", "EECE", "PHIL", "ENGW", "CY", "IS"]
                
            task_result = fetch_dynamic_course_data.delay(term_code, subjects)
            result = task_result.get(timeout=300)  # 5 minute timeout
            
            success = result.get("success", False)
            if success:
                print(f"Successfully refreshed course data: {result.get('total_courses', 0)} courses")
            
            return success
            
        except Exception as e:
            print(f"Error refreshing course data: {e}")
            return False
    
    @strawberry.mutation
    async def generate_ai_suggestions(
        self,
        interest: str,
        duration_years: int = 2,
        current_courses: Optional[List[str]] = None
    ) -> List[SuggestedPlan]:
        """Generate AI-powered course suggestions with enhanced logic"""
        try:
            task_result = generate_ai_suggestion.delay(interest, duration_years)
            suggestions = task_result.get(timeout=60)
            
            suggested_plans = []
            for suggestion in suggestions:
                plan = SuggestedPlan(
                    year=suggestion.get("year", 1),
                    term=suggestion.get("term", "Fall"),
                    courses=suggestion.get("courses", []),
                    credits=suggestion.get("credits", 0),
                    notes=suggestion.get("notes", f"AI-generated plan focused on {interest}")
                )
                suggested_plans.append(plan)
            
            return suggested_plans
            
        except Exception as e:
            print(f"Error generating AI suggestions: {e}")
            return []


# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# Import for FastAPI
from strawberry.fastapi import GraphQLRouter

graphql_app = GraphQLRouter(schema)

# Enhanced test queries with new functionality
TEST_QUERIES = """
# =============================================================================
# EXISTING FUNCTIONALITY (Enhanced)
# =============================================================================

# Test 1: Health Check
query {
  healthCheck
}

# Test 2: API Status (includes NU Banner connectivity test)
query {
  apiStatus
}

# Test 3: Get Terms
query {
  getTerms(maxResults: 10) {
    id
    name
  }
}

# Test 4: Get Subjects
query {
  getSubjects(term: "202510") {
    code
    name
  }
}

# Test 5: Search Courses
query {
  searchCourses(term: "202510", subject: "CS", pageSize: 5) {
    crn
    title
    subject
    courseNumber
    instructor
    meetingDays
    meetingTimes
    location
    enrollment
    enrollmentCap
    credits
  }
}

# Test 6: Enhanced AI Plan Suggestion
query {
  suggestPlan(interest: "artificial intelligence", years: 2) {
    year
    term
    courses
    credits
    notes
  }
}

# =============================================================================
# NEW ENHANCED ACADEMIC PLANNING FEATURES
# =============================================================================

# Test 7: Get Available Majors
query {
  getAvailableMajors {
    id
    name
    college
    degreeType
    totalCredits
    concentrations {
      id
      name
      description
    }
  }
}

# Test 8: Get Major Details
query {
  getMajorDetails(majorId: "neu_cs_bs") {
    id
    name
    totalCredits
    concentrations {
      id
      name
      description
      specialNotes
    }
  }
}

# Test 9: Get Course Information
query {
  getCourseInfo(courseCode: "CS2500") {
    code
    title
    credits
    prerequisites
    corequisites
  }
}

# Test 10: Get Course Recommendations
query {
  getCourseRecommendations(
    completedCourses: ["CS1800", "CS2500", "MATH1341"]
    interestAreas: ["machine learning", "artificial intelligence"]
    semesterTarget: "fall"
    maxResults: 5
  ) {
    code
    title
    credits
    nupathRequirements
  }
}

# Test 11: Validate Semester Schedule
query {
  validateSemesterSchedule(
    courses: ["CS2510", "CS3000", "MATH1365", "PHYS1151"]
    semester: "spring"
    year: 2024
  ) {
    valid
    totalCredits
    errors {
      type
      message
      severity
      coursesInvolved
    }
    warnings {
      type
      message
      severity
    }
    suggestions
  }
}

# Test 12: Check Course Data Status
query {
  getCurrentCourseDataStatus
}

# =============================================================================
# MUTATIONS
# =============================================================================

# Test 13: Generate Complete Academic Plan
mutation {
  generateAcademicPlan(input: {
    majorId: "neu_cs_bs"
    concentrationId: "ai"
    startYear: 2024
    completedCourses: ["CS1800", "MATH1341", "ENGW1111"]
    interestAreas: ["artificial intelligence", "machine learning"]
    coopPattern: SPRING_SUMMER
    preferences: {
      "maxCreditsPerSemester": 18
      "minCreditsPerSemester": 12
    }
    useAiSuggestions: true
  }) {
    success
    plan {
      id
      totalCredits
      isAiGenerated
      aiConfidenceScore
      semesters {
        semester
        year
        courses
        credits
        isCoop
        conflicts {
          type
          message
          severity
        }
      }
    }
    errors
    warnings
    aiReasoning
  }
}

# Test 14: Refresh Course Data
mutation {
  refreshCourseData(subjects: ["CS", "DS", "MATH"])
}

# Test 15: Generate AI Suggestions
mutation {
  generateAiSuggestions(
    interest: "web development"
    durationYears: 2
    currentCourses: ["CS1800", "CS2500"]
  ) {
    year
    term
    courses
    credits
    notes
  }
}

# Test 16: Reset Cache
mutation {
  resetCourseCache
}

# Test 17: Save Schedule
mutation {
  saveSchedule(
    userId: "user123"
    year: 2024
    term: "Fall"
    courses: ["CS2500", "MATH1341", "ENGW1111", "PHYS1151"]
  )
}
"""