# NEUscheduler

AI-powered academic planning tool for Northeastern University students.

## Project Structure

```bash
NEU_scheduler/
├── server/                     # Backend API (Python/FastAPI)
│   ├── app/                   # Application code
│   ├── poetry.lock           # Poetry lock file
│   ├── pyproject.toml       # Python dependencies & config
│   ├── README.md            # Backend setup instructions
│   └── .env                 # Environment variables
├── client/                    # Frontend (Next.js/React)
│   ├── app/                  # Next.js app directory
│   ├── components/           # React components
│   ├── public/              # Static assets
│   ├── package.json         # Node.js dependencies
│   └── README.md            # Frontend setup instructions
├── LICENSE
└── README.md                # This file
```

## Quick Start

### Prerequisites

- Python 3.13+
- Poetry (for Python dependency management)
- Node.js 18+ and yarn (for frontend)
- Redis (for caching and background tasks)

### Backend

```bash
cd server
poetry install
poetry run uvicorn app.main:app --reload
```

The backend will start on `http://localhost:8000`

### Frontend

```bash
cd client
yarn install
yarn dev
```

The frontend will start on `http://localhost:3000`

## API Endpoints

- **REST API:** `http://localhost:8000/api`
- **GraphQL:** `http://localhost:8000/api/graphql`
- **Health Check:** `http://localhost:8000/api/health`
- **API Documentation:** `http://localhost:8000/docs`

## Features

- 🎓 Course search and filtering
- 📅 Smart schedule generation
- 🤖 AI-powered course recommendations
- 📊 GraphQL API for flexible data queries
- ⚡ Real-time updates with background processing
- 🔄 Integration with Northeastern's course catalog

## Development

For detailed setup instructions, see:

- [Server README](./server/README.md) - Backend development guide
- [Client README](./client/README.md) - Frontend development guide
