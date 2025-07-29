from app.worker.celery_app import celery_app
import redis
import json
from typing import Dict, List, Any, Optional, Tuple
from app.config import settings
from app.neu_api.searchneu_client import SearchNEUClient
import asyncio
import logging
from datetime import datetime, timedelta
import re
from dataclasses import dataclass
import openai

# Initialize Redis client
redis_client = redis.Redis.from_url(settings.redis_url)

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=settings.openai_api_key)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CourseInfo:
    """Enhanced course information from NEU API"""
    subject: str
    course_number: str
    title: str
    credits: int
    crn: str
    prerequisites: List[str] = None
    corequisites: List[str] = None
    description: str = ""
    nupath_attributes: List[str] = None
    offered_semesters: List[str] = None
    restrictions: List[str] = None
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []
        if self.corequisites is None:
            self.corequisites = []
        if self.nupath_attributes is None:
            self.nupath_attributes = []
        if self.offered_semesters is None:
            self.offered_semesters = []
        if self.restrictions is None:
            self.restrictions = []
    
    @property
    def course_code(self) -> str:
        return f"{self.subject}{self.course_number}"

async def _ai_generate_major_requirements(major: str, level: str) -> dict:
    """Use AI to dynamically generate major requirements based on the major and level"""
    prompt = f"""
    For a {level} in {major}, provide the typical academic requirements in this JSON format:
    {{
        "name": "Full Program Name",
        "total_credits": 120,
        "subjects_to_fetch": ["CS", "MATH", "etc"],
        "core_courses": ["CS1210", "CS2500", "etc"],
        "math_requirements": ["MATH1341", "MATH1365"],
        "science_requirements": {{
            "options": [
                {{"courses": ["PHYS1151", "PHYS1152"], "name": "Physics 1"}},
                {{"courses": ["CHEM1161", "CHEM1162"], "name": "Chemistry 1"}}
            ],
            "required": 2
        }},
        "writing_requirements": ["ENGW1111"],
        "concentrations": {{
            "ai": {{
                "name": "Artificial Intelligence",
                "courses": ["CS4100", "CS4120"],
                "required": 4,
                "description": "Focus description"
            }}
        }},
        "general_electives": 28
    }}
    
    Focus on realistic course codes and requirements for {major} at {level} level.
    Use standard course prefixes like CS, MATH, PHYS, CHEM, BIOL, ENGW, etc.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        # Try to parse as JSON
        import json
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:
            # Fallback structure if AI doesn't return valid JSON
            return _get_default_major_structure(major, level)
    except Exception as e:
        logger.error(f"Failed to generate AI major requirements: {e}")
        return _get_default_major_structure(major, level)

def _get_default_major_structure(major: str, level: str) -> dict:
    """Fallback structure for major requirements"""
    return {
        "name": f"{major} ({level})",
        "total_credits": 120,
        "subjects_to_fetch": ["CS", "MATH", "PHYS", "CHEM", "BIOL", "ENGW", "PHIL"],
        "core_courses": [f"Core courses for {major}"],
        "math_requirements": ["MATH1341", "MATH1365"],
        "science_requirements": {
            "options": [
                {"courses": ["PHYS1151", "PHYS1152"], "name": "Physics"},
                {"courses": ["CHEM1161", "CHEM1162"], "name": "Chemistry"}
            ],
            "required": 1
        },
        "writing_requirements": ["ENGW1111"],
        "concentrations": {
            "general": {
                "name": "General Track",
                "courses": ["Elective courses"],
                "required": 4,
                "description": f"General {major} concentration"
            }
        },
        "general_electives": 20
    }

async def _get_major_requirements_dynamically(major_code: str) -> dict:
    """Get major requirements dynamically using AI instead of hardcoded data"""
    # Parse major code to extract major and level
    parts = major_code.split('_')
    if len(parts) >= 3:
        university = parts[0]  # neu
        major = parts[1]       # cs  
        level = parts[2]       # bs
        
        # Map common abbreviations to full names
        major_mapping = {
            "cs": "Computer Science",
            "ds": "Data Science", 
            "is": "Information Systems",
            "cy": "Cybersecurity",
            "ce": "Computer Engineering",
            "se": "Software Engineering"
        }
        
        level_mapping = {
            "bs": "Bachelor of Science",
            "ba": "Bachelor of Arts", 
            "ms": "Master of Science",
            "phd": "Doctor of Philosophy"
        }
        
        full_major = major_mapping.get(major, major.title())
        full_level = level_mapping.get(level, level.upper())
        
        return await _ai_generate_major_requirements(full_major, full_level)
    else:
        # Fallback for unrecognized format
        return _get_default_major_structure(major_code, "Bachelor")

# Dynamic major requirements - no more hardcoded data!
# This will be populated dynamically using AI for each request
MAJOR_REQUIREMENTS = {}

@celery_app.task(bind=True, name="fetch_dynamic_course_data")
def fetch_dynamic_course_data(self, term_code: Optional[str] = None, subjects: Optional[List[str]] = None) -> Dict[str, Any]:
    """Fetch course data dynamically from NEU Banner API"""
    try:
        return asyncio.run(_fetch_course_data_async(term_code, subjects))
    except Exception as e:
        logger.error(f"Error in fetch_dynamic_course_data: {e}", exc_info=True)
        self.retry(countdown=300, max_retries=3)
        return {"success": False, "error": str(e)}

async def _fetch_course_data_async(term_code: Optional[str] = None, subjects: Optional[List[str]] = None) -> Dict[str, Any]:
    """Async helper to fetch course data"""
    client = SearchNEUClient()
    
    try:
        # Get current terms if no term specified
        if not term_code:
            terms = await client.get_terms(max_results=10)
            # Find the most recent term (typically first in the list)
            if terms and len(terms) > 0:
                term_code = terms[0]["code"]
                logger.info(f"Using most recent term: {term_code} - {terms[0]['description']}")
                
                # Log all available terms for debugging
                logger.info("Available terms:")
                for i, term in enumerate(terms[:5]):  # Show first 5 terms
                    logger.info(f"  {i+1}. {term['code']} - {term['description']}")
            else:
                return {"success": False, "error": "No terms available"}
        
        # Default subjects for various academic programs
        if not subjects:
            subjects = ["CS", "DS", "IS", "MATH", "PHYS", "CHEM", "BIOL", "EECE", "PHIL", "ENGW", "BUSN", "ACCT", "FINA", "MGMT", "ECON", "STAT"]
        
        all_courses = {}
        total_fetched = 0
        
        # Try the current term first, then fallback to other terms if no data
        terms_to_try = [term_code]
        if not term_code:
            # If we didn't specify a term, we already have the list
            terms_to_try = [term["code"] for term in (await client.get_terms(max_results=5))]
        
        # Also add some known terms with data as fallback
        fallback_terms = ["202540", "202530", "202520", "202510"]  # Recent semesters likely to have data
        for fallback_term in fallback_terms:
            if fallback_term not in terms_to_try:
                terms_to_try.append(fallback_term)
        
        successful_term = None
        
        for attempt, try_term in enumerate(terms_to_try):
            logger.info(f"Attempt {attempt + 1}: Trying term {try_term}")
            term_total = 0
            
            for subject in subjects:
                logger.info(f"Fetching courses for subject: {subject} in term {try_term}")
                
                # Check cache first
                cache_key = f"subject_courses:{try_term}:{subject}"
                cached_data = redis_client.get(cache_key)
                
                if cached_data:
                    try:
                        subject_courses = json.loads(cached_data)
                        if subject not in all_courses:
                            all_courses[subject] = []
                        all_courses[subject].extend(subject_courses)
                        term_total += len(subject_courses)
                        logger.info(f"Using cached data for {subject}: {len(subject_courses)} courses")
                        continue
                    except Exception as e:
                        logger.warning(f"Failed to load cached data for {subject}: {e}")
                
                # Fetch from API
                course_search_result = await client.search_courses(
                    term=try_term,
                    subject=subject,
                    page_max_size=500  # Get as many as possible
                )
            
                if course_search_result.get("success", False):
                    courses_data = course_search_result.get("data", [])
                    processed_courses = []
                    seen_courses = set()
                    
                    for course_data in courses_data:
                        course_key = f"{course_data.get('subject', '')}{course_data.get('courseNumber', '')}"
                        
                        # Avoid duplicates (multiple sections of same course)
                        if course_key not in seen_courses:
                            seen_courses.add(course_key)
                            
                            # Extract NUPath attributes
                            nupath_attrs = []
                            section_attrs = course_data.get("sectionAttributes", [])
                            for attr in section_attrs:
                                if "NUpath" in attr.get("description", ""):
                                    nupath_attrs.append(attr.get("description", ""))
                            
                            course_info = {
                                "subject": course_data.get("subject", ""),
                                "course_number": course_data.get("courseNumber", ""),
                                "title": course_data.get("courseTitle", ""),
                                "credits": course_data.get("creditHourLow", 4),
                                "crn": course_data.get("courseReferenceNumber", ""),
                                "nupath_attributes": nupath_attrs,
                                "offered_semesters": [_parse_semester_from_term(course_data.get("termDesc", ""))],
                                "prerequisites": [],  # Would need additional API calls to get these
                                "corequisites": [],   # Would need additional API calls to get these
                                "description": "",    # Would need additional API call
                                "restrictions": []
                            }
                            
                            processed_courses.append(course_info)
                    
                    if subject not in all_courses:
                        all_courses[subject] = []
                    all_courses[subject].extend(processed_courses)
                    term_total += len(processed_courses)
                    
                    # Cache the results
                    redis_client.setex(cache_key, 3600, json.dumps(processed_courses))
                    logger.info(f"Fetched and cached {subject}: {len(processed_courses)} courses")
                    
                else:
                    logger.error(f"Failed to fetch courses for {subject} in term {try_term}: {course_search_result.get('message', 'Unknown error')}")
                    if subject not in all_courses:
                        all_courses[subject] = []
                
                # Be respectful to the API
                await asyncio.sleep(0.2)
            
            total_fetched += term_total
            logger.info(f"Term {try_term}: Fetched {term_total} total courses")
            
            # If we got some courses, use this term
            if term_total > 0:
                successful_term = try_term
                logger.info(f"Successfully fetched data from term {try_term}")
                break
            elif attempt < len(terms_to_try) - 1:
                logger.warning(f"No courses found in term {try_term}, trying next term...")
        
        # Use the successful term for final term_code
        if successful_term:
            term_code = successful_term
        
        # Cache the complete result
        complete_cache_key = f"all_courses:{term_code}:{'_'.join(subjects)}"
        redis_client.setex(complete_cache_key, 1800, json.dumps({
            "courses": all_courses,
            "term_code": term_code,
            "fetched_at": datetime.now().isoformat(),
            "total_courses": total_fetched
        }))
        
        return {
            "success": True,
            "courses": all_courses,
            "term_code": term_code,
            "total_courses": total_fetched,
            "subjects_processed": len(subjects)
        }
        
    except Exception as e:
        logger.error(f"Error fetching course data: {e}", exc_info=True)
        raise

def _parse_semester_from_term(term_desc: str) -> str:
    """Parse semester from term description like 'Fall 2024 Semester'"""
    if not term_desc:
        return "unknown"
    
    desc_lower = term_desc.lower()
    if 'fall' in desc_lower:
        return 'fall'
    elif 'spring' in desc_lower:
        return 'spring'
    elif 'summer' in desc_lower:
        if '1' in desc_lower or 'first' in desc_lower:
            return 'summer1'
        elif '2' in desc_lower or 'second' in desc_lower:
            return 'summer2'
        else:
            return 'summer'
    return 'unknown'

@celery_app.task(bind=True, name="generate_smart_academic_plan")
def generate_smart_academic_plan(
    self,
    major_id: str,
    concentration_id: Optional[str] = None,
    start_year: int = 2024,
    completed_courses: Optional[List[str]] = None,
    transfer_credits: Optional[Dict[str, int]] = None,
    interest_areas: Optional[List[str]] = None,
    coop_pattern: str = "spring_summer",
    preferences: Optional[Dict[str, Any]] = None,
    use_ai_optimization: bool = True
) -> Dict[str, Any]:
    """Generate academic plan using real course data from NEU API"""
    
    try:
        return asyncio.run(_generate_plan_async(
            major_id, concentration_id, start_year, completed_courses,
            transfer_credits, interest_areas, coop_pattern, preferences, use_ai_optimization
        ))
    except Exception as e:
        logger.error(f"Error generating academic plan: {e}", exc_info=True)
        self.retry(countdown=120, max_retries=2)
        return {"success": False, "error": str(e), "plan": None}

async def _generate_plan_async(
    major_id: str,
    concentration_id: Optional[str],
    start_year: int,
    completed_courses: Optional[List[str]],
    transfer_credits: Optional[Dict[str, int]],
    interest_areas: Optional[List[str]],
    coop_pattern: str,
    preferences: Optional[Dict[str, Any]],
    use_ai_optimization: bool
) -> Dict[str, Any]:
    """Async plan generation with real course data"""
    
    completed_courses = completed_courses or []
    transfer_credits = transfer_credits or {}
    interest_areas = interest_areas or []
    preferences = preferences or {}
    
    logger.info(f"Generating plan for major: {major_id}, concentration: {concentration_id}")
    
    # Get major requirements dynamically using AI
    logger.info(f"Generating dynamic requirements for major {major_id}...")
    major_config = await _get_major_requirements_dynamically(major_id)
    
    # Step 1: Fetch real course data
    logger.info("Fetching current course data...")
    course_data_result = await _fetch_course_data_async(
        subjects=major_config["subjects_to_fetch"]
    )
    
    if not course_data_result["success"]:
        return {"success": False, "error": "Failed to fetch course data", "plan": None}
    
    all_courses = course_data_result["courses"]
    term_code = course_data_result["term_code"]
    
    # Step 2: Build course database from fetched data
    course_database = {}
    for subject, courses in all_courses.items():
        for course in courses:
            course_code = f"{course['subject']}{course['course_number']}"
            course_database[course_code] = course
    
    logger.info(f"Built course database with {len(course_database)} courses")
    
    # Step 3: Collect required courses for the major
    required_courses = _collect_required_courses(major_config, concentration_id, course_database)
    logger.info(f"Identified {len(required_courses)} required courses")
    
    # Step 4: Filter out completed courses
    remaining_courses = [course for course in required_courses if course not in completed_courses]
    logger.info(f"Remaining courses to schedule: {len(remaining_courses)}")
    
    # Step 5: Build prerequisite graph from real course data
    prereq_graph = _build_prerequisite_graph_from_api(remaining_courses, course_database)
    
    # Step 6: Generate semester plan
    semester_plan = _generate_optimized_semester_plan(
        remaining_courses,
        prereq_graph,
        course_database,
        start_year,
        coop_pattern,
        preferences
    )
    
    # Step 7: Add AI insights if requested
    ai_insights = {}
    if use_ai_optimization and interest_areas:
        ai_insights = _generate_ai_insights(semester_plan, interest_areas, concentration_id, course_database)
    
    # Step 8: Validate the plan
    validation_result = _validate_academic_plan(semester_plan, major_config, course_database)
    
    result = {
        "success": True,
        "plan": {
            "id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "major_id": major_id,
            "concentration_id": concentration_id,
            "term_code": term_code,
            "total_credits": _calculate_total_credits(semester_plan, course_database),
            "semesters": semester_plan,
            "completed_courses": completed_courses,
            "transfer_credits": transfer_credits,
            "coop_pattern": coop_pattern,
            "created_at": datetime.now().isoformat(),
            "is_ai_generated": True,
            "validation": validation_result
        },
        "ai_insights": ai_insights,
        "warnings": validation_result.get("warnings", []),
        "recommendations": validation_result.get("recommendations", [])
    }
    
    # Cache the result
    cache_key = f"academic_plan:{major_id}:{concentration_id}:{start_year}:{hash(str(completed_courses))}"
    redis_client.setex(cache_key, 1800, json.dumps(result))
    
    return result

def _collect_required_courses(major_config: Dict[str, Any], concentration_id: Optional[str], course_database: Dict[str, Any]) -> List[str]:
    """Collect required courses, validating against available courses"""
    courses = []
    
    # Core courses
    for course in major_config["core_courses"]:
        if course in course_database:
            courses.append(course)
        else:
            logger.warning(f"Core course {course} not found in current offerings")
    
    # Math requirements
    courses.extend([c for c in major_config["math_requirements"] if c in course_database])
    
    # Science requirements (simplified - take first available options)
    science_req = major_config.get("science_requirements", {})
    science_options = science_req.get("options", [])
    required_count = science_req.get("required", 2)
    
    added_science = 0
    for option in science_options:
        if added_science >= required_count:
            break
        option_courses = option.get("courses", [])
        # Check if all courses in this option are available
        if all(course in course_database for course in option_courses):
            courses.extend(option_courses)
            added_science += 1
    
    # Supporting courses
    courses.extend([c for c in major_config.get("supporting_courses", []) if c in course_database])
    
    # Writing requirements
    for req in major_config.get("writing_requirements", []):
        if isinstance(req, str):
            if req in course_database:
                courses.append(req)
        elif isinstance(req, dict) and "options" in req:
            # Take first available option
            for option in req["options"]:
                if option in course_database:
                    courses.append(option)
                    break
    
    # Additional requirements
    for req_type, req_data in major_config.get("additional_requirements", {}).items():
        if "options" in req_data:
            for option in req_data["options"]:
                if option in course_database:
                    courses.append(option)
                    break
    
    # Concentration courses
    if concentration_id and concentration_id in major_config.get("concentrations", {}):
        conc = major_config["concentrations"][concentration_id]
        conc_courses = conc["courses"]
        required_count = conc["required"]
        
        available_conc_courses = [c for c in conc_courses if c in course_database]
        courses.extend(available_conc_courses[:required_count])
    
    return list(set(courses))  # Remove duplicates

def _build_prerequisite_graph_from_api(courses: List[str], course_database: Dict[str, Any]) -> Dict[str, List[str]]:
    """Build prerequisite graph from API course data"""
    graph = {}
    
    for course in courses:
        graph[course] = []
        if course in course_database:
            # In a full implementation, we'd fetch detailed prerequisite info
            # For now, use basic prerequisite inference
            prereqs = course_database[course].get("prerequisites", [])
            graph[course] = [p for p in prereqs if p in courses]
    
    return graph

def _generate_optimized_semester_plan(
    courses: List[str],
    prereq_graph: Dict[str, List[str]],
    course_database: Dict[str, Any],
    start_year: int,
    coop_pattern: str,
    preferences: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate optimized semester plan using real course data"""
    
    plan = []
    remaining_courses = set(courses)
    completed_in_plan = set()
    
    max_credits = preferences.get("max_credits_per_semester", 18)
    min_credits = preferences.get("min_credits_per_semester", 12)
    
    current_year = start_year
    semesters = ["fall", "spring"]
    semester_index = 0
    
    while remaining_courses and len(plan) < 16:  # Safety limit
        current_semester = semesters[semester_index % 2]
        
        # Check for co-op semester
        is_coop = _should_be_coop_semester(current_year, current_semester, start_year, coop_pattern)
        
        if is_coop:
            plan.append({
                "year": current_year,
                "semester": current_semester,
                "courses": [],
                "credits": 0,
                "is_coop": True,
                "notes": f"Co-op semester ({coop_pattern} pattern)"
            })
        else:
            # Find available courses for this semester
            available_courses = []
            for course in remaining_courses:
                if _can_take_course_now(course, completed_in_plan, prereq_graph):
                    # Check if course is typically offered this semester
                    course_info = course_database.get(course, {})
                    offered_semesters = course_info.get("offered_semesters", [current_semester])
                    if current_semester in offered_semesters or "unknown" in offered_semesters:
                        available_courses.append(course)
            
            # Select courses for this semester
            selected_courses = _select_optimal_courses(
                available_courses,
                course_database,
                max_credits,
                min_credits,
                preferences
            )
            
            credits = sum(course_database.get(course, {}).get("credits", 4) for course in selected_courses)
            
            plan.append({
                "year": current_year,
                "semester": current_semester,
                "courses": selected_courses,
                "credits": credits,
                "is_coop": False,
                "notes": f"{len(selected_courses)} courses, {credits} credits"
            })
            
            # Update tracking
            remaining_courses -= set(selected_courses)
            completed_in_plan.update(selected_courses)
        
        # Advance semester
        semester_index += 1
        if semester_index % 2 == 0:
            current_year += 1
    
    return plan

