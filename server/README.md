# NEUscheduler Backend

FastAPI-based backend server for the NEUscheduler application, providing AI-powered course scheduling and management for Northeastern University students.

## Architecture Overview

The backend follows a modular architecture with the following components:

```bash
server/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Configuration settings
│   ├── graphql/
│   │   ├── __init__.py
│   │   ├── schema.py            # GraphQL schema definition
│   │   ├── resolvers/
│   │   │   ├── __init__.py
│   │   │   ├── auth_resolver.py # Authentication resolvers
│   │   │   ├── course_resolver.py # Course query resolvers
│   │   │   └── health_resolver.py # Health check resolvers
│   │   └── types/
│   │       ├── __init__.py
│   │       ├── course.py        # Course GraphQL types
│   │       ├── schedule.py      # Schedule GraphQL types
│   │       └── user.py          # User GraphQL types
│   ├── models/
│   │   └── user.py              # User data models
│   ├── neu_api/
│   │   ├── __init__.py
│   │   └── searchneu_client.py  # SearchNEU API client
│   ├── services/
│   │   ├── auth.py              # Authentication services
│   │   ├── email.py             # Email service implementation
│   │   ├── email_factory.py     # Email service factory
│   │   └── otp_cache.py         # OTP caching service
│   ├── storage/
│   │   └── r2_client.py         # Cloudflare R2 storage client
│   └── worker/
│       ├── __init__.py
│       ├── celery_app.py        # Celery configuration
│       └── tasks.py             # Background tasks
├── poetry.lock                  # Poetry lock file
├── pyproject.toml              # Python dependencies & config
├── README.md                   # This file
├── .env                        # Environment variables
└── .env.example                # Environment variables template
```

## Installation & Setup

### Prerequisites

- Python 3.13+
- Poetry (Python dependency management)
- Redis (for caching and background tasks)

### Quick Start

1. **Navigate to the server directory:**

   ```bash
   cd server
   ```

2. **Install dependencies with Poetry:**

   ```bash
   poetry install
   ```

3. **Set up environment variables:**

   Copy the example environment file and configure your settings:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` with your actual configuration values.

4. **Start Redis (if running locally):**

   ```bash
   redis-server
   ```

   Or use Docker:

   ```bash
   docker run -d -p 6379:6379 redis:alpine
   ```

5. **Run the development server:**

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

   The server will start on `http://localhost:8000`

## Environment Variables

Create a `.env` file in the server directory with the following variables:

```env
# API Configuration
API_BASE_URL=https://nubanner.neu.edu/StudentRegistrationSsb/ssb/
NU_BANNER_BASE_URL=https://nubanner.neu.edu/StudentRegistrationSsb/ssb/

# Redis Configuration
REDIS_URL=redis://localhost:6379

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Email Configuration
EMAIL_PROVIDER=your_preferred_email_provider
EMAIL_API_KEY=your_email_api_key
EMAIL_FROM_ADDRESS=noreply@yourdomain.com

# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your_r2_account_id
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_NAME=your_bucket_name

# Application Settings
DEBUG=true
CORS_ORIGINS=http://localhost:3000,https://localhost:3000

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

### REST API

- **Base URL:** `http://localhost:8000/api`
- **Health Check:** `GET /api/health`
- **Test Endpoint:** `GET /api/test`

### GraphQL

- **GraphQL Endpoint:** `http://localhost:8000/api/graphql`
- **GraphQL Playground:** Available in development mode

### Documentation

- **OpenAPI Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Development

### Running the Server

**Development mode with auto-reload:**

```bash
poetry run uvicorn app.main:app --reload
```

**Production mode:**

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Background Tasks

Start Celery worker for background task processing:

```bash
poetry run celery -A app.worker.celery_app worker --loglevel=info
```

### Testing

Run tests (when available):

```bash
poetry run pytest
```

### Code Formatting

Format code with black:

```bash
poetry run black app/
```

## Features

- **FastAPI Framework:** Modern, fast web framework for building APIs
- **GraphQL API:** Flexible query language for efficient data fetching
- **Authentication System:** JWT-based authentication with OTP verification
- **Email Services:** Multi-provider email service with factory pattern
- **User Management:** Complete user registration and authentication flow
- **Course Search:** Integration with Northeastern's course search API
- **Health Monitoring:** Comprehensive health check endpoints
- **File Storage:** Cloudflare R2 integration for file uploads
- **Background Tasks:** Celery integration for async task processing
- **Pydantic Models:** Data validation using Python type annotations
- **Redis Integration:** Caching and session storage
- **CORS Support:** Cross-origin resource sharing for frontend integration
- **Environment Configuration:** Flexible configuration management

## Technology Stack

- **Web Framework:** FastAPI
- **GraphQL:** Strawberry GraphQL
- **Authentication:** JWT with OTP verification
- **Email Services:** Multiple email providers support
- **File Storage:** Cloudflare R2
- **Caching:** Redis
- **Background Tasks:** Celery
- **HTTP Client:** httpx
- **Configuration:** Pydantic Settings
- **Environment Management:** python-dotenv
- **Data Models:** Pydantic models

## Troubleshooting

### Common Issues

1. **Config import failed error:**

   - Ensure your `.env` file is properly configured
   - Check that Redis is running
   - Verify all required environment variables are set

2. **Port already in use:**

   - Change the port in the uvicorn command: `--port 8001`
   - Kill the process using the port: `lsof -ti:8000 | xargs kill -9` (macOS/Linux)

3. **Redis connection error:**
   - Start Redis server: `redis-server`
   - Check Redis URL in `.env` file
   - Verify Redis is accessible on the configured port

### Logs

The application logs important information during startup, including:

- API base URL configuration
- Redis connection status
- OpenAI API key status

Check the console output for any configuration warnings or errors.
