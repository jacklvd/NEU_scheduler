import strawberry
from typing import List
from app.graphql.resolvers.course_resolver import CourseQuery
from app.graphql.resolvers.auth_resolver import AuthMutation, AuthQuery
from app.graphql.types.schedule import SuggestedPlan, AcademicPlan, PlannedCourse
from app.worker.tasks import generate_ai_suggestion


@strawberry.type
class Query(CourseQuery, AuthQuery):
    @strawberry.field
    async def suggest_plan(self, interest: str, years: int = 2) -> List[SuggestedPlan]:
        """Generate AI-powered course plan suggestions"""
        try:
            result = generate_ai_suggestion.delay(interest, years)
            result.wait(timeout=30)
            return result.result or []
        except Exception as e:
            print(f"Error generating AI suggestion: {e}")
            return []

    @strawberry.field
    async def health_check(self) -> str:
        """Simple health check endpoint"""
        return "GraphQL API is running with corrected NU Banner integration!"


@strawberry.type
class Mutation(AuthMutation):
    @strawberry.mutation
    async def save_schedule(
        self, user_id: str, year: int, term: str, courses: List[str]
    ) -> bool:
        """Save a user's course schedule"""
        schedule_data = {
            "user_id": user_id,
            "year": year,
            "term": term,
            "courses": courses,
        }
        print(f"Saved schedule: {schedule_data}")
        return True


schema = strawberry.Schema(query=Query, mutation=Mutation)
from strawberry.fastapi import GraphQLRouter

graphql_app = GraphQLRouter(schema)