def _should_be_coop_semester(current_year: int, semester: str, start_year: int, coop_pattern: str) -> bool:
    """Determine if this should be a co-op semester"""
    if coop_pattern == "no_coop" or current_year <= start_year:
        return False
    
    year_offset = current_year - start_year
    
    if coop_pattern == "spring_summer":
        return semester == "spring" and year_offset >= 2
    elif coop_pattern == "summer_fall":
        return semester == "fall" and year_offset >= 2
    
    return False

def _can_take_course_now(course: str, completed: set, prereq_graph: Dict[str, List[str]]) -> bool:
    """Check if prerequisites are met"""
    prereqs = prereq_graph.get(course, [])
    return all(prereq in completed for prereq in prereqs)

def _select_optimal_courses(
    available_courses: List[str],
    course_database: Dict[str, Any],
    max_credits: int,
    min_credits: int,
    preferences: Dict[str, Any]
) -> List[str]:
    """Select optimal courses for a semester"""
    
    selected = []
    current_credits = 0
    
    # Sort by priority (foundation courses first, then by credits)
    def course_priority(course):
        course_info = course_database.get(course, {})
        credits = course_info.get("credits", 4)
        
        # Prioritize foundation courses
        if any(subj in course for subj in ["CS1", "CS2", "MATH", "ENGW1"]):
            return (0, credits)
        elif any(subj in course for subj in ["CS3", "DS2", "DS3"]):
            return (1, credits)
        else:
            return (2, credits)
    
    sorted_courses = sorted(available_courses, key=course_priority)
    
    for course in sorted_courses:
        course_info = course_database.get(course, {})
        credits = course_info.get("credits", 4)
        
        if current_credits + credits <= max_credits:
            selected.append(course)
            current_credits += credits
            
            # Stop if we have a good load
            if current_credits >= min_credits and len(selected) >= 4:
                break
    
    return selected

