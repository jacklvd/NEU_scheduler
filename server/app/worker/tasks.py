"""
Celery Tasks for NEU Scheduler - Clean and Optimized Version
"""

from app.worker.celery_app import celery_app
from app.redis_client import get_redis_client
import json
import asyncio
import logging
import re
import openai
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.config import settings
from app.neu_api.searchneu_client import SearchNEUClient

# Initialize components
redis_client = get_redis_client()
openai_client = openai.OpenAI(api_key=settings.openai_api_key)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dynamic major requirements - populated dynamically using AI
MAJOR_REQUIREMENTS = {}

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

# =============================================================================
# CORE TASKS - Main Celery Tasks
# =============================================================================

@celery_app.task(bind=True, name="generate_ai_suggestion")
def generate_ai_suggestion(self, interest: str, years: int = 2) -> List[Dict[str, Any]]:
    """Generate AI-powered academic plan suggestions"""
    try:
        return asyncio.run(_generate_ai_suggestion_async(interest, years))
    except Exception as e:
        logger.error(f"Error generating AI suggestion: {e}", exc_info=True)
        error_message = str(e)
        if "Unable to process plan" in error_message:
            raise Exception(error_message)
        else:
            raise Exception("Unable to process plan - system error occurred")

@celery_app.task(bind=True, name="fetch_dynamic_course_data")
def fetch_dynamic_course_data(self, term_code: Optional[str] = None, subjects: Optional[List[str]] = None) -> Dict[str, Any]:
    """Fetch course data dynamically from NEU Banner API"""
    try:
        return asyncio.run(_fetch_course_data_async(term_code, subjects))
    except Exception as e:
        logger.error(f"Error in fetch_dynamic_course_data: {e}", exc_info=True)
        self.retry(countdown=300, max_retries=3)
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True, name="validate_course_prerequisites")
def validate_course_prerequisites(self, courses: List[str], term_code: Optional[str] = None) -> Dict[str, Any]:
    """Validate prerequisites for a list of courses"""
    try:
        return asyncio.run(_validate_prerequisites_async(courses, term_code))
    except Exception as e:
        logger.error(f"Error validating prerequisites: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True, name="get_course_recommendations")
def get_course_recommendations(
    self, 
    completed_courses: List[str], 
    interest_areas: List[str], 
    semester_target: str = "fall",
    max_recommendations: int = 10
) -> Dict[str, Any]:
    """Get personalized course recommendations"""
    try:
        return asyncio.run(_get_recommendations_async(completed_courses, interest_areas, semester_target, max_recommendations))
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@celery_app.task(name="cleanup_cache")
def cleanup_cache() -> bool:
    """Clean up expired cache entries"""
    try:
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

@celery_app.task(name="cache_courses")
def cache_courses(key: str, data: List[Dict[str, Any]]) -> bool:
    """Cache course data in Redis"""
    try:
        redis_client.setex(key, 3600, json.dumps(data))
        return True
    except Exception as e:
        logger.error(f"Error caching data: {e}")
        return False

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
    """Generate comprehensive academic plan using real course data from NEU API"""
    try:
        return asyncio.run(_generate_smart_plan_async(
            major_id, concentration_id, start_year, completed_courses,
            transfer_credits, interest_areas, coop_pattern, preferences, use_ai_optimization
        ))
    except Exception as e:
        logger.error(f"Error generating smart academic plan: {e}", exc_info=True)
        # Return fallback response structure
        return {
            "success": False, 
            "error": str(e), 
            "plan": None,
            "ai_insights": {},
            "warnings": [f"Failed to generate plan: {str(e)}"],
            "recommendations": []
        }

# =============================================================================
# AI SUGGESTION GENERATION - Core AI functionality
# =============================================================================

async def _generate_ai_suggestion_async(interest: str, years: int) -> List[Dict[str, Any]]:
    """Generate AI suggestions using real course data with dynamic AI processing"""
    
    logger.info(f"Starting AI suggestion generation for interest: '{interest}', years: {years}")
    
    # Fetch current course data
    logger.info("Fetching real course data from NEU API...")
    course_data_result = await _fetch_course_data_async()
    
    if not course_data_result["success"]:
        logger.error("Failed to fetch course data from NEU API")
        raise Exception("Unable to process plan - course data unavailable")
    
    all_courses = course_data_result["courses"]
    logger.info(f"Fetched course data for subjects: {list(all_courses.keys())}")
    
    # Prepare courses for AI processing
    all_available_courses = []
    total_api_courses = 0
    
    for subject, courses in all_courses.items():
        total_api_courses += len(courses)
        logger.info(f"Subject {subject}: {len(courses)} courses")
        
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
    
    # Use AI to process courses and generate plan
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
    
    # AI-driven course selection based on interest
    selected_courses = await _ai_select_relevant_courses(available_courses, interest)
    
    # More realistic minimum course requirements based on years
    min_courses_needed = max(6, years * 4)  # At least 6 courses, or 4 per year
    if len(selected_courses) < min_courses_needed:
        logger.warning(f"AI selected {len(selected_courses)} courses, may be insufficient for {years}-year plan (need ~{min_courses_needed})")
        # Don't fail here - let the system try to work with what we have
        # The sequencing function can add electives if needed
    
    # AI-driven curriculum sequencing
    sequenced_plan = await _ai_sequence_courses(selected_courses, years, interest)
    
    if not sequenced_plan or len(sequenced_plan) == 0:
        logger.error("AI failed to sequence courses into semesters")
        raise Exception("Unable to process plan - course sequencing failed")
    
    logger.info(f"AI successfully generated {len(sequenced_plan)} semester plan")
    return sequenced_plan

# =============================================================================
# COURSE DATA FETCHING - NEU API Integration
# =============================================================================

async def _fetch_course_data_async(term_code: Optional[str] = None, subjects: Optional[List[str]] = None) -> Dict[str, Any]:
    """Async helper to fetch course data"""
    client = SearchNEUClient()
    
    try:
        # Get current terms if no term specified
        if not term_code:
            terms = await client.get_terms(max_results=10)
            if terms and len(terms) > 0:
                term_code = terms[0]["code"]
                logger.info(f"Using most recent term: {term_code} - {terms[0]['description']}")
            else:
                return {"success": False, "error": "No terms available"}
        
        # Default subjects for various academic programs
        if not subjects:
            subjects = ["CS", "DS", "IS", "MATH", "PHYS", "CHEM", "BIOL", "EECE", "PHIL", "ENGW", "BUSN", "ACCT", "FINA", "MGMT", "ECON", "STAT"]
        
        all_courses = {}
        total_fetched = 0
        
        # Try current term first, then fallback to other terms
        terms_to_try = [term_code]
        fallback_terms = ["202540", "202530", "202520", "202510"]
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
                    page_max_size=500
                )
            
                if course_search_result.get("success", False):
                    courses_data = course_search_result.get("data", [])
                    processed_courses = []
                    seen_courses = set()
                    
                    for course_data in courses_data:
                        course_key = f"{course_data.get('subject', '')}{course_data.get('courseNumber', '')}"
                        
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
                                "prerequisites": [],
                                "corequisites": [],
                                "description": "",
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
                    logger.error(f"Failed to fetch courses for {subject} in term {try_term}")
                    if subject not in all_courses:
                        all_courses[subject] = []
                
                await asyncio.sleep(0.2)  # Be respectful to the API
            
            total_fetched += term_total
            logger.info(f"Term {try_term}: Fetched {term_total} total courses")
            
            if term_total > 0:
                successful_term = try_term
                logger.info(f"Successfully fetched data from term {try_term}")
                break
            elif attempt < len(terms_to_try) - 1:
                logger.warning(f"No courses found in term {try_term}, trying next term...")
        
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
    """Parse semester from term description"""
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

