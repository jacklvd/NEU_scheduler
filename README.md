# NEUscheduler

AI-powered academic planning tool for Northeastern University students.

## Project Structure

### Server (Backend)

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
│   │   │   └── course_resolver.py # Course query resolvers
│   │   └── types/
│   │       ├── __init__.py
│   │       ├── course.py        # Course GraphQL types
│   │       ├── schedule.py      # Schedule GraphQL types
│   │       └── user.py          # User GraphQL types
│   ├── neu_api/
│   │   ├── __init__.py
│   │   └── searchneu_client.py  # SearchNEU API client
│   ├── services/
│   │   └── html_parser.py       # HTML parsing utilities
│   └── worker/
│       ├── __init__.py
│       ├── celery_app.py        # Celery configuration
│       └── tasks.py             # Background tasks
├── poetry.lock                  # Poetry lock file
├── pyproject.toml              # Python dependencies & config
└── .env                        # Environment variables
```

### Client (Frontend)

```bash
client/
├── app/
│   ├── favicon.ico
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── public/
├── eslint.config.mjs
├── next-env.d.ts
├── next.config.ts
├── package.json
├── postcss.config.mjs
├── README.md
└── tsconfig.json
```

## Installation & Setup

### Prerequisites

- Python 3.13+
- Poetry (for Python dependency management)
- Node.js 18+ and yarn (for frontend)
- Redis (for caching and background tasks)

### Backend Setup

1. **Navigate to the server directory:**

   ```bash
   cd server
   ```

2. **Install Python dependencies using Poetry:**

   ```bash
   poetry install
   ```

3. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start Redis server (if running locally):**

   ```bash
   redis-server
   ```

5. **Run the FastAPI server:**

   ```bash
   # Using Poetry (recommended)
   poetry run python app/main.py

   # Or activate the virtual environment first
   poetry shell
   python app/main.py
   ```

   The server will start on `http://localhost:8000`

### Frontend Setup

1. **Navigate to the client directory:**

   ```bash
   cd client
   ```

2. **Install dependencies:**

   ```bash
   yarn
   ```

3. **Run the development server:**

   ```bash
   yarn dev
   ```

   The frontend will start on `http://localhost:3000`

## API Endpoints

- **REST API:** `http://localhost:8000`
- **GraphQL Playground:** `http://localhost:8000/graphql`
- **Health Check:** `http://localhost:8000/health`

## Features

- GraphQL API for course data queries
- Integration with SearchNEU API
- Background task processing with Celery
- AI-powered course recommendations
- Course schedule management

## Development

### Running with Poetry

```bash
cd server
poetry run python app/main.py
```

### Running Background Tasks

```bash
cd server
poetry run celery -A app.worker.celery_app worker --loglevel=info
```
