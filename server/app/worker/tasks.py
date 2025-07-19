from celery import Celery
from app.worker.celery_app import celery_app
import redis
import json
import os
import openai
from typing import List, Dict, Any
from app.config import settings

# Initialize Redis client
redis_client = redis.Redis.from_url(settings.redis_url)

# Set OpenAI API key
openai.api_key = settings.openai_api_key
# Initialize Celery app
celery_app = Celery("worker", broker=settings.celery_broker_url)


@celery_app.task(bind=True, name="cache_courses")
def cache_courses(self, key: str, data: List[Dict[str, Any]]) -> bool:
    """Cache course data in Redis"""
    try:
        # Convert data to JSON string and cache for 1 hour
        redis_client.setex(key, 3600, json.dumps(data))
        print(f"✅ Cached data with key: {key}")
        return True
    except Exception as e:
        print(f"❌ Error caching data: {e}")
        # Retry the task up to 3 times
        self.retry(countdown=60, max_retries=3)
        return False


@celery_app.task(bind=True, name="generate_ai_suggestion")
def generate_ai_suggestion(self, interest: str, years: int = 2) -> List[Dict[str, Any]]:
    """Generate AI-powered course suggestions"""
    try:
        # Create a more detailed prompt
        prompt = f"""
        You are an academic advisor for Northeastern University. Create a {years}-year course plan 
        for a student interested in {interest}.
        
        Requirements:
        - Each year has Fall and Spring semesters (and optionally Summer)
        - Suggest 4-5 courses per semester
        - Include relevant CS, MATH, and elective courses
        - Consider prerequisite chains
        - Include both technical and general education requirements
        
        Format your response as a structured plan. For each semester, list specific course codes like:
        - CS 2500 (Fundamentals of Computer Science 1)
        - MATH 1365 (Introduction to Mathematical Reasoning)
        
        Years: {years}
        Interest Area: {interest}
        
        Please provide a realistic course sequence.
        """

        # Using the newer OpenAI API format
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7,
        )

        content = response.choices[0].message.content

        # Parse the response into structured data
        plan = parse_ai_response(content, years)

        print(f"✅ Generated AI suggestion for {interest}")
        return plan

    except Exception as e:
        print(f"❌ Error generating AI suggestion: {e}")
        # Retry the task up to 2 times
        self.retry(countdown=120, max_retries=2)
        return []


def parse_ai_response(content: str, years: int) -> List[Dict[str, Any]]:
    """Parse AI response into structured course plan"""
    plan = []

    # Simple parsing logic - you can make this more sophisticated
    lines = content.strip().split("\n")
    current_year = 1
    current_term = "Fall"
    current_courses = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Look for year/semester indicators
        if any(
            keyword in line.lower() for keyword in ["year", "fall", "spring", "summer"]
        ):
            # Save previous semester if we have courses
            if current_courses:
                plan.append(
                    {
                        "year": current_year,
                        "term": current_term,
                        "courses": current_courses,
                    }
                )
                current_courses = []

            # Parse new semester info
            if "year" in line.lower():
                try:
                    current_year = int("".join(filter(str.isdigit, line)))
                except:
                    pass

            if "fall" in line.lower():
                current_term = "Fall"
            elif "spring" in line.lower():
                current_term = "Spring"
            elif "summer" in line.lower():
                current_term = "Summer"

        # Look for course codes (like CS 2500, MATH 1365)
        elif any(char.isdigit() for char in line) and any(
            char.isalpha() for char in line
        ):
            # Extract course from line
            course = line.split("(")[0].strip()  # Take part before parentheses
            if course and len(course) < 20:  # Reasonable course code length
                current_courses.append(course)

    # Add final semester
    if current_courses:
        plan.append(
            {"year": current_year, "term": current_term, "courses": current_courses}
        )

    # If parsing failed, create a default structure
    if not plan:
        semesters = ["Fall", "Spring"] * years
        for i, semester in enumerate(semesters):
            year = (i // 2) + 1
            plan.append(
                {
                    "year": year,
                    "term": semester,
                    "courses": [
                        "CS 2500 - Fundamentals of Computer Science 1",
                        "MATH 1365 - Introduction to Mathematical Reasoning",
                        "ENGW 1111 - First-Year Writing",
                        "PHIL 1145 - Technology and Human Values",
                    ],
                }
            )

    return plan


@celery_app.task(name="cleanup_cache")
def cleanup_cache() -> bool:
    """Clean up expired cache entries"""
    try:
        # Get all keys that match our pattern
        cache_keys = redis_client.keys("courses:*")
        cache_keys.extend(redis_client.keys("terms:*"))
        cache_keys.extend(redis_client.keys("subjects:*"))

        # Clean up keys that are close to expiring
        cleaned = 0
        for key in cache_keys:
            ttl = redis_client.ttl(key)
            if ttl < 300:  # Less than 5 minutes remaining
                redis_client.delete(key)
                cleaned += 1

        print(f"✅ Cleaned up {cleaned} cache entries")
        return True

    except Exception as e:
        print(f"❌ Error cleaning cache: {e}")
        return False
