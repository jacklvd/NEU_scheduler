# NEUscheduler Frontend

React/Next.js frontend application for the NEUscheduler platform - an AI-powered academic planning tool for Northeastern University students.

## Overview

The frontend provides an intuitive interface for students to:

- Search and explore course catalogs
- Generate optimized class schedules
- Receive AI-powered course recommendations
- Manage academic planning across semesters
- Visualize schedule conflicts and preferences

## Technology Stack

- **Framework:** Next.js 15+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** Custom components with shadcn/ui
- **State Management:** (To be implemented)
- **API Communication:** GraphQL + REST API
- **Font:** Geist font family

## Project Structure

```bash
client/
├── app/                    # Next.js App Router
│   ├── courses/           # Course search and catalog pages
│   ├── planner/          # Academic planning pages
│   ├── schedule/         # Schedule management pages
│   ├── favicon.ico       # App favicon
│   ├── globals.css       # Global styles
│   ├── layout.tsx        # Root layout component
│   └── page.tsx          # Home page
├── components/            # React components
│   ├── auth/             # Authentication components
│   ├── magicui/          # Magic UI components with animations
│   │   └── ripple-button.tsx
│   ├── ui/               # Reusable UI components (shadcn/ui)
│   │   ├── avatar.tsx
│   │   ├── breadcrumb.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── pagination.tsx
│   │   ├── sonner.tsx
│   │   └── tooltip.tsx
│   ├── ai-planner.tsx    # AI-powered planning component
│   ├── course-search.tsx # Course search functionality
│   └── navbar.tsx        # Navigation component
├── lib/                  # Utility libraries
│   ├── api/             # API client configurations
│   ├── hooks/           # Custom React hooks
│   └── utils.ts         # Utility functions
├── public/              # Static assets
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
├── types/               # TypeScript type definitions
│   └── api.ts          # API type definitions
├── .husky/             # Git hooks configuration
├── .env                # Environment variables
├── .prettierignore     # Prettier ignore rules
├── .prettierrc         # Prettier configuration
├── components.json     # shadcn/ui configuration
├── eslint.config.mjs   # ESLint configuration
├── next-env.d.ts       # Next.js TypeScript declarations
├── next.config.ts      # Next.js configuration
├── package.json        # Dependencies and scripts
├── postcss.config.mjs  # PostCSS configuration
├── README.md           # This file
├── tsconfig.json       # TypeScript configuration
└── yarn.lock           # Yarn lock file
```

## Installation & Setup

### Prerequisites

- Node.js 18+
- yarn (recommended) or npm
- Backend server running (see [server README](../server/README.md))

### Quick Start

1. **Navigate to the client directory:**

   ```bash
   cd client
   ```

2. **Install dependencies:**

   ```bash
   yarn install
   # or
   npm install
   ```

3. **Set up environment variables:**

   Create a `.env.local` file in the client directory:

   ```env
   # API Configuration
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   NEXT_PUBLIC_GRAPHQL_URL=http://localhost:8000/api/graphql

   # App Configuration
   NEXT_PUBLIC_APP_NAME=NEUscheduler
   NEXT_PUBLIC_APP_VERSION=1.0.0
   ```

4. **Run the development server:**

   ```bash
   yarn dev
   # or
   npm run dev
   ```

5. **Open your browser:**

   Navigate to [http://localhost:3000](http://localhost:3000) to see the application.

## Available Scripts

```bash
# Development
yarn dev          # Start development server
yarn build        # Build for production
yarn start        # Start production server
yarn lint         # Run ESLint
yarn type-check   # Run TypeScript type checking

# Package management
yarn add <package>        # Add new dependency
yarn add -D <package>     # Add dev dependency
```

## Development

### Code Structure

- **`app/`** - Next.js App Router pages and layouts
- **`components/ui/`** - Reusable UI components (shadcn/ui based)
- **`components/magicui/`** - Enhanced UI components with animations
- **`public/`** - Static assets (images, icons, etc.)

### Styling

The project uses Tailwind CSS for styling with custom components from shadcn/ui:

```bash
# Add new shadcn/ui component
npx shadcn-ui@latest add <component-name>
```

### API Integration

The frontend communicates with the backend through:

- **REST API:** For simple CRUD operations
- **GraphQL:** For complex queries and real-time data

Example API usage:

```typescript
// REST API call
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
const data = await response.json();

// GraphQL query (to be implemented)
// const { data } = useQuery(GET_COURSES, { variables: { term: 'spring2024' } });
```

### Component Development

Components follow the shadcn/ui pattern with Tailwind CSS:

```typescript
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function CourseCard({ course }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{course.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <p>{course.description}</p>
        <Button variant="outline">Add to Schedule</Button>
      </CardContent>
    </Card>
  )
}
```

## Features (Planned)

- **Course Search:** Advanced filtering and search capabilities
- **Schedule Builder:** Drag-and-drop schedule creation
- **AI Recommendations:** Intelligent course suggestions
- **Conflict Detection:** Automatic schedule conflict resolution
- **Responsive Design:** Mobile-first, responsive interface
- **Dark Mode:** Theme switching support
- **Real-time Updates:** Live data synchronization

## Configuration

### Next.js Configuration

Key configurations in `next.config.ts`:

- TypeScript support
- Tailwind CSS integration
- API proxy settings (if needed)
- Build optimizations

### Tailwind Configuration

Custom theme extensions and component styles are configured in `tailwind.config.js`.

## Deployment

### Development Deployment

```bash
yarn build
yarn start
```

### Production Deployment

The application can be deployed to:

- **Vercel** (recommended for Next.js)
- **Netlify**
- **Docker containers**
- **Static hosting** (with `next export`)

For Vercel deployment:

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

## Troubleshooting

### Common Issues

1. **Module not found errors:**

   ```bash
   rm -rf node_modules package-lock.json yarn.lock
   yarn install
   ```

2. **TypeScript errors:**

   ```bash
   yarn type-check
   ```

3. **Build errors:**
   - Check environment variables are set
   - Ensure backend API is accessible
   - Verify all imports are correct

### Development Tips

- Use `yarn dev` for hot reloading during development
- Check browser console for client-side errors
- Use React Developer Tools for debugging
- Ensure backend server is running on `http://localhost:8000`

## Contributing

1. Follow the existing code style and component patterns
2. Use TypeScript for all new components
3. Add appropriate prop types and JSDoc comments
4. Test components in isolation when possible
5. Follow the established folder structure

## Backend API Integration

The frontend integrates with the backend API endpoints:

- **Health Check:** `GET /api/health`
- **Course Search:** `GET /api/courses`
- **GraphQL Endpoint:** `POST /api/graphql`

Ensure the backend server is running before starting frontend development.