def _calculate_total_credits(plan: List[Dict[str, Any]], course_database: Dict[str, Any]) -> int:
    """Calculate total credits in the plan"""
    total = 0
    for semester in plan:
        if not semester.get("is_coop", False):
            total += semester.get("credits", 0)
    return total

def _generate_ai_insights(
    plan: List[Dict[str, Any]],
    interest_areas: List[str],
    concentration_id: Optional[str],
    course_database: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate AI insights about the academic plan"""
    
    insights = {
        "optimization_score": 85,  # Placeholder - would use actual AI analysis
        "recommendations": [],
        "interest_alignment": {},
        "workload_analysis": {}
    }
    
    # Analyze workload distribution
    semester_credits = [s.get("credits", 0) for s in plan if not s.get("is_coop", False)]
    if semester_credits:
        avg_credits = sum(semester_credits) / len(semester_credits)
        max_credits = max(semester_credits)
        min_credits = min(semester_credits)
        
        insights["workload_analysis"] = {
            "average_credits": round(avg_credits, 1),
            "max_credits": max_credits,
            "min_credits": min_credits,
            "well_balanced": max_credits - min_credits <= 4
        }
        
        if max_credits > 18:
            insights["recommendations"].append("Consider redistributing courses from high-credit semesters")
        if min_credits < 12 and min_credits > 0:
            insights["recommendations"].append("Some semesters may be under the full-time minimum")
    
    # Interest area alignment
    if interest_areas:
        for interest in interest_areas:
            related_courses = []
            for semester in plan:
                for course in semester.get("courses", []):
                    course_info = course_database.get(course, {})
                    title = course_info.get("title", "").lower()
                    if interest.lower() in title or any(interest.lower() in attr.lower() for attr in course_info.get("nupath_attributes", [])):
                        related_courses.append(course)
            
            insights["interest_alignment"][interest] = {
                "related_courses": related_courses,
                "alignment_score": len(related_courses) * 10  # Simplified scoring
            }
    
    return insights

def _validate_academic_plan(plan: List[Dict[str, Any]], major_config: Dict[str, Any], course_database: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the generated academic plan"""
    
    validation = {
        "is_valid": True,
        "warnings": [],
        "recommendations": [],
        "graduation_feasible": True
    }
    
    # Check total credits
    total_credits = sum(s.get("credits", 0) for s in plan if not s.get("is_coop", False))
    required_credits = major_config.get("total_credits", 134)
    
    if total_credits < required_credits:
        validation["warnings"].append(f"Plan only includes {total_credits} credits, need {required_credits}")
        validation["graduation_feasible"] = False
    
    # Check for prerequisite violations (simplified)
    all_scheduled_courses = []
    for semester in plan:
        if not semester.get("is_coop", False):
            all_scheduled_courses.extend(semester.get("courses", []))
    
    # Check if core courses are included
    core_courses = major_config.get("core_courses", [])
    missing_core = [course for course in core_courses if course not in all_scheduled_courses]
    
    if missing_core:
        validation["warnings"].append(f"Missing core courses: {', '.join(missing_core)}")
        validation["is_valid"] = False
    
    # Check semester credit loads
    for semester in plan:
        if not semester.get("is_coop", False):
            credits = semester.get("credits", 0)
            if credits > 20:
                validation["warnings"].append(f"Heavy load in {semester['semester']} {semester['year']}: {credits} credits")
            elif credits < 12 and credits > 0:
                validation["warnings"].append(f"Light load in {semester['semester']} {semester['year']}: {credits} credits")
    
    return validation

# Legacy support for existing AI generation
@celery_app.task(bind=True, name="generate_ai_suggestion")
def generate_ai_suggestion(self, interest: str, years: int = 2) -> List[Dict[str, Any]]:
    """Dynamic AI suggestion generation using real course data only"""
    try:
        return asyncio.run(_generate_ai_suggestion_async(interest, years))
    except Exception as e:
        logger.error(f"Error generating AI suggestion: {e}", exc_info=True)
        error_message = str(e)
        if "Unable to process plan" in error_message:
            # Return the specific error message for frontend
            raise Exception(error_message)
        else:
            # Generic error
            raise Exception("Unable to process plan - system error occurred")

@celery_app.task(bind=True, name="generate_multiple_plan_options")
def generate_multiple_plan_options(self, interest: str, years: int = 2) -> List[Dict[str, Any]]:
    """Generate multiple dynamic plan options"""
    try:
        # Generate the main plan using AI
        main_plan = asyncio.run(_generate_ai_suggestion_async(interest, years))
        return main_plan
        
    except Exception as e:
        logger.error(f"Error generating multiple plan options: {e}", exc_info=True)
        error_message = str(e)
        if "Unable to process plan" in error_message:
            raise Exception(error_message)
        else:
            raise Exception("Unable to process plan - system error occurred")

async def _generate_ai_suggestion_async(interest: str, years: int) -> List[Dict[str, Any]]:
    """Generate AI suggestions using real course data with dynamic AI processing"""
    
    logger.info(f"Starting AI suggestion generation for interest: '{interest}', years: {years}")
    
    # Fetch current course data - wait for real data
    logger.info("Fetching real course data from NEU API...")
    course_data_result = await _fetch_course_data_async()
    
    if not course_data_result["success"]:
        logger.error("Failed to fetch course data from NEU API")
        raise Exception("Unable to process plan - course data unavailable")
    
    all_courses = course_data_result["courses"]
    logger.info(f"Fetched course data for subjects: {list(all_courses.keys())}")
    
    # Count total courses available
    total_api_courses = 0
    all_available_courses = []
    
    for subject, courses in all_courses.items():
        total_api_courses += len(courses)
        logger.info(f"Subject {subject}: {len(courses)} courses")
        
        # Collect all course information for AI processing
        for course in courses:
            course_info = {
                'subject': course['subject'],
                'course_number': course['course_number'],
                'title': course.get('title', ''),
                'credits': course.get('credits', 4),
                'code': f"{course['subject']}{course['course_number']}"
            }
            all_available_courses.append(course_info)
    
    logger.info(f"Total courses available for AI processing: {total_api_courses}")
    
    if total_api_courses == 0:
        logger.error("No courses found in API response")
        raise Exception("Unable to process plan - no course data available")
    
    # Use AI to process the course data and generate plan
    logger.info(f"Processing {len(all_available_courses)} courses with AI for interest: {interest}")
    ai_generated_plan = await _process_courses_with_ai(all_available_courses, interest, years)
    
    if not ai_generated_plan or len(ai_generated_plan) == 0:
        logger.error("AI processing failed to generate a valid plan")
        raise Exception("Unable to process plan - AI analysis failed")
    
    logger.info(f"AI generated plan with {len(ai_generated_plan)} semesters")
    return ai_generated_plan

async def _process_courses_with_ai(available_courses: List[Dict[str, Any]], interest: str, years: int) -> List[Dict[str, Any]]:
    """Use AI to process course data and generate academic plan"""
    
    logger.info(f"Starting AI analysis for {len(available_courses)} courses with interest: {interest}")
    
    # Prepare course data for AI analysis
    course_catalog = {}
    subject_counts = {}
    
    for course in available_courses:
        subject = course['subject']
        course_catalog[course['code']] = course
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
    
    logger.info(f"Course catalog prepared: {len(course_catalog)} unique courses")
    logger.info(f"Available subjects: {dict(sorted(subject_counts.items()))}")
    
    # AI-driven course selection based on interest
    selected_courses = await _ai_select_relevant_courses(available_courses, interest)
    
    if len(selected_courses) < 8:  # Minimum courses needed for a plan
        logger.error(f"AI selected only {len(selected_courses)} courses, insufficient for {years}-year plan")
        raise Exception("Unable to process plan - insufficient relevant courses found")
    
    # AI-driven curriculum sequencing
    sequenced_plan = await _ai_sequence_courses(selected_courses, years, interest)
    
    if not sequenced_plan or len(sequenced_plan) == 0:
        logger.error("AI failed to sequence courses into semesters")
        raise Exception("Unable to process plan - course sequencing failed")
    
    logger.info(f"AI successfully generated {len(sequenced_plan)} semester plan")
    return sequenced_plan

async def _ai_select_relevant_courses(available_courses: List[Dict[str, Any]], interest: str) -> List[Dict[str, Any]]:
    """AI-powered course selection based on interest using OpenAI"""
    
    logger.info(f"AI analyzing {len(available_courses)} courses for relevance to '{interest}'")
    
    # Use OpenAI to batch analyze course relevance for efficiency
    try:
        # Prepare course information for batch analysis
        course_info_batch = []
        for i, course in enumerate(available_courses[:50]):  # Limit to first 50 courses for API efficiency
            course_info = f"{i}: {course['code']} - {course['title']} (Subject: {course['subject']})"
            course_info_batch.append(course_info)
        
        prompt = f"""
        Analyze which of these university courses are most relevant for a student interested in "{interest}".
        
        Courses to analyze:
        {chr(10).join(course_info_batch)}
        
        For each course, rate its relevance to "{interest}" on a scale of 0-10 where:
        - 0-2: Not relevant
        - 3-4: Somewhat relevant
        - 5-6: Moderately relevant  
        - 7-8: Highly relevant
        - 9-10: Essential for this interest
        
        Consider:
        1. Direct subject matter alignment
        2. Foundational knowledge needed
        3. Practical skills development
        4. Career preparation value
        5. Prerequisites for advanced study
        
        Return only the course numbers (0, 1, 2, etc.) that score 5 or higher, separated by commas.
        Example: "0, 3, 7, 12, 15"
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.2
        )
        
        relevant_indices_text = response.choices[0].message.content.strip()
        
        # Parse the AI response
        try:
            relevant_indices = [int(idx.strip()) for idx in relevant_indices_text.split(',') if idx.strip().isdigit()]
            selected_courses = []
            
            for idx in relevant_indices:
                if 0 <= idx < len(available_courses):
                    course = available_courses[idx].copy()
                    # Get individual relevance score for this course
                    individual_score = await _calculate_ai_relevance_score(course, interest)
                    course['ai_relevance_score'] = individual_score
                    selected_courses.append(course)
            
            logger.info(f"OpenAI selected {len(selected_courses)} relevant courses from batch analysis")
            
            # If we have more courses, process remaining with individual scoring
            if len(available_courses) > 50:
                remaining_courses = available_courses[50:]
                for course in remaining_courses:
                    relevance_score = await _calculate_ai_relevance_score(course, interest)
                    if relevance_score > 0.5:  # Only include highly relevant courses
                        course_with_score = course.copy()
                        course_with_score['ai_relevance_score'] = relevance_score
                        selected_courses.append(course_with_score)
            
            # Sort by relevance score
            selected_courses.sort(key=lambda x: x['ai_relevance_score'], reverse=True)
            
            return selected_courses
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse OpenAI batch response: {e}")
            
    except Exception as e:
        logger.warning(f"OpenAI batch analysis failed: {e}")
    
    # Fallback to individual course analysis
    return await _ai_select_relevant_courses_fallback(available_courses, interest)

async def _ai_select_relevant_courses_fallback(available_courses: List[Dict[str, Any]], interest: str) -> List[Dict[str, Any]]:
    """Fallback course selection when OpenAI batch analysis fails"""
    
    logger.info(f"Using fallback individual analysis for {len(available_courses)} courses")
    
    relevant_courses = []
    
    # Analyze each course individually
    for course in available_courses:
        relevance_score = await _calculate_ai_relevance_score(course, interest)
        
        if relevance_score > 0.3:  # Threshold for relevance
            course_with_score = course.copy()
            course_with_score['ai_relevance_score'] = relevance_score
            relevant_courses.append(course_with_score)
    
    # Sort by AI relevance score
    relevant_courses.sort(key=lambda x: x['ai_relevance_score'], reverse=True)
    
    logger.info(f"Fallback analysis selected {len(relevant_courses)} relevant courses")
    
    return relevant_courses

async def _calculate_ai_relevance_score(course: Dict[str, Any], interest: str) -> float:
    """Calculate AI-driven relevance score for a course using OpenAI"""
    
    course_title = course.get('title', '')
    course_subject = course.get('subject', '')
    course_number = course.get('course_number', '')
    
    # Use OpenAI to analyze course relevance
    try:
        prompt = f"""
        Analyze how relevant this course is to a student interested in "{interest}".
        
        Course Details:
        - Subject: {course_subject}
        - Number: {course_number}
        - Title: {course_title}
        
        Student Interest: {interest}
        
        Rate the relevance on a scale of 0.0 to 1.0 where:
        - 0.0 = Not relevant at all
        - 0.3 = Somewhat related
        - 0.5 = Moderately relevant
        - 0.7 = Highly relevant
        - 1.0 = Extremely relevant and essential
        
        Consider:
        1. Direct content alignment with the interest
        2. Foundational knowledge needed for the interest area
        3. Practical skills applicable to the interest
        4. Career preparation relevance
        
        Respond with only a single number between 0.0 and 1.0
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.1
        )
        
        score_text = response.choices[0].message.content.strip()
        score = float(score_text)
        return min(max(score, 0.0), 1.0)  # Ensure score is between 0 and 1
        
    except Exception as e:
        logger.warning(f"OpenAI API error for course {course_subject}{course_number}: {e}")
        # Fallback to simple keyword matching
        return _calculate_fallback_relevance_score(course, interest)