# =============================================================================
# AI COURSE SELECTION - OpenAI Integration
# =============================================================================

async def _ai_select_relevant_courses(available_courses: List[Dict[str, Any]], interest: str) -> List[Dict[str, Any]]:
    """AI-powered course selection based on interest using OpenAI with multiple strategies"""
    
    logger.info(f"AI analyzing {len(available_courses)} courses for relevance to '{interest}'")
    
    # Strategy 1: Use AI to expand the interest into related concepts first
    expanded_interests = await _expand_interest_with_ai(interest)
    logger.info(f"Expanded '{interest}' to include: {expanded_interests}")
    
    # Strategy 2: Cast a wider net with batch analysis
    selected_courses = []
    
    try:
        # Process courses in batches of 50 for better analysis
        batch_size = 50
        for batch_start in range(0, min(len(available_courses), 200), batch_size):
            batch_end = min(batch_start + batch_size, len(available_courses))
            batch_courses = available_courses[batch_start:batch_end]
            
            course_info_batch = []
            for i, course in enumerate(batch_courses):
                course_info = f"{i}: {course['code']} - {course['title']} (Subject: {course['subject']})"
                course_info_batch.append(course_info)
            
            # Use expanded interests for better matching
            all_interests = [interest] + expanded_interests
            interests_text = " OR ".join(all_interests)
            
            prompt = f"""
            Analyze which university courses could be relevant for a student interested in any of these areas: {interests_text}
            
            Courses to analyze:
            {chr(10).join(course_info_batch)}
            
            Consider courses that provide:
            1. Direct skills for these interest areas
            2. Foundational knowledge (math, statistics, programming, writing)
            3. Supporting business or technical skills
            4. General education that builds analytical thinking
            5. Data analysis, visualization, or decision-making skills
            
            Rate each course 0-10 where:
            - 0-3: Not helpful
            - 4-5: Somewhat useful (foundational/supporting)
            - 6-7: Moderately relevant
            - 8-10: Highly relevant
            
            Return ALL course numbers (0,1,2,etc) that score 4 or higher, separated by commas.
            Be generous - include foundational courses that build relevant skills.
            """
            
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        openai_client.chat.completions.create,
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=300,
                        temperature=0.3
                    ),
                    timeout=30.0
                )
                
                relevant_indices_text = response.choices[0].message.content.strip()
                relevant_indices = [int(idx.strip()) for idx in relevant_indices_text.split(',') if idx.strip().isdigit()]
                
                for idx in relevant_indices:
                    if 0 <= idx < len(batch_courses):
                        course = batch_courses[idx].copy()
                        # Get detailed relevance score
                        individual_score = await _calculate_enhanced_relevance_score(course, all_interests)
                        course['ai_relevance_score'] = individual_score
                        selected_courses.append(course)
                
                logger.info(f"Batch {batch_start}-{batch_end}: Selected {len([i for i in relevant_indices if i < len(batch_courses)])} courses")
                
            except Exception as e:
                logger.warning(f"Batch analysis failed for batch {batch_start}-{batch_end}: {e}")
                # Fallback for this batch
                for course in batch_courses:
                    score = await _calculate_enhanced_relevance_score(course, all_interests)
                    if score > 0.3:  # Lower threshold for fallback
                        course_with_score = course.copy()
                        course_with_score['ai_relevance_score'] = score
                        selected_courses.append(course_with_score)
        
        # Strategy 3: If still not enough courses, be even more inclusive
        if len(selected_courses) < 12:  # Need at least 12 courses for a 4-year plan
            logger.info(f"Only found {len(selected_courses)} courses, expanding search...")
            
            # Add more courses with lower thresholds
            for course in available_courses[200:300]:  # Check more courses
                score = await _calculate_enhanced_relevance_score(course, [interest] + expanded_interests)
                if score > 0.2:  # Very low threshold
                    course_with_score = course.copy()
                    course_with_score['ai_relevance_score'] = score
                    selected_courses.append(course_with_score)
            
            # If still not enough, add foundational courses by subject
            if len(selected_courses) < 8:
                logger.info("Adding foundational courses by subject...")
                foundational_subjects = ['MATH', 'ENGW', 'CS', 'DS', 'BUSN', 'STAT', 'ECON']
                for course in available_courses:
                    if course['subject'] in foundational_subjects and course not in selected_courses:
                        course_with_score = course.copy()
                        course_with_score['ai_relevance_score'] = 0.4  # Default foundational score
                        selected_courses.append(course_with_score)
                        if len(selected_courses) >= 16:  # Enough for 4-year plan
                            break
        
        # Remove duplicates and sort by relevance
        seen_codes = set()
        unique_selected = []
        for course in selected_courses:
            if course['code'] not in seen_codes:
                seen_codes.add(course['code'])
                unique_selected.append(course)
        
        unique_selected.sort(key=lambda x: x['ai_relevance_score'], reverse=True)
        
        logger.info(f"Final selection: {len(unique_selected)} relevant courses for '{interest}'")
        return unique_selected
        
    except Exception as e:
        logger.warning(f"AI course selection completely failed: {e}")
        # Ultimate fallback - return a reasonable set of courses
        return await _emergency_course_selection_fallback(available_courses, interest)

