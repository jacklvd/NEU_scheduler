# app/graphql/schema.py - Improved version
import strawberry
from typing import List, Optional
from app.graphql.resolvers.course_resolver import CourseQuery
from app.graphql.resolvers.auth_resolver import AuthMutation, AuthQuery
from app.graphql.resolvers.health_resolver import HealthQuery
from app.graphql.types.schedule import SuggestedPlan, AcademicPlan, PlannedCourse
from app.worker.tasks import generate_ai_suggestion


@strawberry.type
class Query(CourseQuery, AuthQuery, HealthQuery):
    @strawberry.field
    async def suggest_plan(self, interest: str, years: int = 2) -> List[SuggestedPlan]:
        """Generate AI-powered course plan suggestions"""
        try:
            result = generate_ai_suggestion.delay(interest, years)
            result.wait(timeout=30)
            return result.result or []
        except Exception as e:
            print(f"Error generating AI suggestion: {e}")
            # Return empty list instead of None to match return type
            return []

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
            # Quick test to see if NU Banner is accessible
            terms = await client.get_terms(max_results=1)
            if terms:
                return f"✅ API operational - NU Banner accessible ({len(terms)} terms)"
            else:
                return "⚠️ API operational - NU Banner returns no data"
        except Exception as e:
            return f"❌ API issues - NU Banner error: {str(e)}"


@strawberry.type
class Mutation(AuthMutation):
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
            }
            print(f"Saving schedule: {schedule_data}")
            # TODO: Implement actual saving to R2 or database
            return True
        except Exception as e:
            print(f"Error saving schedule: {e}")
            return False

    @strawberry.mutation
    async def reset_course_cache(self) -> bool:
        """Reset the course search cache (useful for debugging)"""
        try:
            from app.neu_api.searchneu_client import SearchNEUClient

            client = SearchNEUClient()
            if client.redis_client:
                # Delete all course-related cache keys
                keys = client.redis_client.keys("courses:*")
                keys.extend(client.redis_client.keys("terms:*"))
                keys.extend(client.redis_client.keys("subjects:*"))

                if keys:
                    client.redis_client.delete(*keys)
                    return True
            return False
        except Exception as e:
            print(f"Error resetting cache: {e}")
            return False


# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# Import for FastAPI
from strawberry.fastapi import GraphQLRouter

graphql_app = GraphQLRouter(schema)

# Test queries you can use in GraphQL Playground
TEST_QUERIES = """
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

# Test 4: Get Subjects (use a term ID from previous query)
query {
  getSubjects(term: "202410") {
    code
    name
  }
}

# Test 5: Search Courses
query {
  searchCourses(term: "202410", subject: "CS", pageSize: 5) {
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

# Test 6: AI Plan Suggestion
query {
  suggestPlan(interest: "machine learning", years: 2) {
    year
    term
    courses
  }
}

# Test 7: Reset Cache (mutation)
mutation {
  resetCourseCache
}
"""
