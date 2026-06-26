# KgpOne Frontend — Architecture & State Management Guide

## 1. Overview
The frontend is built with React, Vite, and TailwindCSS (using shadcn/ui components). It interacts with the FastAPI backend.

## 2. Global State & Contexts

### `AuthContext`
- **Purpose**: Manages user authentication state (`user`, `loading`), login, register, and logout functions.
- **Location**: `src/context/AuthContext.jsx`
- **Usage**: Fetches from `/api/v1/users/login` and `/api/v1/users/me`. Stores JWT access tokens in `localStorage`.

### `AcademicContext`
- **Purpose**: A role-scoped centralized context that caches the University's core structure (Departments and Courses).
- **Location**: `src/context/AcademicContext.jsx`
- **How it works**: 
  - Instead of fetching the global catalog on every page load, it fetches `departments` and `courses` **exactly once** when an Admin or Publisher accesses the restricted sections.
  - Exposes `departments`, `courses`, `loading`, and a `refreshAcademicData` function.
- **Why**: "Fetch once, apply everywhere". Reduces redundant API calls, lowers latency for publishers, and prevents multiple `Promise.all` failures from breaking individual pages.

## 3. Layouts & Routing

- **`AuthLayout`**: Wrapper for Login and Register pages.
- **`DashboardLayout`**: Main layout with the Sidebar and Topbar for authenticated users.
- **`AcademicLayout`**: 
  - Wraps Publisher/Admin-specific routes (`/departments`, `/courses`, `/documents`).
  - Instantiates the `AcademicProvider` so that the heavy catalog data is only loaded for authorized personnel managing the academic structure.
- **Protected Routes**: We use a custom `<ProtectedRoute>` wrapper in `App.jsx` to enforce Role-Based Access Control (RBAC) on the client side before ever hitting the backend.

## 4. API Client (`lib/api.js`)
We use an Axios instance (`api.js`) that automatically intercepts all outgoing requests and injects the `Authorization: Bearer <token>` header from `localStorage`.

## 5. Page Implementations
- **`Documents.jsx`**: Handles knowledge ingestion. Uses `AcademicContext` for instant cascading dropdowns (Department -> Course). It fetches "Offerings" dynamically based on the selected course.
- **`Courses.jsx`**: Uses `AcademicContext` to display the catalog. Upon creating a new course, it calls `refreshAcademicData()` to update the global state instantly without a hard reload.
- **`Departments.jsx`**: Uses `AcademicContext` to display the departments instantly.