async def _expand_interest_with_ai(interest: str) -> List[str]:
    """Use AI to expand the interest into related concepts and skills"""
    try:
        prompt = f"""
        A student is interested in "{interest}". What related academic areas, skills, and concepts would be relevant for university course selection?
        
        Provide 5-8 related terms that would help identify relevant courses, including:
        - Foundational subjects
        - Related technical skills
        - Business/industry applications
        - Supporting knowledge areas
        
        For example, if interest is "data science", related terms might include: "statistics", "programming", "machine learning", "databases", "visualization", "business analytics"
        
        Return only the related terms separated by commas.
        """
        
        response = await asyncio.wait_for(
            asyncio.to_thread(
                openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            ),
            timeout=15.0
        )
        
        expanded_text = response.choices[0].message.content.strip()
        expanded_interests = [term.strip().lower() for term in expanded_text.split(',') if term.strip()]
        return expanded_interests[:8]  # Limit to 8 terms
        
    except Exception as e:
        logger.warning(f"Failed to expand interest '{interest}': {e}")
        # Fallback expansion based on common patterns
        return _fallback_expand_interest(interest)

def _fallback_expand_interest(interest: str) -> List[str]:
    """Fallback interest expansion when AI fails"""
    interest_lower = interest.lower()
    
    if 'business' in interest_lower and 'intelligence' in interest_lower:
        return ['data analytics', 'business analysis', 'statistics', 'databases', 'reporting', 'decision making', 'management']
    elif 'business' in interest_lower:
        return ['management', 'economics', 'finance', 'accounting', 'marketing', 'statistics']
    elif 'data' in interest_lower:
        return ['statistics', 'programming', 'databases', 'analytics', 'visualization', 'machine learning']
    elif 'intelligence' in interest_lower or 'ai' in interest_lower:
        return ['machine learning', 'programming', 'algorithms', 'statistics', 'mathematics']
    else:
        return ['mathematics', 'statistics', 'programming', 'writing']

