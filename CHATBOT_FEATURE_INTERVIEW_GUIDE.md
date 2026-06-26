# 🌿 AyurBot — Chatbot Feature: Complete Interview Guide

> This document covers every technical and functional aspect of the **AyurBot** chatbot built inside **AyurPulse**, designed to help you confidently explain it in any interview.

---

## 📌 Table of Contents

1. [Feature Overview](#1-feature-overview)
2. [Tech Stack Used](#2-tech-stack-used)
3. [System Architecture](#3-system-architecture)
4. [Dual Chat Modes](#4-dual-chat-modes)
5. [How It Works — Step by Step Flow](#5-how-it-works--step-by-step-flow)
6. [Backend: API Endpoints](#6-backend-api-endpoints)
7. [Backend: Chat Controller (LLM Logic)](#7-backend-chat-controller-llm-logic)
8. [Frontend: ChatPage UI](#8-frontend-chatpage-ui)
9. [Security: JWT Authentication](#9-security-jwt-authentication)
10. [Conversation History (Multi-turn Chat)](#10-conversation-history-multi-turn-chat)
11. [Mock/Fallback Mode](#11-mockfallback-mode)
12. [Key Design Decisions](#12-key-design-decisions)
13. [Interview Q&A — Ready Answers](#13-interview-qa--ready-answers)

---

## 1. Feature Overview

**AyurBot** is an AI-powered Ayurvedic wellness chatbot embedded inside the AyurPulse web application. It allows logged-in users to ask natural language questions in **two distinct modes**:

### 🟢 General Mode ("Ask Anything")
- Ayurvedic doshas (Vata, Pitta, Kapha)
- Herbs, skin care routines, and nutrition
- General Ayurvedic lifestyle tips and wellness advice

### 📋 Plan Chat Mode ("My Plan Chat")
- Users select one of their generated Ayurvedic treatment plans
- AyurBot answers questions specifically about **that plan's ingredients, routines, and recommendations**
- The full plan JSON is injected into the system prompt — bot acts as an expert on that exact plan

**What makes it unique:**
- Powered by **Meta's LLaMA 3.1 8B Instant** model via the **Groq API** — extremely fast LLM inference
- **Two segregated chat modes** with independent message histories — switching tabs doesn't clear context
- **Plan-aware chat** — bot knows your exact diet, morning routine, herbs, and doctor notes
- Supports **multi-turn conversation** (remembers the full chat history per tab)
- Secured behind **JWT authentication** — only logged-in users can access it
- Has a **graceful mock fallback** when no API key is configured (useful for local dev/testing)

---

## 2. Tech Stack Used

| Layer       | Technology                          | Purpose                                    |
|-------------|-------------------------------------|--------------------------------------------|
| **LLM**     | Meta LLaMA 3.1 8B Instant (via Groq)| Generating Ayurvedic answers               |
| **LLM SDK** | `langchain-groq`, `langchain`       | LLM invocation and message schema          |
| **Backend** | FastAPI (Python)                    | REST API server                            |
| **Auth**    | JWT (HS256) via `python-jose`       | Protect the chatbot endpoint               |
| **Frontend**| React (Vite), Axios                 | Chat UI and API communication              |
| **Styling** | Tailwind CSS                        | Responsive, beautiful chat bubbles         |
| **DB**      | MongoDB (Motor - async driver)      | User data, user_plans (fetched for context)|

---

## 3. System Architecture

```
User (Browser)
    │
    │  GET /api/v1/chat/plans          (fetch user's plan list for selector)
    │  POST /api/v1/chat  { message, history[], chat_mode, plan_id? }
    │  Authorization: Bearer <JWT>
    ▼
FastAPI Backend (chat.py — Router)
    │
    │  1. Validates JWT token → extracts user_id
    │  2. Delegates to handle_chat_message(message, user_id, history, chat_mode, plan_id)
    ▼
chat_controller.py (LLM Logic)
    │
    │  3. If chat_mode == "plan":
    │       → Fetches plan from MongoDB by plan_id
    │       → Verifies plan belongs to the user
    │       → Serializes plan to JSON → injects into system prompt
    │  4. If chat_mode == "general":
    │       → Uses the standard GENERAL_SYSTEM_PROMPT
    │
    │  5. Builds message list:
    │     [ SystemMessage ] + [ history turns ] + [ HumanMessage ]
    │
    │  6. Calls Groq API (LLaMA 3.1 8B Instant) via langchain's ainvoke() (async)
    ▼
Groq Cloud API  ────► LLaMA 3.1 8B Instant Model
    │
    │  7. Returns AI-generated answer
    ▼
FastAPI Response → { answer: "...", sources: [] }
    │
    ▼
React ChatPage (ChatPage.jsx)
    │
    │  8. Appends bot message to correct tab's message array
    │  9. Scrolls to bottom smoothly
    └─► User reads the answer
```

---

## 4. Dual Chat Modes

This is a key feature added in the latest implementation. The chat page has **two tabs** — each with its own independent conversation history and behaviour.

### Tab 1: "Ask Anything" (General Mode)
- `chat_mode: "general"` in the API request
- Uses `GENERAL_SYSTEM_PROMPT` — a warm Ayurvedic assistant persona
- No plan_id required
- Suitable for general dosha, herb, and wellness questions

### Tab 2: "My Plan Chat" (Plan Mode)
- `chat_mode: "plan"` in the API request
- User first sees a **Plan Selector Screen** that lists all their generated plans
- After selecting a plan, the plan's MongoDB document (diet, routines, herbs, doctor notes) is serialized to JSON and injected into the system prompt
- AyurBot answers **only** based on what's in that specific plan
- The `plan_id` is sent with every message in plan mode

### Segregated Histories
```js
const [messages, setMessages] = useState([]);       // General chat history
const [planMessages, setPlanMessages] = useState([]); // Plan chat history
```
Both arrays are maintained simultaneously — switching tabs does **not** lose history.

---

## 5. How It Works — Step by Step Flow

### Step 1: User Selects a Mode
- **General tab** — user types directly and starts chatting
- **Plan tab** → app calls `GET /api/v1/chat/plans` to load the user's plans → user clicks a plan card → plan chat begins

### Step 2: Frontend Sends Request
```js
// From ChatPage.jsx
const payload = {
  message: text,
  history: currentHistory.map((m) => ({ role: m.role, content: m.content })),
  chat_mode: activeTab,          // "general" or "plan"
};

if (activeTab === 'plan') {
  payload.plan_id = selectedPlanId;  // MongoDB ObjectId of selected plan
}

const response = await api.post('/chat', payload);
```
- The `api` axios instance auto-attaches the `Bearer <JWT>` token from `localStorage`
- Full conversation history for the **active tab** is sent with every request

### Step 3: Backend Validates JWT
- `Depends(get_current_user)` runs automatically on every request
- If the token is missing, invalid, or expired → **401 Unauthorized** returned
- On success → `user_id` is extracted from the token payload

### Step 4: Controller Builds the System Prompt
```python
if chat_mode == "plan" and plan:
    plan_json = json.dumps(cleaned_plan, indent=2)
    system_prompt = f"""
You are AyurBot.
The user has selected the following personalized Ayurvedic treatment plan.
Plan Details:
{plan_json}
Use the plan as the primary source of truth.
Answer questions based on the plan's:
- Condition, Dominant dosha, Diet recommendations
- Morning routine, Evening routine, Lifestyle recommendations, Doctor notes
If information is not present in the plan, clearly say so.
Do not invent treatments not mentioned in the plan.
"""
else:
    system_prompt = GENERAL_SYSTEM_PROMPT
```

### Step 5: Controller Builds LLM Messages
```python
messages = [SystemMessage(content=system_prompt)]

for turn in history:
    if turn["role"] == "user":
        messages.append(HumanMessage(content=turn["content"]))
    elif turn["role"] == "bot":
        messages.append(AIMessage(content=turn["content"]))

messages.append(HumanMessage(content=user_message))
```
- The system prompt defines AyurBot's personality and constraints
- Previous turns are **replayed** so the LLM understands full context
- The new question is appended last

### Step 6: LLM is Invoked Asynchronously
```python
response = await llm.ainvoke(messages)
return { "answer": response.content, "sources": [] }
```
- Uses `ainvoke()` (async) — non-blocking, works perfectly with FastAPI's async architecture
- Temperature is set to `0.2` → **more factual, less hallucination**
- Max tokens: `1024` — enough for a thorough Ayurvedic explanation

### Step 7: Response Displayed in UI
- Bot message bubble appears on the left side with smooth animation
- A "Thinking…" spinner is shown while waiting for the response
- If sources are present, they appear as reference pills below the message

---

## 6. Backend: API Endpoints

**File:** `app/routes/chat.py`

### Endpoint 1: Fetch User Plans

```
GET /api/v1/chat/plans
Authorization: Bearer <access_token>
```

**Response:**
```json
[
  {
    "id": "6847c2a1f3e9a40012b4cd91",
    "title": "Acne Treatment Plan",
    "condition": "acne",
    "dosha": "pitta",
    "created_at": "2026-06-15"
  }
]
```
- Returns all plans the logged-in user has generated, sorted newest-first
- Condition is extracted from `plan_id` or `title` (e.g., "ACNE" → `"acne"`)
- Dosha is read from `dosha_focus` field or parsed from `plan_id` as fallback

### Endpoint 2: Send a Chat Message

```
POST /api/v1/chat
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "What herbs help reduce Pitta dosha?",
  "history": [
    { "role": "user", "content": "Tell me about Vata dosha" },
    { "role": "bot", "content": "Vata dosha governs movement and is associated with..." }
  ],
  "chat_mode": "general",
  "plan_id": null
}
```

**Plan mode request:**
```json
{
  "message": "Why was Neem recommended in my plan?",
  "history": [],
  "chat_mode": "plan",
  "plan_id": "6847c2a1f3e9a40012b4cd91"
}
```

**Response:**
```json
{
  "answer": "For Pitta dosha, cooling herbs like Amla, Shatavari, and Brahmi are excellent...",
  "sources": []
}
```

**Validation Rules:**
- `message`: minimum 1 character, maximum 1000 characters (Pydantic enforced)
- `history`: optional list of `{role, content}` dicts (defaults to empty)
- `chat_mode`: `"general"` or `"plan"` (defaults to `"general"`)
- `plan_id`: required when `chat_mode` is `"plan"`

**Error Handling:**
- `401 Unauthorized` → JWT missing or expired
- `403 Forbidden` → plan does not belong to the requesting user
- `404 Not Found` → invalid `plan_id` or plan not found
- `422 Unprocessable Entity` → validation error (e.g., empty message)
- `500 Internal Server Error` → LLM error, wrapped with a descriptive message

---

## 7. Backend: Chat Controller (LLM Logic)

**File:** `app/controllers/chat_controller.py`

### System Prompt Engineering

**General Mode Prompt:**
```python
GENERAL_SYSTEM_PROMPT = """You are AyurBot, a warm, friendly, and knowledgeable
Ayurvedic wellness assistant for AyurPulse.
Answer the user's question about Ayurveda, health, herbs, nutrition, recipes,
wellness, or general life tips based on your comprehensive knowledge of Ayurveda.
Keep your response clear, helpful, well-structured, and easy to read.
Avoid sounding dry or overly clinical. If you mention medical suggestions, add
a gentle reminder that they should consult their Ayurvedic practitioner...
Do not refer to technical concepts like 'RAG', 'retrieval', or 'database'...
Do not start your response with greetings like 'Namaste' or 'Hello'."""
```

**Why this prompt works:**
- Sets a **warm, friendly persona** (not a cold API)
- Instructs to **avoid technical jargon** (no mention of RAG, databases)
- Prevents unnecessary greetings — user gets answers faster
- Reminds users to consult practitioners for medical advice (legal safety)

**Plan Mode Prompt:**
- The entire plan MongoDB document is serialized to JSON (`json.dumps(cleaned_plan, indent=2)`)
- Sensitive fields (`_id`, `user_id`) are stripped before injection
- LLM is explicitly told to **only** use the plan as source of truth
- LLM is told to clearly state if something is not in the plan (no hallucination)

### LLM Singleton Pattern
```python
@lru_cache(maxsize=1)
def _get_llm() -> ChatGroq:
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=settings.GROQ_API_KEY,
        temperature=0.2,
        max_tokens=1024,
    )
```
- `@lru_cache(maxsize=1)` → **LLM client is created only once** and reused across requests
- This prevents unnecessary object creation on every API call (performance optimization)
- Temperature `0.2` = answers are more accurate and fact-based, less creative/random

### MongoDB Document Serialization
```python
def serialize_mongo_doc(doc: dict) -> dict:
    """Helper to convert MongoDB ObjectId and datetime objects to strings recursively."""
```
- MongoDB documents contain `ObjectId` and `datetime` objects that are not JSON-serializable
- This utility recursively converts them to strings before passing to `json.dumps()`
- Required for plan mode — otherwise `json.dumps(plan)` would crash

### Plan Access Control
```python
plan = await db["user_plans"].find_one({"_id": obj_id})
if not plan:
    raise ValueError(f"Plan not found.")
if plan.get("user_id") != user_id:
    raise PermissionError("Access denied. This plan does not belong to you.")
```
- Plans are fetched by `ObjectId` from MongoDB
- Ownership is **always verified** — a user cannot chat about another user's plan
- Returns `404` for missing plans, `403` for unauthorized access

### Helper: Condition Extraction
```python
def get_condition_from_plan_id(plan_id: str, title: str = "") -> str:
    """Extract condition name (e.g. 'acne', 'blackheads') from plan_id or title."""
    search_str = (plan_id + " " + title).upper()
    if "ACNE" in search_str: return "acne"
    elif "BLACKHEAD" in search_str: return "blackheads"
    elif "DARK SPOTS" in search_str: return "dark_spots"
    elif "PORES" in search_str: return "pores"
    elif "WRINKLES" in search_str: return "wrinkles"
    return "general"
```
- Used when returning the plan list to the frontend
- Parses the condition from `plan_id` or `title` string — handles naming inconsistencies

---

## 8. Frontend: ChatPage UI

**File:** `frontend/src/pages/ChatPage.jsx`

### Key UI Features

| Feature | Implementation |
|---------|---------------|
| **Dual tab navigation** | "Ask Anything" + "My Plan Chat" tabs with active state styling |
| **Plan Selector Screen** | Card grid shown when plan tab is active and no plan selected |
| **Dosha-colored badges** | Pitta = amber, Vata = sky blue, Kapha = emerald on plan cards |
| **Active Plan Banner** | Shows selected plan name at top of chat with "Switch Plan" button |
| **Suggested Questions** | 5 general chips + 6 plan-specific chips shown on empty state |
| **Segregated histories** | `messages` + `planMessages` — switching tabs preserves both |
| **User bubble** | Right-aligned, emerald gradient background |
| **Bot bubble** | Left-aligned, white card with shadow |
| **Loading indicator** | Animated spinner with "Thinking…" text |
| **Auto-scroll** | `useRef` + `scrollIntoView({ behavior: 'smooth' })` |
| **Auto-focus input** | `inputRef.current?.focus()` when tab or plan changes |
| **Enter to send** | `onKeyDown` handler (Shift+Enter = new line) |
| **Online badge** | Pulsing green indicator in header |
| **Source pills** | References shown below bot messages (when available) |

### State Management
```js
// Navigation
const [activeTab, setActiveTab] = useState('general'); // 'general' or 'plan'

// Segregated message histories
const [messages, setMessages] = useState([]);       // Ask Anything (General)
const [planMessages, setPlanMessages] = useState([]); // My Plan Chat

// Input & Loading
const [inputValue, setInputValue] = useState('');
const [isLoading, setIsLoading] = useState(false);

// Plan selection
const [userPlans, setUserPlans] = useState([]);
const [selectedPlanId, setSelectedPlanId] = useState(null);
const [isPlansLoading, setIsPlansLoading] = useState(false);
```

### Plan Selector Flow
1. User clicks **"My Plan Chat"** tab
2. `fetchUserPlans()` calls `GET /chat/plans`
3. Plan cards are rendered in a responsive grid (1 col on mobile, 2 on sm+)
4. Clicking a card: sets `selectedPlanId`, clears `planMessages`, shows chat
5. **Switch Plan** button resets `selectedPlanId` and re-fetches plans

### Error Handling in UI
```js
catch (err) {
  const errMsg = err?.response?.data?.detail || 'Something went wrong. Please try again.';
  // Displays the error as a bot message with ⚠️ prefix
}
```
- Errors are shown **inline as bot messages** — no jarring alert popups
- Applied to both general and plan chat modes

---

## 9. Security: JWT Authentication

**How the chatbot is protected:**

1. User logs in → receives `access_token` (15 min expiry) + `refresh_token` (7 days)
2. Tokens stored in `localStorage`
3. Every chatbot request includes: `Authorization: Bearer <access_token>`
4. FastAPI dependency `get_current_user` verifies the token on every request
5. If token expires → `api.js` interceptor automatically calls `/auth/refresh` and retries
6. If refresh also fails → user is redirected to `/login?expired=true`

```js
// From api.js — automatic token refresh logic
if (error.response?.status === 401 && !originalRequest._retry) {
  originalRequest._retry = true;
  // ... refresh token and retry original request
}
```

**Why JWT?**
- Stateless — server doesn't need to store session data
- Scalable — works perfectly with FastAPI's async architecture
- Short-lived access tokens minimize security risk

**Extra: Plan-level authorization**
- Even with a valid JWT, users cannot access another user's plan
- The controller checks `plan.get("user_id") != user_id` and raises `403 Forbidden`

---

## 10. Conversation History (Multi-turn Chat)

**The chatbot supports full multi-turn conversations.** This means AyurBot remembers what was said earlier in the session — independently for each tab.

**How it works:**
- React maintains **two separate** `messages` arrays (general + plan)
- On every new message send, the **entire history for the active tab** is sent to the backend
- The backend replays all previous turns as `HumanMessage` / `AIMessage` objects before the new question
- The LLM sees the full context and can reference previous answers

**Example — General Mode:**
```
User: "Tell me about Pitta dosha"
Bot:  "Pitta dosha is associated with fire and water elements..."

User: "What foods should I avoid for it?"  ← refers to "it" (Pitta)
Bot:  "For Pitta dosha specifically, you should avoid..."  ← correctly understands context
```

**Example — Plan Mode:**
```
User: "Why is Neem in my morning routine?"
Bot:  "According to your plan, Neem is recommended for its antibacterial properties..."

User: "Can I replace it with something else?"
Bot:  "Based on your plan's condition (acne) and dosha (Pitta)..."  ← still in plan context
```

**Note:** History is stored only in **frontend React state** (not in MongoDB), so it resets on page refresh — keeping the architecture simple and stateless.

---

## 11. Mock/Fallback Mode

If no valid Groq API key is configured, the chatbot automatically enters **Mock Mode**:

```python
def _is_dummy_api_key() -> bool:
    key = settings.GROQ_API_KEY or ""
    dummy_prefixes = ["gsk_dummy", "your_key", "change-this", "test_key", "placeholder"]
    return any(key.lower().startswith(p) for p in dummy_prefixes)
```

**Mock response for General mode:**
```
[MOCK MODE — Set a real GROQ_API_KEY to get AI-generated answers]

Based on my general knowledge of Ayurveda, here is a mock response
for your question: "What is Pitta dosha?"
```

**Mock response for Plan mode:**
```
[MOCK MODE — Set a real GROQ_API_KEY to get AI-generated answers]

Based on your selected plan "Acne Treatment Plan", here is a mock response
for your question: "Why was Neem recommended?"
```

**Why this is useful:**
- Developers can run the full app locally without needing a real API key
- The frontend and backend integration can be tested without LLM costs
- Prevents crashes — the app always responds gracefully
- **Plan mock mode** even references the selected plan's title, making it easy to test plan mode UI flow

---

## 12. Key Design Decisions

### 1. Why Groq + LLaMA instead of OpenAI?
- **Groq** offers extremely low latency inference (often sub-second response times)
- **LLaMA 3.1 8B Instant** is free-tier friendly and more than capable for Q&A tasks
- Open-source model = more control and no dependency on a closed ecosystem

### 2. Why two separate chat modes instead of one?
- General chat and plan chat have **fundamentally different system prompts**
- Mixing them would make the bot try to answer "what is Pitta?" using your plan data, which doesn't make sense
- Segregated states also mean users don't lose general chat history when switching to plan mode

### 3. Why inject the full plan JSON into the system prompt?
- This gives the LLM **precise, structured knowledge** about the exact plan
- The bot knows diet recommendations, morning/evening routines, specific herbs and doctor notes
- Alternative (few-shot retrieval from plan) would be more complex and slower
- Trade-off: large plans increase prompt size, but `1024 max_tokens` keeps responses concise

### 4. Why `@lru_cache` on the LLM client?
- Creating a `ChatGroq` object on every request would be wasteful
- `lru_cache(maxsize=1)` ensures a **singleton** — created once, reused forever
- This is a standard Python performance optimization for expensive object initialization

### 5. Why temperature = 0.2?
- Ayurvedic advice should be **accurate and consistent**, not creative
- Low temperature = deterministic, factual answers
- Higher temperature would cause the bot to "hallucinate" herbs or dosages

### 6. Why is history sent from the frontend, not stored in DB?
- **Simpler architecture** — no need for a `chat_sessions` MongoDB collection
- Each browser session is independent
- Keeps the backend stateless and scalable
- Trade-off: history is lost on page refresh (acceptable for a wellness chatbot)

### 7. Why async (`ainvoke`) instead of sync?
- FastAPI is an async framework — blocking calls would freeze the event loop
- `ainvoke()` is non-blocking, allowing the server to handle other requests while waiting for Groq

### 8. Why serialize MongoDB docs before JSON dump?
- MongoDB returns `ObjectId` and `datetime` objects that Python's `json.dumps()` can't handle
- `serialize_mongo_doc()` recursively converts them to strings
- This is required for plan mode to work without errors

---

## 13. Interview Q&A — Ready Answers

**Q: What is AyurBot and what does it do?**

> AyurBot is an AI-powered Ayurvedic wellness chatbot in AyurPulse. It has two modes: a general mode where users can ask anything about Ayurveda — doshas, herbs, skin routines, nutrition — and a plan chat mode where users can select one of their generated treatment plans and ask specific questions about that plan's ingredients, routines, and recommendations. It's powered by Meta's LLaMA 3.1 model running on Groq's ultra-fast inference platform.

---

**Q: What are the two chat modes and how are they different?**

> "Ask Anything" (general mode) uses a generic Ayurvedic assistant system prompt and can answer any wellness question. "My Plan Chat" (plan mode) fetches the user's selected plan from MongoDB, serializes it to JSON, and injects it directly into the system prompt — so the bot becomes an expert specifically on *that* plan's treatments. The two modes have completely separate message histories in React state, so switching tabs doesn't clear either conversation.

---

**Q: How does the chatbot maintain conversation context?**

> The frontend (React) stores all messages in two separate state arrays — one for general, one for plan chat. Every time the user sends a new message, the entire conversation history for the active tab is sent to the backend as a JSON array. The backend then reconstructs the full message chain — system prompt, all previous turns, and the new question — before invoking the LLM. This gives the model full context to understand follow-up questions.

---

**Q: How is the chatbot secured?**

> The `/api/v1/chat` endpoint is protected by JWT authentication. A user must be logged in to use it. The React frontend attaches the Bearer token to every request via an Axios interceptor. If the token expires, the interceptor automatically refreshes it using the refresh token, then retries the original request. If refresh also fails, the user is redirected to login. Additionally, in plan mode, even with a valid JWT, the backend verifies that the requested plan belongs to the requesting user — unauthorized access returns a 403 Forbidden.

---

**Q: What LLM did you use and why?**

> I used Meta's LLaMA 3.1 8B Instant model via the Groq API. I chose Groq because it offers industry-leading low-latency inference — responses come back in under a second usually. The 8B model is efficient yet powerful enough for Ayurvedic Q&A. I also set the temperature to 0.2 to keep responses accurate and factual rather than creative.

---

**Q: How did you design the system prompt?**

> I designed two different prompts. The general prompt defines AyurBot's persona as a warm, friendly Ayurvedic assistant — it avoids technical terms like 'RAG' or 'database', skips generic greetings, and reminds users to consult a practitioner for medical advice. The plan prompt is dynamically generated — I serialize the user's full plan JSON (diet, routines, herbs, doctor notes) and inject it as context. The LLM is then told to treat it as the single source of truth and to clearly state when something isn't in the plan, which prevents hallucination.

---

**Q: How does the Plan Chat mode work end to end?**

> When a user clicks the "My Plan Chat" tab, the frontend calls `GET /api/v1/chat/plans` to load all their generated plans. These are shown as clickable cards with dosha-colored badges and condition info. After selecting a plan, every subsequent message sends the plan's MongoDB `_id` along with `chat_mode: "plan"`. The backend fetches that plan document, verifies the user owns it, serializes it to JSON (stripping `_id` and `user_id`), and injects it into the system prompt. The LLM then answers exclusively based on what's in that plan.

---

**Q: What happens if the API key is not set?**

> The controller has a `_is_dummy_api_key()` check that detects placeholder or missing keys. In that case it returns a clearly labeled mock response, so the app never crashes. In plan mode, the mock response even includes the plan's title so you can still test the full UI flow without a real API key. This was important for local development — the team could run the full stack without needing a real API key.

---

**Q: Why did you use `@lru_cache` on `_get_llm()`?**

> Creating the `ChatGroq` client involves network initialization and config loading. Doing this on every API call would be wasteful. `@lru_cache(maxsize=1)` turns it into a singleton — it's created once on the first request and reused for all subsequent requests. This is a standard Python optimization pattern for expensive resources.

---

**Q: Is the chat history stored in the database?**

> No, and that was a deliberate design decision. Storing chat history in MongoDB would require a `chat_sessions` collection, session IDs, and more complex queries. Instead, I kept it simple — history lives in React state and is sent with every request. The trade-off is that history resets on page refresh, which is acceptable for a wellness assistant use case. The architecture stays stateless and scalable.

---

**Q: How does the frontend handle errors from the chatbot?**

> Instead of showing alert popups (which are jarring), errors are displayed inline as bot messages with a ⚠️ prefix. The error message is extracted from the backend's `detail` field if available, or falls back to a generic "Something went wrong" message. This keeps the user experience smooth and consistent — and it works the same way in both general and plan chat modes.

---

**Q: What is the API contract for the chatbot endpoint?**

> It's a POST request to `/api/v1/chat` with a JSON body containing `message` (string, 1-1000 chars), `history` (optional array of `{role, content}` objects), `chat_mode` ("general" or "plan"), and optionally `plan_id` (MongoDB ObjectId string, required in plan mode). The response is `{answer: string, sources: []}`. Pydantic models enforce input validation, and FastAPI generates OpenAPI docs for it automatically.

---

**Q: How do you prevent one user from accessing another user's plan?**

> In plan mode, the backend fetches the plan from MongoDB using the provided `plan_id`. After fetching, it checks `plan.get("user_id") != user_id`. If the plan doesn't belong to the requesting user, a `PermissionError` is raised which the route handler catches and returns as a `403 Forbidden` HTTP response. This ensures users can only chat about their own plans, even if they somehow obtain another plan's ID.

---

## 📁 Relevant Files — Quick Reference

| File | Purpose |
|------|---------|
| [`app/routes/chat.py`](app/routes/chat.py) | FastAPI router — 2 endpoints: `GET /chat/plans` + `POST /chat`; request/response Pydantic models |
| [`app/controllers/chat_controller.py`](app/controllers/chat_controller.py) | LLM logic — dual mode system prompts, plan fetching, history building, Groq invocation |
| [`frontend/src/pages/ChatPage.jsx`](frontend/src/pages/ChatPage.jsx) | React chat UI — dual tab navigation, plan selector, segregated histories, suggested questions |
| [`frontend/src/services/api.js`](frontend/src/services/api.js) | Axios instance — auto-attaches JWT, handles 401/token refresh |
| [`app/config/settings.py`](app/config/settings.py) | App configuration — GROQ_API_KEY, JWT settings, model params |
| [`app/main.py`](app/main.py) | App entry point — registers the chat router |

---

*Generated for AyurPulse v1.0.0 — AyurBot Chatbot Feature (Updated: Dual Chat Mode)*
