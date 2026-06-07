# Frontend Engineer Guide

Welcome to the KgpOne Frontend team! We are building a high-velocity, lightweight web application using plain JavaScript to maintain speed and flexibility for the MVP.

## Tech Stack
- **Framework**: React 19 initialized with Vite
- **Styling**: Tailwind CSS (Utility-first)
- **Language**: JavaScript (ES6+)

## Project Structure (`/frontend/src/`)
- `components/`: UI atoms and specialized components (`chat/`, `pdf/`).
- `context/`: Global state context (`AuthContext`, `WorkspaceContext`).
- `hooks/`: Custom React hooks, including complex logic for SSE streams and PDF loading.
- `pages/`: Top-level route components.
- `services/`: API configuration and S3 presigned URL clients.

## Your Immediate Tasks

1. **Real-time Chat Streaming**:
   - The backend utilizes LangChain agents that stream tokens. 
   - **Task**: Implement the `useChatStream.js` hook to listen to Server-Sent Events (SSE) from the FastAPI backend and correctly append markdown tokens to the chat UI.

2. **PDF Viewer Integration**:
   - The Course Workspace features a split-pane layout with chat on one side and a document on the other.
   - **Task**: Implement the `PdfViewer.jsx` component and `usePdfRender.js` hook to load and render structural PDFs from our local S3 instance (LocalStack).

3. **Build Out the Pages**:
   - **Task**: Implement the UI layouts for `Login.jsx`, `Marketplace.jsx`, `Dashboard.jsx`, and the core `CourseWorkspace.jsx` using modern, responsive Tailwind CSS utility classes.

4. **S3 Client Handling**:
   - **Task**: Flesh out `services/s3_client.js` to handle browser-based parsing of presigned URLs provided by the backend to fetch secure documents without exposing AWS credentials.

## Running Locally
```bash
cd frontend
npm install
npm run dev
```