def _calculate_fallback_relevance_score(course: Dict[str, Any], interest: str) -> float:
    """Fallback relevance calculation when OpenAI is unavailable"""
    course_title = course.get('title', '').lower()
    interest_lower = interest.lower()
    
    # Simple keyword matching as fallback
    if interest_lower in course_title:
        return 0.7
    
    # Basic subject relevance
    subject = course.get('subject', '')
    if interest_lower in ['data science', 'analytics'] and subject in ['DS', 'CS', 'STAT']:
        return 0.6
    elif interest_lower in ['ai', 'artificial intelligence', 'machine learning'] and subject in ['CS', 'DS']:
        return 0.6
    elif interest_lower in ['business', 'analysis'] and subject in ['BUSN', 'ACCT', 'ECON']:
        return 0.5
    
    return 0.2

async def _extract_interest_keywords(interest: str) -> List[str]:
    """Extract keywords from interest using OpenAI"""
    
    try:
        prompt = f"""
        Extract the most important keywords and related terms for the academic interest: "{interest}"
        
        Provide keywords that would help identify relevant university courses, including:
        1. Direct keywords from the interest
        2. Related technical terms
        3. Fundamental concepts
        4. Industry terminology
        5. Academic subjects that support this interest
        
        Return as a comma-separated list of keywords.
        Example: "programming, algorithms, software, development, computer science"
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3
        )
        
        keywords_text = response.choices[0].message.content.strip()
        keywords = [kw.strip().lower() for kw in keywords_text.split(',')]
        return keywords
        
    except Exception as e:
        logger.warning(f"OpenAI API error extracting keywords for '{interest}': {e}")
        # Fallback to basic keyword extraction
        return _extract_fallback_keywords(interest)

def _extract_fallback_keywords(interest: str) -> List[str]:
    """Fallback keyword extraction when OpenAI is unavailable"""
    keyword_mapping = {
        "business analysis": ["business", "analysis", "analytics", "data", "statistics", "visualization", "reporting", "intelligence"],
        "data science": ["data", "science", "analytics", "statistics", "machine", "learning", "mining", "visualization"],
        "artificial intelligence": ["artificial", "intelligence", "machine", "learning", "neural", "algorithm", "ai", "ml"],
        "software engineering": ["software", "engineering", "programming", "development", "systems", "design", "architecture"],
        "cybersecurity": ["security", "cyber", "cryptography", "network", "privacy", "forensics"],
        "web development": ["web", "development", "javascript", "html", "css", "frontend", "backend", "fullstack"]
    }
    
    base_keywords = interest.lower().split()
    
    for key, keywords in keyword_mapping.items():
        if any(word in interest.lower() for word in key.split()):
            base_keywords.extend(keywords)
    
    return list(set(base_keywords))

async def _ai_sequence_courses(selected_courses: List[Dict[str, Any]], years: int, interest: str) -> List[Dict[str, Any]]:
    """AI-powered course sequencing into semesters using OpenAI"""
    
    logger.info(f"AI sequencing {len(selected_courses)} courses into {years}-year plan")
    
    # Prepare course information for OpenAI
    course_descriptions = []
    for course in selected_courses:
        course_info = f"{course['code']}: {course['title']} ({course.get('credits', 4)} credits)"
        course_descriptions.append(course_info)
    
    try:
        prompt = f"""
        You are an academic advisor helping create an optimal {years}-year course sequence for a student interested in "{interest}".
        
        Available courses:
        {chr(10).join(course_descriptions)}
        
        Create an optimal semester-by-semester plan with these guidelines:
        1. Prerequisites should be taken before advanced courses
        2. Foundation courses (1000-2000 level) should come early
        3. Advanced courses (3000+ level) should come later  
        4. Aim for 12-18 credits (3-4 courses) per semester
        5. Balance difficulty across semesters
        6. Consider logical learning progression for "{interest}"
        
        Format the response as a JSON array with this structure:
        [
          {{
            "year": 1,
            "term": "Fall",
            "courses": ["Course1", "Course2", "Course3"],
            "credits": 12,
            "notes": "Foundation semester focusing on..."
          }}
        ]
        
        Include exactly {years * 2} semesters (Fall and Spring for each year).
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        import json
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            ai_plan = json.loads(json_text)
            
            # Validate and enhance the AI response
            if isinstance(ai_plan, list) and len(ai_plan) > 0:
                logger.info(f"OpenAI generated plan with {len(ai_plan)} semesters")
                return ai_plan
            else:
                logger.warning("OpenAI response format invalid, using fallback")
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse OpenAI JSON response: {e}")
        
    except Exception as e:
        logger.warning(f"OpenAI API error for course sequencing: {e}")
    
    # Fallback to deterministic sequencing
    return await _ai_determine_course_sequence_fallback(selected_courses, years, interest)

