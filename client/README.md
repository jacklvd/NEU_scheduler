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
- **Authentication:** NextAuth.js v5
- **Styling:** Tailwind CSS v4
- **UI Components:** shadcn/ui + custom components
- **State Management:** React hooks + Context API
- **API Communication:** GraphQL + REST API
- **HTTP Client:** Built-in fetch + custom API clients
- **Form Handling:** Server Actions
- **Font:** Geist font family
- **Development:** Hot reloading, TypeScript, ESLint, Prettier

## Project Structure

```bash
client/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Authentication route group
│   │   ├── error/         # Auth error pages
│   │   ├── sign-in/       # Sign in page
│   │   ├── sign-up/       # Sign up page
│   │   └── layout.tsx     # Auth layout component
│   ├── api/               # API routes (server-side)
│   ├── courses/           # Course search and catalog pages
│   ├── dashboard/         # Dashboard page
│   ├── planner/           # Academic planning pages
│   ├── schedule/          # Schedule management pages
│   ├── favicon.ico        # App favicon
│   ├── globals.css        # Global styles with Tailwind CSS
│   ├── layout.tsx         # Root layout component
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── auth/              # Authentication components
│   │   ├── auth-form.tsx  # Login/signup form
│   │   ├── auth-guard.tsx # Route protection
│   │   └── user-dropdown.tsx # User menu dropdown
│   ├── magicui/           # Magic UI components with animations
│   │   └── ripple-button.tsx
│   ├── providers/         # Context providers
│   │   └── auth-provider.tsx # Authentication context
│   ├── ui/                # Reusable UI components (shadcn/ui)
│   │   ├── avatar.tsx
│   │   ├── breadcrumb.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── pagination.tsx
│   │   ├── sonner.tsx
│   │   └── tooltip.tsx
│   ├── ai-planner.tsx     # AI-powered planning component
│   ├── calendar-01.tsx    # Calendar component
│   ├── course-search.tsx  # Course search functionality
│   ├── custom-pagination.tsx # Custom pagination component
│   └── navbar.tsx         # Navigation component
├── hooks/                 # Custom React hooks
│   ├── use-mobile.ts      # Mobile detection hook
│   ├── use-pagination.ts  # Pagination logic hook
│   └── useCourses.ts      # Course data hooks
├── lib/                   # Utility libraries
│   ├── actions/           # Server actions
│   │   ├── auth-actions.ts # Authentication actions
│   │   └── graphql-actions.ts # GraphQL actions
│   ├── api/               # API client configurations
│   │   ├── auth.ts        # Authentication API
│   │   ├── course.ts      # Course API
│   │   └── graphql.ts     # GraphQL client
│   └── utils.ts           # Utility functions
├── public/                # Static assets
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
├── types/                 # TypeScript type definitions
│   └── api.ts            # API type definitions
├── certificates/          # SSL certificates (development)
├── constant/              # Application constants
├── .husky/                # Git hooks configuration
├── .env.local             # Environment variables
├── .prettierignore        # Prettier ignore rules
├── .prettierrc            # Prettier configuration
├── auth.ts                # NextAuth configuration
├── components.json        # shadcn/ui configuration
├── eslint.config.mjs      # ESLint configuration
├── middleware.ts          # Next.js middleware
├── next-env.d.ts          # Next.js TypeScript declarations
├── next.config.ts         # Next.js configuration
├── package.json           # Dependencies and scripts
├── postcss.config.mjs     # PostCSS configuration
├── README.md              # This file
├── tsconfig.json          # TypeScript configuration
└── yarn.lock              # Yarn lock file
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

   # NextAuth Configuration
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=your-super-secret-nextauth-key-change-this-in-production

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
  - **`(auth)/`** - Authentication route group with dedicated layout
  - **`api/`** - Server-side API routes
  - **`dashboard/`**, **`courses/`**, **`planner/`**, **`schedule/`** - Main app pages
- **`components/`** - React components organized by feature
  - **`auth/`** - Authentication-related components
  - **`ui/`** - Reusable UI components (shadcn/ui based)
  - **`providers/`** - React context providers
- **`hooks/`** - Custom React hooks for state management
- **`lib/`** - Utility libraries and API clients
  - **`actions/`** - Server actions for form handling
  - **`api/`** - API client configurations
- **`types/`** - TypeScript type definitions
- **`public/`** - Static assets (images, icons, etc.)

### Styling

The project uses Tailwind CSS for styling with custom components from shadcn/ui:

```bash
# Add new shadcn/ui component
npx shadcn-ui@latest add <component-name>
```

### API Integration

The frontend communicates with the backend through:

- **REST API:** For simple CRUD operations and health checks
- **GraphQL:** For complex queries and course data
- **Server Actions:** For form submissions and authentication

Example API usage:

```typescript
// REST API call
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
const data = await response.json();

// GraphQL query using custom hooks
const { courses, loading, error } = useCourseSearch();

// Server action
import { signIn } from '@/lib/actions/auth-actions';
await signIn(formData);
```

### Component Development

Components follow the shadcn/ui pattern with Tailwind CSS v4 and Northeastern theming:

```typescript
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function CourseCard({ course }) {
  return (
    <Card className="border-gray-200">
      <CardHeader className="bg-northeastern-red text-white">
        <CardTitle>{course.name}</CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        <p className="text-gray-600">{course.description}</p>
        <Button variant="outline" className="mt-4">
          Add to Schedule
        </Button>
      </CardContent>
    </Card>
  )
}
```

### Authentication Flow

The app uses NextAuth.js v5 with custom providers:

```typescript
// Protected route example
import { AuthGuard } from "@/components/auth/auth-guard"

export default function ProtectedPage() {
  return (
    <AuthGuard>
      <div>Protected content here</div>
    </AuthGuard>
  )
}
```

## Features (Implemented)

- **Authentication System:** Complete sign-in/sign-up with NextAuth.js
- **Course Search:** Advanced filtering and search with pagination (15 results per page)
- **Responsive Design:** Mobile-first, responsive interface
- **Northeastern Theming:** Official NEU colors and branding
- **Route Protection:** Auth guards for protected pages
- **Custom Pagination:** Built-in pagination component
- **Calendar Integration:** Calendar component for schedule visualization
- **AI Planner:** AI-powered course planning assistance
- **Real-time Validation:** Form validation and error handling
- **Navigation:** Responsive navbar with user dropdown

## Features (Planned)

- **Schedule Builder:** Drag-and-drop schedule creation
- **Conflict Detection:** Automatic schedule conflict resolution
- **Dark Mode:** Theme switching support
- **Real-time Updates:** Live data synchronization
- **Export/Import:** Schedule export to various formats

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
- **Authentication:** Server actions with JWT tokens
- **Course Search:** GraphQL queries for course data
- **Terms & Subjects:** GraphQL queries for academic terms
- **GraphQL Endpoint:** `POST /api/graphql`

Key API features:

- **Course Search:** Search courses by term, subject, and keywords
- **Pagination:** 15 results per page with custom pagination
- **Authentication:** Secure JWT-based authentication
- **Real-time Data:** GraphQL subscriptions for live updates

Ensure the backend server is running on `http://localhost:8000` before starting frontend development.
