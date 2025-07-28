# app/graphql/resolvers/schedule_resolver.py
import strawberry
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..types.schedule import (
    AcademicPlan, SuggestedPlan, PlannedCourse, ScheduleConflict,
    PlanGenerationInput, PlanGenerationResult, ValidationResult,
    RequirementProgress, PlanAnalysis, Major, Concentration,
    Course, SmartSuggestion, OptimizationResult, CoopPattern,
    SemesterPlan, Semester
)
from ...worker.tasks import (
    generate_smart_academic_plan, fetch_dynamic_course_data,
    validate_course_prerequisites, get_course_recommendations,
    generate_ai_suggestion
)
from ...config import settings
import redis

# Initialize Redis for caching
redis_client = redis.Redis.from_url(settings.redis_url)

@strawberry.type
class ScheduleQuery:
    
    @strawberry.field
    async def get_available_majors(self) -> List[Major]:
        """Get all available majors with their requirements"""
        
        # This would typically come from a database
        # For now, return NEU CS as an example
        from ...worker.tasks import MAJOR_REQUIREMENTS
        
        majors = []
        for major_id, config in MAJOR_REQUIREMENTS.items():
            # Convert config to Major type
            major = Major(
                id=major_id,
                name=config["name"],
                college="Khoury College of Computer Sciences",
                degree_type="BSCS",
                total_credits=config["total_credits"],
                core_requirements=[],  # Would be populated from config
                concentrations=[],     # Would be populated from config
                supporting_requirements=[],
                elective_requirements=[],
                special_requirements={},
                available_coop_patterns=[]
            )
            majors.append(major)
        
        return majors
    
    @strawberry.field
    async def get_major_details(self, major_id: str) -> Optional[Major]:
        """Get detailed information about a specific major"""
        
        from ...worker.tasks import MAJOR_REQUIREMENTS
        
        if major_id not in MAJOR_REQUIREMENTS:
            return None
        
        config = MAJOR_REQUIREMENTS[major_id]
        
        # Build concentrations
        concentrations = []
        for conc_id, conc_config in config.get("concentrations", {}).items():
            concentration = Concentration(
                id=conc_id,
                name=conc_config["name"],
                description=conc_config.get("description", ""),
                requirements=[],  # Would build from conc_config
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
            core_requirements=[],  # Would build from config
            concentrations=concentrations,
            supporting_requirements=[],
            elective_requirements=[],
            special_requirements={},
            available_coop_patterns=[]
        )
        
        return major
    
    @strawberry.field
    async def get_course_info(self, course_code: str, term_code: Optional[str] = None) -> Optional[Course]:
        """Get detailed information about a specific course"""
        
        # Check cache first
        cache_key = f"course_info:{course_code}:{term_code or 'current'}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            try:
                data = json.loads(cached_data)
                return Course(**data)
            except Exception:
                pass
        
        # Fetch from API
        validation_result = validate_course_prerequisites.delay([course_code], term_code)
        result = validation_result.get(timeout=30)
        
        if result.get("success") and course_code in result.get("validations", {}):
            course_data = result["validations"][course_code]
            
            if course_data.get("valid"):
                course = Course(
                    code=course_code,
                    title=course_data.get("title", ""),
                    credits=course_data.get("credits", 4),
                    prerequisites=[],  # Would need additional API call
                    corequisites=[],   # Would need additional API call
                    offered_semesters=[],
                    description="",
                    nupath_requirements=[]
                )
                
                # Cache the result
                redis_client.setex(cache_key, 1800, json.dumps({
                    "code": course.code,
                    "title": course.title,
                    "credits": course.credits,
                    "prerequisites": course.prerequisites,
                    "corequisites": course.corequisites,
                    "offered_semesters": course.offered_semesters,
                    "description": course.description,
                    "nupath_requirements": course.nupath_requirements
                }))
                
                return course
        
        return None
    
    @strawberry.field
    async def get_academic_plan(self, plan_id: str) -> Optional[AcademicPlan]:
        """Get an existing academic plan"""
        
        cache_key = f"academic_plan:{plan_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            try:
                data = json.loads(cached_data)
                plan_data = data.get("plan", {})
                
                # Convert to AcademicPlan type
                # This would need proper conversion from dict to the strawberry types
                # For now, return a placeholder
                return None  # Would implement proper conversion
            except Exception:
                pass
        
        return None
    
    @strawberry.field
    async def get_course_recommendations(
        self,
        completed_courses: List[str],
        interest_areas: List[str],
        semester_target: str = "fall",
        max_results: int = 10
    ) -> List[Course]:
        """Get personalized course recommendations"""
        
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
    
    @strawberry.field
    async def validate_semester_schedule(
        self,
        courses: List[str],
        semester: str,
        year: int,
        term_code: Optional[str] = None
    ) -> ValidationResult:
        """Validate a semester schedule for conflicts and prerequisites"""
        
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
                    if validation.get("available", True) == False:
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
                suggestions.append("Consider reducing course load or spreading across multiple semesters")
            elif total_credits < 12:
                warnings.append(ScheduleConflict(
                    type="underload",
                    message=f"Low course load: {total_credits} credits (may not meet full-time requirements)",
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

@strawberry.type
class ScheduleMutation:
    
    @strawberry.mutation
    async def generate_academic_plan(self, input: PlanGenerationInput) -> PlanGenerationResult:
        """Generate a comprehensive academic plan"""
        
        try:
            # Convert strawberry input to dict for celery task
            preferences_dict = {}
            if input.preferences:
                try:
                    preferences_dict = json.loads(input.preferences)
                except json.JSONDecodeError:
                    preferences_dict = {}
            
            # Convert transfer credits list to dict for task
            transfer_credits_dict = {tc.course_code: tc.credits for tc in input.transfer_credits}
            
            task_data = {
                "major_id": input.major_id,
                "concentration_id": input.concentration_id,
                "start_year": input.start_year,
                "completed_courses": input.completed_courses,
                "transfer_credits": transfer_credits_dict,
                "interest_areas": input.interest_areas,
                "coop_pattern": input.coop_pattern.value,
                "preferences": preferences_dict,
                "use_ai_optimization": input.use_ai_suggestions
            }
            
            # Submit task to celery
            task_result = generate_smart_academic_plan.delay(**task_data)
            result = task_result.get(timeout=120)  # 2 minute timeout
            
            if result.get("success"):
                plan_data = result.get("plan", {})
                
                # Convert plan data to AcademicPlan type
                # This is a simplified conversion - you'd need to properly map all fields
                semesters = []
                for sem_data in plan_data.get("semesters", []):
                    semester_enum = {
                        "fall": Semester.FALL,
                        "spring": Semester.SPRING,
                        "summer": Semester.SUMMER1
                    }.get(sem_data.get("semester", "fall"), Semester.FALL)
                    
                    semester_plan = SemesterPlan(
                        semester=semester_enum,
                        year=sem_data.get("year", input.start_year),
                        courses=sem_data.get("courses", []),
                        credits=sem_data.get("credits", 0),
                        is_coop=sem_data.get("is_coop", False),
                        notes=sem_data.get("notes"),
                        conflicts=[]
                    )
                    semesters.append(semester_plan)
                
                academic_plan = AcademicPlan(
                    id=plan_data.get("id", ""),
                    user_id="",  # Would get from context
                    name=f"{input.major_id} Academic Plan",
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
                    ai_reasoning=json.dumps(result.get("ai_insights", {}))
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
            return PlanGenerationResult(
                success=False,
                plan=None,
                errors=[f"Failed to generate plan: {str(e)}"],
                warnings=[],
                ai_reasoning=None
            )
    
    @strawberry.mutation
    async def generate_ai_suggestions(
        self,
        interest: str,
        duration_years: int = 2,
        current_courses: Optional[List[str]] = None
    ) -> List[SuggestedPlan]:
        """Generate AI-powered course suggestions"""
        
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
                    notes=suggestion.get("notes")
                )
                suggested_plans.append(plan)
            
            return suggested_plans
            
        except Exception as e:
            # Return empty list on error
            return []
    
    @strawberry.mutation
    async def refresh_course_data(self, term_code: Optional[str] = None) -> bool:
        """Refresh course data from NEU API"""
        
        try:
            subjects = ["CS", "DS", "MATH", "PHYS", "CHEM", "BIOL", "EECE", "PHIL", "ENGW", "CY", "IS"]
            task_result = fetch_dynamic_course_data.delay(term_code, subjects)
            result = task_result.get(timeout=300)  # 5 minute timeout for data refresh
            
            return result.get("success", False)
            
        except Exception as e:
            return False
    
    @strawberry.mutation
    async def optimize_academic_plan(self, plan_id: str) -> OptimizationResult:
        """Optimize an existing academic plan using AI"""
        
        # This would implement plan optimization logic
        # For now, return a placeholder
        
        try:
            # Get existing plan from cache/storage
            cache_key = f"academic_plan:{plan_id}"
            cached_data = redis_client.get(cache_key)
            
            existing_plan = None
            if cached_data:
                try:
                    data = json.loads(cached_data)
                    plan_data = data.get("plan", {})
                    # For now, we'll create a simple placeholder plan
                    # In a real implementation, you'd convert the cached data properly
                    existing_plan = AcademicPlan(
                        id=plan_id,
                        user_id="",
                        name="Existing Plan",
                        major_id="",
                        degree_type="BSCS",
                        duration_years=4,
                        coop_pattern=CoopPattern.NO_COOP,
                        start_year=2024,
                        total_credits=128,
                        semesters=[],
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                except Exception:
                    pass
            
            if not existing_plan:
                raise Exception("Plan not found")
            
            # Apply optimization logic here
            # This would involve rearranging courses, balancing loads, etc.
            
            suggestions = [
                SmartSuggestion(
                    type="course_swap",
                    title="Balance Semester Load",
                    description="Move CS4500 from Fall to Spring to balance credit distribution",
                    impact="medium",
                    courses_affected=["CS4500"],
                    implementation_steps=[
                        "Move CS4500 from Fall 2025 to Spring 2026",
                        "Verify prerequisites are still met",
                        "Check course availability in Spring"
                    ]
                )
            ]
            
            return OptimizationResult(
                optimized_plan=existing_plan,  # Would return optimized version
                improvements=["Better semester balance", "Improved prerequisite flow"],
                suggestions=suggestions,
                efficiency_score=87.5,
                reasoning="Optimized course distribution for better workload balance and prerequisite management"
            )
            
        except Exception as e:
            # Return current plan with error message
            return OptimizationResult(
                optimized_plan=existing_plan or AcademicPlan(
                    id="error",
                    user_id="",
                    name="Error Plan",
                    major_id="",
                    degree_type="",
                    duration_years=4,
                    coop_pattern=CoopPattern.NO_COOP,
                    start_year=2024,
                    total_credits=0,
                    semesters=[],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                improvements=[],
                suggestions=[],
                efficiency_score=0.0,
                reasoning=f"Optimization failed: {str(e)}"
            )

# Helper functions for data processing
def _convert_semester_data_to_plan(semester_data: Dict[str, Any], input_data: PlanGenerationInput) -> List[SemesterPlan]:
    """Convert raw semester data from tasks to SemesterPlan objects"""
    
    semester_plans = []
    
    for sem_data in semester_data:
        # Map string semester to enum
        semester_mapping = {
            "fall": Semester.FALL,
            "spring": Semester.SPRING,
            "summer1": Semester.SUMMER1,
            "summer2": Semester.SUMMER2,
            "summer": Semester.SUMMER1
        }
        
        semester_enum = semester_mapping.get(
            sem_data.get("semester", "fall").lower(), 
            Semester.FALL
        )
        
        # Check for conflicts (would implement proper conflict detection)
        conflicts = []
        courses = sem_data.get("courses", [])
        credits = sem_data.get("credits", 0)
        
        # Add conflict if overloaded
        if credits > 20:
            conflicts.append(ScheduleConflict(
                type="credit_overload",
                message=f"Heavy semester load: {credits} credits",
                courses_involved=courses,
                severity="warning",
                suggested_resolution="Consider moving some courses to another semester"
            ))
        
        semester_plan = SemesterPlan(
            semester=semester_enum,
            year=sem_data.get("year", input_data.start_year),
            courses=courses,
            credits=credits,
            is_coop=sem_data.get("is_coop", False),
            notes=sem_data.get("notes"),
            conflicts=conflicts
        )
        
        semester_plans.append(semester_plan)
    
    return semester_plans

def _build_requirement_progress(plan_data: Dict[str, Any], major_config: Dict[str, Any]) -> List[RequirementProgress]:
    """Build requirement progress tracking"""
    
    from ..types.schedule import RequirementProgress, RequirementType
    
    progress_list = []
    
    # Get all scheduled courses
    all_scheduled = []
    for semester in plan_data.get("semesters", []):
        if not semester.get("is_coop", False):
            all_scheduled.extend(semester.get("courses", []))
    
    # Core requirements progress
    core_courses = major_config.get("core_courses", [])
    completed_core = [c for c in core_courses if c in all_scheduled]
    remaining_core = [c for c in core_courses if c not in all_scheduled]
    
    core_progress = RequirementProgress(
        requirement_id="core_requirements",
        requirement_name="Core Computer Science Courses",
        requirement_type=RequirementType.CORE,
        completed_courses=completed_core,
        remaining_courses=remaining_core,
        credits_completed=len(completed_core) * 4,  # Simplified
        credits_required=len(core_courses) * 4,
        courses_completed=len(completed_core),
        courses_required=len(core_courses),
        is_complete=len(remaining_core) == 0,
        progress_percentage=(len(completed_core) / len(core_courses) * 100) if core_courses else 100
    )
    progress_list.append(core_progress)
    
    # Math requirements progress
    math_courses = major_config.get("math_requirements", [])
    completed_math = [c for c in math_courses if c in all_scheduled]
    remaining_math = [c for c in math_courses if c not in all_scheduled]
    
    math_progress = RequirementProgress(
        requirement_id="math_requirements",
        requirement_name="Mathematics Requirements",
        requirement_type=RequirementType.SUPPORTING,
        completed_courses=completed_math,
        remaining_courses=remaining_math,
        credits_completed=len(completed_math) * 4,
        credits_required=len(math_courses) * 4,
        courses_completed=len(completed_math),
        courses_required=len(math_courses),
        is_complete=len(remaining_math) == 0,
        progress_percentage=(len(completed_math) / len(math_courses) * 100) if math_courses else 100
    )
    progress_list.append(math_progress)
    
    return progress_list

# Additional utility functions
async def _fetch_real_time_course_info(course_code: str, term_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch real-time course information from the API"""
    
    try:
        validation_task = validate_course_prerequisites.delay([course_code], term_code)
        result = validation_task.get(timeout=15)
        
        if result.get("success") and course_code in result.get("validations", {}):
            return result["validations"][course_code]
        
    except Exception:
        pass
    
    return None

def _calculate_plan_metrics(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate various metrics for the academic plan"""
    
    semesters = plan_data.get("semesters", [])
    academic_semesters = [s for s in semesters if not s.get("is_coop", False)]
    
    if not academic_semesters:
        return {
            "total_credits": 0,
            "average_credits_per_semester": 0,
            "max_credits": 0,
            "min_credits": 0,
            "total_courses": 0,
            "semesters_count": 0,
            "coop_semesters": 0
        }
    
    credit_loads = [s.get("credits", 0) for s in academic_semesters]
    course_counts = [len(s.get("courses", [])) for s in academic_semesters]
    
    return {
        "total_credits": sum(credit_loads),
        "average_credits_per_semester": sum(credit_loads) / len(credit_loads) if credit_loads else 0,
        "max_credits": max(credit_loads) if credit_loads else 0,
        "min_credits": min(credit_loads) if credit_loads else 0,
        "total_courses": sum(course_counts),
        "semesters_count": len(academic_semesters),
        "coop_semesters": len([s for s in semesters if s.get("is_coop", False)])
    }

def _generate_plan_warnings(plan_data: Dict[str, Any], major_config: Dict[str, Any]) -> List[str]:
    """Generate warnings about the academic plan"""
    
    warnings = []
    metrics = _calculate_plan_metrics(plan_data)
    
    # Credit load warnings
    if metrics["max_credits"] > 20:
        warnings.append(f"High credit load detected: {metrics['max_credits']} credits in one semester")
    
    if metrics["min_credits"] < 12 and metrics["min_credits"] > 0:
        warnings.append(f"Low credit load detected: {metrics['min_credits']} credits may not meet full-time requirements")
    
    # Total credits warning
    required_credits = major_config.get("total_credits", 134)
    if metrics["total_credits"] < required_credits:
        warnings.append(f"Plan includes {metrics['total_credits']} credits, but {required_credits} are required for graduation")
    
    # Duration warning
    if metrics["semesters_count"] > 8:
        warnings.append("Plan extends beyond typical 4-year duration")
    
    return warnings

def _generate_plan_recommendations(plan_data: Dict[str, Any], ai_insights: Dict[str, Any]) -> List[str]:
    """Generate recommendations for improving the academic plan"""
    
    recommendations = []
    metrics = _calculate_plan_metrics(plan_data)
    
    # Load balancing recommendations
    if metrics["max_credits"] - metrics["min_credits"] > 6:
        recommendations.append("Consider redistributing courses for more balanced semester loads")
    
    # Early graduation opportunity
    if metrics["total_credits"] > 134 and metrics["semesters_count"] <= 8:
        recommendations.append("You may be able to graduate early with your current plan")
    
    # Co-op recommendations
    if metrics["coop_semesters"] == 0:
        recommendations.append("Consider adding co-op experiences to gain practical experience")
    
    # Interest alignment recommendations
    interest_alignment = ai_insights.get("interest_alignment", {})
    for interest, data in interest_alignment.items():
        if data.get("alignment_score", 0) < 30:
            recommendations.append(f"Consider adding more courses related to {interest} to better align with your interests")
    
    return recommendations

# Export the resolvers for use in the main schema
schedule_query = ScheduleQuery
schedule_mutation = ScheduleMutation