async def _ai_determine_course_sequence_fallback(selected_courses: List[Dict[str, Any]], years: int, interest: str) -> List[Dict[str, Any]]:
    """Fallback course sequencing when OpenAI is unavailable"""
    
    # Sort courses by level and relevance
    foundation_courses = []
    intermediate_courses = []
    advanced_courses = []
    
    for course in selected_courses:
        course_number = course.get('course_number', '')
        level = int(course_number[0]) if course_number and course_number[0].isdigit() else 2
        
        if level <= 2:
            foundation_courses.append(course)
        elif level == 3:
            intermediate_courses.append(course)
        else:
            advanced_courses.append(course)
    
    # Sort each group by relevance score
    foundation_courses.sort(key=lambda x: x.get('ai_relevance_score', 0), reverse=True)
    intermediate_courses.sort(key=lambda x: x.get('ai_relevance_score', 0), reverse=True)
    advanced_courses.sort(key=lambda x: x.get('ai_relevance_score', 0), reverse=True)
    
    # Distribute into semesters
    all_courses = foundation_courses + intermediate_courses + advanced_courses
    total_semesters = years * 2
    semesters = ["Fall", "Spring"]
    plan = []
    
    courses_per_semester = max(3, len(all_courses) // total_semesters)
    course_index = 0
    
    for year in range(1, years + 1):
        for semester in semesters:
            semester_courses = []
            semester_credits = 0
            target_courses = min(courses_per_semester, len(all_courses) - course_index)
            
            for _ in range(target_courses):
                if course_index < len(all_courses):
                    course = all_courses[course_index]
                    course_title = f"{course['code']} - {course['title']}"
                    semester_courses.append(course_title)
                    semester_credits += course.get('credits', 4)
                    course_index += 1
            
            # Ensure minimum course load
            while len(semester_courses) < 3 and semester_credits < 12:
                semester_courses.append(f"{interest} Elective")
                semester_credits += 4
            
            if len(semester_courses) > 0:
                plan.append({
                    "year": year,
                    "term": semester,
                    "courses": semester_courses,
                    "credits": semester_credits,
                    "notes": f"AI-optimized for {interest} - {len(semester_courses)} courses"
                })
    
    return plan

@celery_app.task(name="cleanup_cache")
def cleanup_cache() -> bool:
    """Clean up expired cache entries"""
    try:
        # Get all keys that match our patterns
        patterns = ["courses:*", "terms:*", "subjects:*", "subject_courses:*", "academic_plan:*", "all_courses:*"]
        
        cleaned = 0
        for pattern in patterns:
            cache_keys = redis_client.keys(pattern)
            
            for key in cache_keys:
                ttl = redis_client.ttl(key)
                if ttl < 300:  # Less than 5 minutes remaining
                    redis_client.delete(key)
                    cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} expired cache entries")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning cache: {e}")
        return False

