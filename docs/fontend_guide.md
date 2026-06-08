# KnowledgeOS: Frontend Engineering Guide (For Beginners)

Welcome to the frontend team of **KnowledgeOS** (KgpOne)! This guide is designed to help you understand the file structure, core patterns, and the background task ingestion workflow from the client side.

---

## 🛠️ The Technology Stack

We build our interface using a modern, fast client-side stack:
1. **Build Tool**: **Vite** — Extremely fast build tool for React development.
2. **Framework**: **React** (JSX) — For modular, stateful component trees.
3. **Styling**: **Tailwind CSS** — Utility-first styling to construct consistent, responsive designs.
4. **HTTP Client**: **Axios** — Used to make REST requests to our FastAPI backend.
5. **Core State**: **React Context** — For simple state sharing (e.g. User Authentication status).

---

## 📁 Frontend File Structure (`/frontend`)

All source files are located inside the `frontend/src/` folder:

```text
frontend/
│
├── index.html                  # Main entry point template
├── vite.config.js              # Vite configuration (e.g. dev proxies)
│
└── src/
    ├── main.jsx                # Mounts the React application to the DOM
    ├── App.jsx                 # App router, global layouts, and guards
    ├── index.css / App.css     # Tailwind imports and custom global css
    │
    ├── components/             # Reusable, stateless or UI components
    │   └── ThemeToggle.jsx     # Controls light/dark theme state
    │
    ├── pages/                  # Full page layouts (views mapped to routes)
    │   ├── Login.jsx           # User sign-in page
    │   ├── Dashboard.jsx       # Main user dashboard containing workspace features
    │   └── Marketplace.jsx     # React Flow diagram listing learning nodes
    │
    ├── context/                # Global states
    │   └── AuthContext.jsx     # Manages user authentication status and tokens
    │
    ├── hooks/                  # Reusable custom hooks (e.g. useLocalStorage)
    │
    └── services/               # API clients and HTTP configurations
        ├── api.js              # Custom Axios instance (handles CSRF, token refresh)
        └── s3_client.js        # Helper to manage direct-to-S3 uploads
```

---

## 🔄 The Ingestion Upload Pipeline (Frontend Perspective)

To parse and process user PDF textbooks without overloading the server, we use a **direct-to-S3 uploading workflow**. Here is how you implement it as a frontend engineer:

```text
[Select PDF File] ──> [Request Presigned URL] ──> [Upload directly to S3] ──> [Send Webhook] ──> [Poll/Listen for Results]
```

### Step 1: Request a Presigned URL
When the user selects a `.pdf` file in a file-input, do not upload it immediately. Instead, send a small request to our API containing only metadata:
```javascript
// Request presigned URL from FastAPI backend
const response = await api.post('/workspace/upload-notes/presigned', {
  filename: file.name,
  file_size: file.size
});
const { upload_url, s3_key } = response.data;
```

### Step 2: Direct Upload to S3
Use the retrieved `upload_url` to send the file bytes straight to S3. 
* **Important**: You must make a `PUT` request with headers matching the S3 expectations, sending the raw file blob:
```javascript
// Direct pipe from client browser to AWS S3 bucket
await axios.put(upload_url, file, {
  headers: {
    'Content-Type': file.type
  }
});
```

### Step 3: Send Webhook to Backend
Once S3 returns a `200 OK` status, trigger the webhook to notify FastAPI that the file is safely vaulted. This joins the S3 location with educational context:
```javascript
// Trigger backend processing queue
const taskResponse = await api.post('/workspace/upload-notes/webhook', {
  s3_key: s3_key,
  course_id: 'TPMP-301',
  filename: file.name
});
const { task_id } = taskResponse.data;
```

### Step 4: Monitor Task Status (Polling)
The backend immediately returns a `task_id` with `status: "processing"`. Use this ID to poll the status endpoint or listen to Server-Sent Events (SSE) to update the UI once parsing succeeds:
```javascript
const pollTaskStatus = setInterval(async () => {
  const statusRes = await api.get(`/tasks/${task_id}`);
  if (statusRes.data.status === 'SUCCESS') {
    clearInterval(pollTaskStatus);
    alert('Processing completed! Content is ready.');
  } else if (statusRes.data.status === 'FAILURE') {
    clearInterval(pollTaskStatus);
    alert('Failed to process document.');
  }
}, 3000); // Check every 3 seconds
```

---

## 🚀 How to Run the Frontend Locally

1. **Install Node Packages**:
   Make sure you are in the `frontend/` directory and run:
   ```bash
   npm install
   ```

2. **Start Vite Development Server**:
   ```bash
   npm run dev
   ```
   *(By default, the site will open at `http://localhost:5173`.)*

3. **Routing Proxy**:
   Our `vite.config.js` is set up to automatically proxy any client requests starting with `/api` to the backend dev server (`http://localhost:8000`), avoiding CORS issues.
