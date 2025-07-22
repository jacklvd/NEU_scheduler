from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.graphql.schema import graphql_app

# Import settings without causing validation errors
try:
    from app.config import settings

    cors_origins = settings.cors_origins
    debug_mode = settings.debug
except Exception as e:
    print(f"Warning: Config import failed: {e}")
    cors_origins = ["https://localhost:3000", "http://127.0.0.1:3000"]
    debug_mode = True

app = FastAPI(
    title="NEUCourseScheduler API",
    description="AI-powered academic planning for Northeastern students",
    version="1.0.0",
    debug=debug_mode,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "NEUCourseScheduler API"}


@app.get("/api/test")
async def test_endpoint():
    return {"message": "Server is running!", "status": "success"}


# Include GraphQL router
app.include_router(graphql_app, prefix="/api/graphql")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