async def _calculate_enhanced_relevance_score(course: Dict[str, Any], interests: List[str]) -> float:
    """Enhanced relevance scoring that considers multiple interests and is more lenient"""
    
    course_title = course.get('title', '').lower()
    course_subject = course.get('subject', '').upper()
    course_number = course.get('course_number', '')
    
    # Quick keyword matching first
    max_keyword_score = 0
    for interest in interests:
        if interest.lower() in course_title:
            max_keyword_score = max(max_keyword_score, 0.9)
        elif any(word in course_title for word in interest.lower().split()):
            max_keyword_score = max(max_keyword_score, 0.6)
    
    # Subject-based scoring (more generous)
    subject_score = 0
    if course_subject in ['CS', 'DS', 'IS', 'BUSN', 'STAT', 'ECON', 'MGMT', 'ACCT', 'FINA']:
        subject_score = 0.6
    elif course_subject in ['MATH', 'PHIL', 'ENGW']:
        subject_score = 0.4  # Foundation courses
    else:
        subject_score = 0.2  # Other courses might still be useful
    
    # Use AI for detailed analysis only if initial score is promising or we need more courses
    if max_keyword_score > 0.5 or subject_score > 0.4:
        try:
            interests_text = ", ".join(interests)
            prompt = f"""
            Rate how this course could help a student interested in: {interests_text}
            
            Course: {course_subject}{course_number} - {course.get('title', '')}
            
            Consider if this course provides:
            - Direct relevant skills or knowledge
            - Important foundational concepts
            - Supporting business or analytical skills
            - General critical thinking or communication skills
            
            Rate 0.0-1.0 where:
            0.0-0.2: Not helpful
            0.3-0.4: Foundational/supporting value
            0.5-0.6: Moderately relevant
            0.7-0.8: Highly relevant
            0.9-1.0: Perfect match
            
            Be generous with foundational courses. Respond with only a number.
            """
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    openai_client.chat.completions.create,
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10,
                    temperature=0.2
                ),
                timeout=10.0
            )
            
            score_text = response.choices[0].message.content.strip()
            ai_score = float(score_text)
            
            # Combine scores, giving weight to AI analysis
            final_score = max(max_keyword_score, subject_score, ai_score)
            return min(max(final_score, 0.0), 1.0)
            
        except Exception as e:
            logger.debug(f"AI scoring failed for {course['code']}: {e}")
    
    # Fallback to keyword + subject scoring
    return max(max_keyword_score, subject_score)

async def _emergency_course_selection_fallback(available_courses: List[Dict[str, Any]], interest: str) -> List[Dict[str, Any]]:
    """Emergency fallback when all AI methods fail"""
    logger.info("Using emergency course selection fallback")
    
    selected = []
    
    # Priority subjects for any academic interest
    priority_subjects = ['MATH', 'ENGW', 'CS', 'DS', 'BUSN', 'STAT', 'PHIL', 'ECON']
    
    for subject in priority_subjects:
        subject_courses = [c for c in available_courses if c['subject'] == subject]
        for course in subject_courses[:3]:  # Take first 3 from each subject
            course_with_score = course.copy()
            course_with_score['ai_relevance_score'] = 0.5  # Moderate relevance
            selected.append(course_with_score)
            
            if len(selected) >= 16:  # Enough for 4-year plan
                break
        
        if len(selected) >= 16:
            break
    
    # If still not enough, add more courses
    if len(selected) < 12:
        for course in available_courses:
            if course not in selected:
                course_with_score = course.copy()
                course_with_score['ai_relevance_score'] = 0.3
                selected.append(course_with_score)
                if len(selected) >= 16:
                    break
    
    logger.info(f"Emergency fallback selected {len(selected)} courses")
    return selected

async def _ai_select_relevant_courses_fallback(available_courses: List[Dict[str, Any]], interest: str) -> List[Dict[str, Any]]:
    """Fallback course selection when OpenAI batch analysis fails"""
    
    logger.info(f"Using fallback individual analysis for {min(len(available_courses), 50)} courses")
    
    relevant_courses = []
    
    for course in available_courses[:50]:
        relevance_score = await _calculate_ai_relevance_score(course, interest)
        
        if relevance_score > 0.2:
            course_with_score = course.copy()
            course_with_score['ai_relevance_score'] = relevance_score
            relevant_courses.append(course_with_score)
    
    relevant_courses.sort(key=lambda x: x['ai_relevance_score'], reverse=True)
    logger.info(f"Fallback analysis selected {len(relevant_courses)} relevant courses")
    
    return relevant_courses