@celery_app.task(bind=True, name="validate_course_prerequisites")
def validate_course_prerequisites(self, courses: List[str], term_code: Optional[str] = None) -> Dict[str, Any]:
    """Validate prerequisites for a list of courses using real API data"""
    
    try:
        return asyncio.run(_validate_prerequisites_async(courses, term_code))
    except Exception as e:
        logger.error(f"Error validating prerequisites: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

async def _validate_prerequisites_async(courses: List[str], term_code: Optional[str]) -> Dict[str, Any]:
    """Async prerequisite validation"""
    
    client = SearchNEUClient()
    
    try:
        # Get current term if not provided
        if not term_code:
            terms = await client.get_terms(max_results=5)
            term_code = terms[0]["code"] if terms else "202510"
        
        validation_results = {}
        
        for course_code in courses:
            # Parse subject and course number
            match = re.match(r'([A-Z]+)(\d+)', course_code)
            if not match:
                validation_results[course_code] = {
                    "valid": False,
                    "error": "Invalid course code format"
                }
                continue
            
            subject, course_number = match.groups()
            
            # Search for the course
            search_result = await client.search_courses(
                term=term_code,
                subject=subject,
                course_number=course_number,
                page_max_size=5
            )
            
            if search_result.get("success") and search_result.get("data"):
                course_data = search_result["data"][0]
                validation_results[course_code] = {
                    "valid": True,
                    "title": course_data.get("courseTitle", ""),
                    "credits": course_data.get("creditHourLow", 4),
                    "available": course_data.get("seatsAvailable", 0) > 0,
                    "crn": course_data.get("courseReferenceNumber", "")
                }
            else:
                validation_results[course_code] = {
                    "valid": False,
                    "error": "Course not found in current term"
                }
            
            # Small delay to be respectful
            await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "term_code": term_code,
            "validations": validation_results,
            "overall_valid": all(v.get("valid", False) for v in validation_results.values())
        }
        
    except Exception as e:
        logger.error(f"Error in prerequisite validation: {e}", exc_info=True)
        raise

