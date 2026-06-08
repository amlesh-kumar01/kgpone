import axios from 'axios';

// Create a global axios instance pointing to the FastAPI backend
const api = axios.create({
  baseURL: '/api', // Assuming proxy or same domain, otherwise set full URL e.g., 'http://localhost:8000/api'
  withCredentials: true, // IMPORTANT: Allows cookies (HttpOnly tokens) to be sent cross-origin or same-origin
});

// Helper to get CSRF token from cookies
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

// Request Interceptor: Attach CSRF Token
api.interceptors.request.use(
  (config) => {
    // Only attach CSRF token to state-changing methods
    const methodsRequireCsrf = ['post', 'put', 'patch', 'delete'];
    if (methodsRequireCsrf.includes(config.method.toLowerCase())) {
      const csrfToken = getCookie('fastapi-csrf-token'); // default name used by fastapi-csrf-protect
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Silent Refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Check if error is 401 and we haven't already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject });
        }).then(() => {
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Attempt silent refresh
        await axios.post('/api/auth/refresh', {}, { withCredentials: true });
        
        processQueue(null);
        // Retry the original failed request
        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        // If refresh fails, we log the user out (client side redirect or event)
        window.dispatchEvent(new Event('auth-expired'));
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export default api;
