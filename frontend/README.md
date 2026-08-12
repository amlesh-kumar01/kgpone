# KgpOne Frontend

The KgpOne frontend is a modern, responsive React application built with Vite and Tailwind CSS. It provides both an **Admin/Publisher Dashboard** for knowledge ingestion and a **Student Marketplace** for exam preparation.

## Key Features

- **Knowledge Ingestion**: Upload PDFs directly to S3 via presigned URLs. The backend automatically processes and parses these documents using Docling.
- **Analysis Studio**: Interactive dashboards for admins to trigger AI summarization, generate quizzes, and extract formulas from individual documents.
- **Course Exam Prep Hub**: A student-facing portal that aggregates insights across an entire course's documents, providing a master quiz bank, formula sheet, and course summary.
- **Dark Mode Support**: Beautiful Tailwind-based dark and light themes using `shadcn/ui`.

## Tech Stack

- **Framework**: React 18 + Vite
- **Routing**: React Router
- **Styling**: Tailwind CSS + `shadcn/ui` (Radix Primitives)
- **API**: Axios with centralized interception for JWT token refresh.
- **Markdown**: `react-markdown` + `remark-gfm` + `@tailwindcss/typography` for beautiful AI result rendering.

## Running Locally

To run the frontend locally during development:

1. Copy `.env.example` to `.env` (if applicable) and ensure `VITE_API_URL` points to your backend.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```

The application will be available at `http://localhost:5173`.