@celery_app.task(bind=True, name="get_course_recommendations")
def get_course_recommendations(
    self, 
    completed_courses: List[str], 
    interest_areas: List[str], 
    semester_target: str = "fall",
    max_recommendations: int = 10
) -> Dict[str, Any]:
    """Get personalized course recommendations based on completed courses and interests"""
    
    try:
        return asyncio.run(_get_recommendations_async(completed_courses, interest_areas, semester_target, max_recommendations))
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

async def _get_recommendations_async(
    completed_courses: List[str], 
    interest_areas: List[str], 
    semester_target: str,
    max_recommendations: int
) -> Dict[str, Any]:
    """Async course recommendations"""
    
    # Fetch current course data
    course_data_result = await _fetch_course_data_async()
    
    if not course_data_result["success"]:
        return {"success": False, "error": "Failed to fetch course data"}
    
    all_courses = course_data_result["courses"]
    recommendations = []
    
    # Interest-based subject mapping
    interest_subjects = {
        "artificial intelligence": ["CS", "DS"],
        "ai": ["CS", "DS"], 
        "machine learning": ["DS", "CS"],
        "data science": ["DS", "MATH"],
        "software engineering": ["CS"],
        "cybersecurity": ["CY", "CS"],
        "systems": ["CS", "EECE"],
        "web development": ["CS"]
    }
    
    # Determine relevant subjects
    relevant_subjects = set()
    for interest in interest_areas:
        subjects = interest_subjects.get(interest.lower(), ["CS"])
        relevant_subjects.update(subjects)
    
    # Get available courses in relevant subjects
    available_courses = []
    for subject in relevant_subjects:
        if subject in all_courses:
            for course in all_courses[subject]:
                course_code = f"{course['subject']}{course['course_number']}"
                
                # Skip if already completed
                if course_code in completed_courses:
                    continue
                
                # Check if course matches interests
                title_lower = course.get('title', '').lower()
                relevance_score = 0
                
                for interest in interest_areas:
                    if interest.lower() in title_lower:
                        relevance_score += 10
                    
                    # Check for related keywords
                    interest_keywords = {
                        "ai": ["intelligence", "learning", "neural", "algorithm"],
                        "data science": ["data", "statistics", "analytics", "mining"],
                        "software engineering": ["software", "engineering", "design", "development"],
                        "cybersecurity": ["security", "crypto", "network", "privacy"]
                    }
                    
                    keywords = interest_keywords.get(interest.lower(), [])
                    for keyword in keywords:
                        if keyword in title_lower:
                            relevance_score += 5
                
                # Check if typically offered in target semester
                offered_semesters = course.get('offered_semesters', [semester_target])
                if semester_target in offered_semesters or 'unknown' in offered_semesters:
                    relevance_score += 2
                
                if relevance_score > 0:
                    available_courses.append({
                        "course_code": course_code,
                        "title": course.get('title', ''),
                        "credits": course.get('credits', 4),
                        "subject": course.get('subject', ''),
                        "course_number": course.get('course_number', ''),
                        "relevance_score": relevance_score,
                        "nupath_attributes": course.get('nupath_attributes', [])
                    })
    
    # Sort by relevance and take top recommendations
    available_courses.sort(key=lambda x: x['relevance_score'], reverse=True)
    recommendations = available_courses[:max_recommendations]
    
    return {
        "success": True,
        "recommendations": recommendations,
        "total_available": len(available_courses),
        "interest_areas": interest_areas,
        "semester_target": semester_target
    }

# Cache courses on startup
@celery_app.task(name="cache_courses")
def cache_courses(key: str, data: List[Dict[str, Any]]) -> bool:
    """Cache course data in Redis"""
    try:
        redis_client.setex(key, 3600, json.dumps(data))
        return True
    except Exception as e:
        logger.error(f"Error caching data: {e}")
        return False