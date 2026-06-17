# 🎨 AyurPulse Frontend Technical Guide: Interview Perspective

This document serves as the comprehensive source of truth for the **AyurPulse** React + Vite frontend application. It covers the frontend architectural choices, libraries used, global state workflows, and advanced interview concepts (specifically silent authentication refresh via Axios interceptors).

---

## 🏛️ 1. Technical Stack & UI Architecture

The frontend is designed as a responsive, premium Single Page Application (SPA):
*   **Vite + React:** Serves as the build tool and runtime environment. Vite offers sub-second Hot Module Replacement (HMR) and utilizes ES Modules for extremely fast development builds compared to Webpack.
*   **Tailwind CSS:** Used for styling. Standardized color palettes, modern typography, glassmorphism, and smooth transitions are configured via `tailwind.config.js`.
*   **Axios:** Configured as the core HTTP client with interceptors for token injection and session recovery.
*   **Lucide React:** Used for rendering lightweight, responsive SVG icons.

---

## 🧬 2. Core Frontend Workflows & State Management

### 2.1. Global Authentication Context (`AuthContext.jsx`)
State persistence and role-based access control are coordinated via a central React Context:
*   **Persistent Session:** On initial load, the `AuthProvider` checks for an `access_token` in `localStorage`. If found, it fires an asynchronous `/auth/me` request to retrieve the current user's profile and populates the global `user` state, hiding loading spinners only after profile verification.
*   **Role-Based Routing:** Redirects users based on their role retrieved during authentication:
    *   **Patient Role (`"user"`)** $\rightarrow$ Routed to the Patient Dashboard page (`/dashboard`).
    *   **Doctor Role (`"doctor"`)** $\rightarrow$ Routed to the Doctor Dashboard page (`/doctor-dashboard`).
*   **Token Cleanup:** Any authorization rejection or logout automatically clears `localStorage` keys and resets the state to `null`.

### 2.2. Advanced Silent Authentication Refresh (Axios Interceptors)
This is a **critical intermediate-to-advanced frontend interview topic** demonstrating high security standards.

*   **The Problem:** Access tokens have a short lifespan (15 minutes) for security. When they expire, the backend rejects subsequent requests with a `401 Unauthorized` status. If the client does not handle this, the app will break or force a hard logout, resulting in a poor user experience.
*   **The Solution:** We configured **Axios Interceptors** in `frontend/src/services/api.js` to manage session recovery seamlessly in the background without user intervention:

```javascript
// Request Interceptor: Automatically injects the JWT access token into the header of every call
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Catches 401 errors, rotates tokens, and retries the original request
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Check if the server returned 401 and this is the first retry attempt
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; // Mark as retrying to prevent infinite loop
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token available');

        // Asynchronously request a new token pair using token rotation
        const refreshResponse = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = refreshResponse.data;
        
        // Save new rotated tokens in storage
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        // Update the header of the original failed request and retry it
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh token is expired or blacklisted -> Clear session and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login?expired=true';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
```

### 2.3. Patient Diagnostic Wizard Flow (`PatientDashboard.jsx`)
Coordinates the step-by-step diagnostic journey using React local state:
1.  **Image Upload Step:** Patients upload skin scan images. Standard forms parse the files, validating size limits (max 5MB) on the client side before sending a `multipart/form-data` request, receiving a `prediction_id` in response.
2.  **Quiz Step:** Simulates a wizard flow where the user answers a 6-question radio-button Prakriti questionnaire.
3.  **Parameters Customization:** Collects user variables like skin type, current season, and lifestyle checklist values (e.g. stress, high caffeine).
4.  **Results Render:** Submits options to the backend, displaying a 7-day treatment plan, custom ingredients, diet lists, and an interactive geolocation map detailing nearby pharmacies.

### 2.4. Doctor Customizer & Vetting Workspace (`DoctorDashboard.jsx`)
Provides an interactive scheduler editor for doctors to inspect and customize plans:
*   **Avoiding State Mutations (Interview Gold):** Directly modifying nested React state arrays causes UI rendering bugs and triggers side effects. To maintain state immutability, we perform a **deep copy** of the plan before editing:
    ```javascript
    const handleStartReview = (plan) => {
      // Create an independent deep copy of the plan object
      setEditingPlan(JSON.parse(JSON.stringify(plan)));
      setDoctorNotes(plan.doctor_notes || '');
    };
    ```
*   **Dynamic Inputs Syncing:** Day-by-day scheduler items, morning/evening lists, diet instructions, and weekly summaries are updated dynamically. Comma-separated strings are parsed into neat arrays on the fly.
*   **Vetting Submission:** The doctor writes customized annotations and clicks "Approve & Save Vetted Plan," updating the queue state seamlessly.

---

## 💡 3. Interview Focus: Common Frontend Questions & Answers

#### Q1: Why did you choose Vite over Create React App (CRA)?
**A:** Create React App is based on Webpack, which builds a complete dependency graph of the entire application before starting the local development server. As the codebase grows, compilation slows down significantly. Vite leverages browser-native ES Modules: it only compiles files as requested by the browser. For production builds, Vite uses Rollup, which generates highly optimized static assets with superior tree-shaking, resulting in smaller bundles and faster page load speeds.

#### Q2: What is the purpose of Axios Interceptors in your application?
**A:** Axios Interceptors act as middleware for HTTP requests and responses. The **Request Interceptor** automatically extracts the JWT access token from `localStorage` and appends it to the `Authorization` header, keeping our component fetch calls clean and dry. The **Response Interceptor** acts as a global error handler: it catches `401 Unauthorized` responses, pauses the application flow to request a new token pair silently using the refresh token, updates `localStorage`, and retries the original request without user interruption.

#### Q3: Why is standard object spreading (`{...plan}`) insufficient for managing state in the Doctor Customizer?
**A:** In JavaScript, standard object spreading (`{...plan}`) or `Object.assign()` only performs a **shallow copy**. If the object contains nested structures (such as our `days` array containing nested `morning`, `evening`, and `diet` objects), a shallow copy only copies the references to those nested structures. Modifying a day's diet would directly mutate the original state object, bypassing React's virtual DOM reconciliation and leading to UI rendering bugs. To prevent this, we perform a **deep copy** using `JSON.parse(JSON.stringify(plan))` to completely duplicate all nested objects and ensure state immutability.

#### Q4: How did you implement role-based security on the client side?
**A:** We use a global `AuthContext` to manage the authenticated user's state. When rendering protected views, the application checks `user.role`. If a patient attempts to access `/doctor-dashboard` or a doctor attempts to access patient pages, React router intercepts the navigation and redirects them to their respective dashboards.