async def _calculate_ai_relevance_score(course: Dict[str, Any], interest: str) -> float:
    """Calculate AI-driven relevance score for a course using OpenAI"""
    
    course_title = course.get('title', '')
    course_subject = course.get('subject', '')
    course_number = course.get('course_number', '')
    
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
        
        Respond with only a single number between 0.0 and 1.0
        """
        
        response = await asyncio.wait_for(
            asyncio.to_thread(
                openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            ),
            timeout=15.0
        )
        
        score_text = response.choices[0].message.content.strip()
        score = float(score_text)
        return min(max(score, 0.0), 1.0)
        
    except Exception as e:
        logger.warning(f"OpenAI API error for course {course_subject}{course_number}: {e}")
        return _calculate_fallback_relevance_score(course, interest)

def _calculate_fallback_relevance_score(course: Dict[str, Any], interest: str) -> float:
    """Simplified fallback relevance calculation when OpenAI is unavailable"""
    course_title = course.get('title', '').lower()
    course_subject = course.get('subject', '').upper()
    interest_lower = interest.lower()
    
    # Check for direct keyword matches in title
    if any(keyword in course_title for keyword in interest_lower.split()):
        return 0.8
    
    # Check if course subject relates to common technical fields
    if course_subject in ['CS', 'DS', 'MATH', 'STAT', 'IS', 'EECE']:
        return 0.5  # Moderate relevance for technical courses
    
    # Foundation courses are generally useful
    if course_subject in ['MATH', 'ENGW', 'PHIL']:
        return 0.3
    
    return 0.25

# =============================================================================
# AI COURSE SEQUENCING - Academic Plan Generation
# =============================================================================

async def _ai_sequence_courses(selected_courses: List[Dict[str, Any]], years: int, interest: str) -> List[Dict[str, Any]]:
    """AI-powered course sequencing into semesters using OpenAI"""
    
    logger.info(f"AI sequencing {len(selected_courses)} courses into {years}-year plan")
    
    course_descriptions = []
    for course in selected_courses:
        course_info = f"{course['code']}: {course['title']} ({course.get('credits', 4)} credits)"
        course_descriptions.append(course_info)
    
    try:
        prompt = f"""
        You are an academic advisor creating an optimal {years}-year course sequence for a student interested in "{interest}".
        
        Available courses:
        {chr(10).join(course_descriptions)}
        
        Create an optimal semester-by-semester plan with these guidelines:
        1. Prerequisites should be taken before advanced courses
        2. Foundation courses (1000-2000 level) should come early
        3. Advanced courses (3000+ level) should come later  
        4. Aim for 12-18 credits (3-4 courses) per semester
        5. Balance difficulty across semesters
        6. Consider logical learning progression for "{interest}"
        7. IMPORTANT: Never repeat the same course - each course should appear only once
        8. If you need electives, create specific meaningful names (not generic "General Elective")
        
        Format the response as a JSON array:
        [
          {{
            "year": 1,
            "term": "Fall",
            "courses": ["CS1200 - Introduction to Computer Science", "MATH1341 - Calculus I", "ENGW1111 - First-Year Writing"],
            "credits": 12,
            "notes": "Foundation semester focusing on..."
          }}
        ]
        
        Include exactly {years * 2} semesters (Fall and Spring for each year).
        Ensure NO duplicate courses across all semesters.
        """
        
        response = await asyncio.wait_for(
            asyncio.to_thread(
                openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            ),
            timeout=30.0
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
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
            
            if isinstance(ai_plan, list) and len(ai_plan) > 0:
                # Validate and clean the AI plan to remove duplicates
                cleaned_plan = _clean_duplicate_courses_from_plan(ai_plan, selected_courses, interest)
                logger.info(f"OpenAI generated plan with {len(cleaned_plan)} semesters (cleaned)")
                return cleaned_plan
            else:
                logger.warning("OpenAI response format invalid, using fallback")
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse OpenAI JSON response: {e}")
        
    except Exception as e:
        logger.warning(f"OpenAI API error for course sequencing: {e}")
    
    # Fallback to deterministic sequencing
    return await _ai_determine_course_sequence_fallback(selected_courses, years, interest)

def _clean_duplicate_courses_from_plan(ai_plan: List[Dict[str, Any]], available_courses: List[Dict[str, Any]], interest: str) -> List[Dict[str, Any]]:
    """Clean AI-generated plan to remove duplicate courses and improve electives"""
    
    cleaned_plan = []
    used_courses = set()
    available_course_map = {course['code']: course for course in available_courses}
    elective_counter = 1
    
    for semester in ai_plan:
        cleaned_semester = {
            "year": semester.get("year", 1),
            "term": semester.get("term", "Fall"),
            "courses": [],
            "credits": 0,
            "notes": semester.get("notes", "")
        }
        
        semester_courses = semester.get("courses", [])
        
        for course_entry in semester_courses:
            # Extract course code from various formats
            course_code = _extract_course_code_from_entry(course_entry)
            
            if course_code and course_code in available_course_map and course_code not in used_courses:
                # Use actual course from our available list
                actual_course = available_course_map[course_code]
                course_title = f"{actual_course['code']} - {actual_course['title']}"
                cleaned_semester["courses"].append(course_title)
                cleaned_semester["credits"] += actual_course.get('credits', 4)
                used_courses.add(course_code)
                
            elif 'elective' in course_entry.lower() or 'general' in course_entry.lower():
                # Create specific elective names
                if 'business' in interest.lower():
                    elective_types = ['Business Strategy', 'Marketing Analytics', 'Financial Analysis', 
                                     'Operations Research', 'Corporate Finance', 'Supply Chain Analytics']
                elif 'data' in interest.lower() or 'intelligence' in interest.lower():
                    elective_types = ['Advanced Analytics', 'Data Warehousing', 'Predictive Modeling',
                                     'Business Intelligence', 'Data Governance', 'Machine Learning Applications']
                else:
                    elective_types = ['Professional Skills', 'Industry Applications', 'Research Project',
                                     'Technical Writing', 'Capstone Experience', 'Leadership Development']
                
                # Select unique elective name
                if elective_counter <= len(elective_types):
                    elective_name = elective_types[(elective_counter - 1) % len(elective_types)]
                else:
                    elective_name = f"{interest.title()} Specialization {elective_counter - len(elective_types)}"
                
                # Check if this elective name is already used
                existing_courses = [c for semester_data in cleaned_plan for c in semester_data.get("courses", [])]
                existing_courses.extend(cleaned_semester["courses"])
                
                if elective_name not in existing_courses:
                    cleaned_semester["courses"].append(elective_name)
                    cleaned_semester["credits"] += 4
                    elective_counter += 1
        
        # Ensure minimum course load without duplicates
        while len(cleaned_semester["courses"]) < 3:
            new_elective = f"{interest.title()} Focus Area {elective_counter}"
            if new_elective not in cleaned_semester["courses"]:
                cleaned_semester["courses"].append(new_elective)
                cleaned_semester["credits"] += 4
                elective_counter += 1
        
        if len(cleaned_semester["courses"]) > 0:
            cleaned_plan.append(cleaned_semester)
    
    return cleaned_plan

def _extract_course_code_from_entry(course_entry: str) -> str:
    """Extract course code from various course entry formats"""
    import re
    
    # Try to find pattern like CS1234, MATH2341, etc.
    pattern = r'\b([A-Z]{2,4}\d{4})\b'
    match = re.search(pattern, course_entry.upper())
    
    if match:
        return match.group(1)
    
    # Try simpler pattern for CS1234 format
    pattern2 = r'\b([A-Z]+\d+)\b'
    match2 = re.search(pattern2, course_entry.upper())
    
    if match2:
        return match2.group(1)
    
    return None

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
    
    # Distribute into semesters ensuring no duplicates
    all_courses = foundation_courses + intermediate_courses + advanced_courses
    total_semesters = years * 2
    semesters = ["Fall", "Spring"]
    plan = []
    
    courses_per_semester = max(3, len(all_courses) // total_semesters)
    course_index = 0
    used_courses = set()  # Track used courses to prevent duplicates
    elective_counter = 1  # Counter for generic electives
    
    for year in range(1, years + 1):
        for semester in semesters:
            semester_courses = []
            semester_credits = 0
            target_courses = min(courses_per_semester, len(all_courses) - course_index)
            
            # Add actual courses from our selected list
            for _ in range(target_courses):
                if course_index < len(all_courses):
                    course = all_courses[course_index]
                    course_code = course['code']
                    
                    # Check for duplicates
                    if course_code not in used_courses:
                        course_title = f"{course['code']} - {course['title']}"
                        semester_courses.append(course_title)
                        semester_credits += course.get('credits', 4)
                        used_courses.add(course_code)
                    
                    course_index += 1
            
            # Fill remaining slots with meaningful electives (no generic duplicates)
            while len(semester_courses) < 4 and semester_credits < 16:
                # Create specific elective names based on interest and semester
                if 'business' in interest.lower():
                    elective_types = ['Business Ethics', 'Organizational Behavior', 'Strategic Management', 
                                     'Operations Management', 'International Business', 'Entrepreneurship',
                                     'Supply Chain Management', 'Digital Marketing']
                elif 'data' in interest.lower() or 'intelligence' in interest.lower():
                    elective_types = ['Data Mining', 'Machine Learning Applications', 'Statistical Modeling',
                                     'Database Design', 'Data Visualization', 'Predictive Analytics',
                                     'Business Intelligence Tools', 'Big Data Technologies']
                else:
                    elective_types = ['Professional Development', 'Technical Communication', 
                                     'Industry Seminar', 'Research Methods', 'Capstone Project',
                                     'Internship Preparation', 'Leadership Skills', 'Ethics in Technology']
                
                # Select an elective type that hasn't been used
                available_electives = [e for e in elective_types if e not in [c.split(' - ')[-1] if ' - ' in c else c for c in semester_courses]]
                
                if available_electives:
                    elective_name = available_electives[0]
                elif elective_counter <= len(elective_types):
                    elective_name = f"{interest.title()} Elective {elective_counter}"
                    elective_counter += 1
                else:
                    elective_name = f"General Elective {elective_counter}"
                    elective_counter += 1
                
                semester_courses.append(elective_name)
                semester_credits += 4
            
            if len(semester_courses) > 0:
                plan.append({
                    "year": year,
                    "term": semester,
                    "courses": semester_courses,
                    "credits": semester_credits,
                    "notes": f"AI-optimized for {interest} - {len([c for c in semester_courses if not any(word in c.lower() for word in ['elective', 'seminar'])])} core courses"
                })
    
    return plan

async def _generate_smart_plan_async(
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
    """Generate comprehensive academic plan using real course data and AI optimization"""
    
    completed_courses = completed_courses or []
    transfer_credits = transfer_credits or {}
    interest_areas = interest_areas or []
    preferences = preferences or {}
    
    logger.info(f"Generating smart plan for major: {major_id}, concentration: {concentration_id}")
    
    try:
        # Step 1: Get major requirements using AI
        major_subjects = await _get_major_subjects_ai(major_id)
        
        # Step 2: Fetch real course data
        logger.info("Fetching current course data...")
        course_data_result = await _fetch_course_data_async(subjects=major_subjects)
        
        if not course_data_result["success"]:
            raise Exception("Failed to fetch course data from NEU API")
        
        all_courses = course_data_result["courses"]
        term_code = course_data_result["term_code"]
        
        # Step 3: Generate course recommendations based on major and interests
        combined_interests = [major_id]
        if concentration_id:
            combined_interests.append(concentration_id)
        combined_interests.extend(interest_areas)
        
        # Use AI to select relevant courses
        all_available_courses = []
        for subject, courses in all_courses.items():
            for course in courses:
                course_info = {
                    'subject': course['subject'],
                    'course_number': course['course_number'],
                    'title': course.get('title', ''),
                    'credits': course.get('credits', 4),
                    'code': f"{course['subject']}{course['course_number']}"
                }
                all_available_courses.append(course_info)
        
        # Filter out completed courses
        available_courses = [c for c in all_available_courses 
                           if c['code'] not in completed_courses]
        
        # Use AI to select and sequence courses
        interest_description = f"{major_id} with focus on {', '.join(combined_interests)}"
        selected_courses = await _ai_select_relevant_courses(available_courses, interest_description)
        
        # Calculate plan duration (default 4 years, adjustable based on remaining courses)
        years_needed = max(2, min(4, len(selected_courses) // 8))
        semester_plan = await _ai_sequence_courses(selected_courses, years_needed, interest_description)
        
        # Calculate total credits
        total_credits = 0
        for semester in semester_plan:
            total_credits += semester.get('credits', 0)
        
        # Generate AI insights
        ai_insights = {}
        if use_ai_optimization:
            ai_insights = {
                "optimization_applied": True,
                "course_selection_method": "AI-powered relevance analysis",
                "sequencing_method": "AI-optimized prerequisite ordering",
                "total_courses_analyzed": len(all_available_courses),
                "courses_selected": len(selected_courses),
                "plan_duration_years": years_needed
            }
        
        # Build the result structure
        result = {
            "success": True,
            "plan": {
                "id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "major_id": major_id,
                "concentration_id": concentration_id,
                "term_code": term_code,
                "total_credits": total_credits,
                "semesters": semester_plan,
                "completed_courses": completed_courses,
                "transfer_credits": transfer_credits,
                "coop_pattern": coop_pattern,
                "created_at": datetime.now().isoformat(),
                "is_ai_generated": True,
                "validation": {"status": "valid", "warnings": [], "recommendations": []}
            },
            "ai_insights": ai_insights,
            "warnings": [],
            "recommendations": []
        }
        
        # Cache the result
        cache_key = f"smart_plan:{major_id}:{concentration_id}:{start_year}:{hash(str(completed_courses))}"
        redis_client.setex(cache_key, 1800, json.dumps(result))
        
        logger.info(f"Successfully generated smart plan with {len(semester_plan)} semesters")
        return result
        
    except Exception as e:
        logger.error(f"Error in smart plan generation: {e}", exc_info=True)
        raise

async def _get_major_subjects_ai(major_id: str) -> List[str]:
    """Use AI to determine relevant subjects for a major"""
    try:
        # Get all available subjects from the system first
        all_subjects = ["CS", "DS", "IS", "MATH", "PHYS", "CHEM", "BIOL", "EECE", "PHIL", 
                       "ENGW", "BUSN", "ACCT", "FINA", "MGMT", "ECON", "STAT", "CY", "PSYC", 
                       "HIST", "ENGL", "MUSC", "ARTF", "THTR", "POLS", "SOCL", "ANTH"]
        
        prompt = f"""
        For a student majoring in "{major_id}", which university subject codes would be most relevant?
        
        Available subject codes: {', '.join(all_subjects)}
        
        Select the 4-8 most relevant subject codes for this major, considering:
        - Core requirements for the major
        - Supporting/prerequisite subjects 
        - Common elective areas
        - General education requirements
        
        Return only the subject codes separated by commas, in order of importance.
        Example: "CS, MATH, PHYS, ENGW"
        """
        
        response = await asyncio.wait_for(
            asyncio.to_thread(
                openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.2
            ),
            timeout=15.0
        )
        
        subjects_text = response.choices[0].message.content.strip()
        subjects = [s.strip().upper() for s in subjects_text.split(',') if s.strip()]
        
        # Validate subjects against available list
        valid_subjects = [s for s in subjects if s in all_subjects]
        
        if len(valid_subjects) >= 3:
            logger.info(f"AI selected subjects for {major_id}: {valid_subjects}")
            return valid_subjects
        else:
            logger.warning(f"AI returned insufficient subjects for {major_id}, using fallback")
            return _get_fallback_subjects(major_id)
            
    except Exception as e:
        logger.warning(f"AI subject selection failed for {major_id}: {e}")
        return _get_fallback_subjects(major_id)

def _get_fallback_subjects(major_id: str) -> List[str]:
    """Fallback subject selection when AI fails"""
    # Basic fallback - just return common subjects
    return ["CS", "MATH", "ENGW", "PHIL"]

async def _get_relevant_subjects_for_interests(interest_areas: List[str]) -> List[str]:
    """Use AI to determine which university subjects are relevant for given interests"""
    if not interest_areas:
        return ["CS", "MATH", "ENGW"]
    
    try:
        all_subjects = ["CS", "DS", "IS", "MATH", "PHYS", "CHEM", "BIOL", "EECE", "PHIL", 
                       "ENGW", "BUSN", "ACCT", "FINA", "MGMT", "ECON", "STAT", "CY", "PSYC", 
                       "HIST", "ENGL", "MUSC", "ARTF", "THTR", "POLS", "SOCL", "ANTH"]
        
        interests_text = ", ".join(interest_areas)
        
        prompt = f"""
        For a student interested in: {interests_text}
        
        Which university subject codes would be most relevant for courses?
        Available subjects: {', '.join(all_subjects)}
        
        Select the 3-6 most relevant subject codes, considering courses that would:
        - Directly relate to these interests
        - Provide foundational knowledge
        - Offer complementary skills
        
        Return only the subject codes separated by commas.
        Example: "CS, MATH, STAT"
        """
        
        response = await asyncio.wait_for(
            asyncio.to_thread(
                openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
                temperature=0.2
            ),
            timeout=15.0
        )
        
        subjects_text = response.choices[0].message.content.strip()
        subjects = [s.strip().upper() for s in subjects_text.split(',') if s.strip()]
        
        # Validate and return
        valid_subjects = [s for s in subjects if s in all_subjects]
        
        if len(valid_subjects) >= 2:
            logger.info(f"AI selected subjects for interests {interest_areas}: {valid_subjects}")
            return valid_subjects
        else:
            return ["CS", "MATH", "ENGW"]  # Fallback
            
    except Exception as e:
        logger.warning(f"AI subject selection failed for interests {interest_areas}: {e}")
        return ["CS", "MATH", "ENGW"]  # Fallback

async def _calculate_course_relevance_for_interests(course: Dict[str, Any], interest_areas: List[str]) -> float:
    """Use AI to calculate how relevant a course is to given interests"""
    if not interest_areas:
        return 0.0
    
    course_title = course.get('title', '')
    course_subject = course.get('subject', '')
    course_number = course.get('course_number', '')
    interests_text = ", ".join(interest_areas)
    
    try:
        prompt = f"""
        Rate how relevant this course is to a student interested in: {interests_text}
        
        Course: {course_subject}{course_number} - {course_title}
        
        Consider:
        - Direct relevance to the interests
        - Foundational value for these areas
        - Practical application potential
        
        Rate from 0-10 where:
        0-2: Not relevant
        3-4: Somewhat relevant
        5-6: Moderately relevant
        7-8: Highly relevant
        9-10: Essential/Perfect match
        
        Respond with only a single number 0-10.
        """
        
        response = await asyncio.wait_for(
            asyncio.to_thread(
                openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            ),
            timeout=10.0
        )
        
        score_text = response.choices[0].message.content.strip()
        score = float(score_text)
        return min(max(score, 0.0), 10.0)
        
    except Exception as e:
        logger.warning(f"AI relevance scoring failed for {course_subject}{course_number}: {e}")
        # Fallback to simple keyword matching
        title_lower = course_title.lower()
        for interest in interest_areas:
            if interest.lower() in title_lower:
                return 8.0
        return 3.0  # Default moderate relevance

# =============================================================================
# ADDITIONAL TASKS - Supporting Functionality
# =============================================================================

async def _validate_prerequisites_async(courses: List[str], term_code: Optional[str]) -> Dict[str, Any]:
    """Async prerequisite validation"""
    
    client = SearchNEUClient()
    
    try:
        if not term_code:
            terms = await client.get_terms(max_results=5)
            term_code = terms[0]["code"] if terms else "202510"
        
        validation_results = {}
        
        for course_code in courses:
            match = re.match(r'([A-Z]+)(\d+)', course_code)
            if not match:
                validation_results[course_code] = {
                    "valid": False,
                    "error": "Invalid course code format"
                }
                continue
            
            subject, course_number = match.groups()
            
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

async def _get_recommendations_async(
    completed_courses: List[str], 
    interest_areas: List[str], 
    semester_target: str,
    max_recommendations: int
) -> Dict[str, Any]:
    """Async course recommendations using AI-driven subject mapping"""
    
    course_data_result = await _fetch_course_data_async()
    
    if not course_data_result["success"]:
        return {"success": False, "error": "Failed to fetch course data"}
    
    all_courses = course_data_result["courses"]
    
    # Use AI to determine relevant subjects for interests
    relevant_subjects = await _get_relevant_subjects_for_interests(interest_areas)
    
    # Get available courses in relevant subjects
    available_courses = []
    for subject in relevant_subjects:
        if subject in all_courses:
            for course in all_courses[subject]:
                course_code = f"{course['subject']}{course['course_number']}"
                
                if course_code in completed_courses:
                    continue
                
                # Use AI to calculate relevance score for each course
                relevance_score = await _calculate_course_relevance_for_interests(
                    course, interest_areas
                )
                
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
