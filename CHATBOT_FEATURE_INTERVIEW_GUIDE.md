# 🌿 AyurBot — Chatbot Feature: Complete Interview Guide

> This document covers every technical and functional aspect of the **AyurBot** chatbot built inside **AyurPulse**, designed to help you confidently explain it in any interview.

---

## 📌 Table of Contents

1. [Feature Overview](#1-feature-overview)
2. [Tech Stack Used](#2-tech-stack-used)
3. [System Architecture](#3-system-architecture)
4. [How It Works — Step by Step Flow](#4-how-it-works--step-by-step-flow)
5. [Backend: API Endpoint](#5-backend-api-endpoint)
6. [Backend: Chat Controller (LLM Logic)](#6-backend-chat-controller-llm-logic)
7. [Frontend: ChatPage UI](#7-frontend-chatpage-ui)
8. [Security: JWT Authentication](#8-security-jwt-authentication)
9. [Conversation History (Multi-turn Chat)](#9-conversation-history-multi-turn-chat)
10. [Mock/Fallback Mode](#10-mockfallback-mode)
11. [Key Design Decisions](#11-key-design-decisions)
12. [Interview Q&A — Ready Answers](#12-interview-qa--ready-answers)

---

## 1. Feature Overview

**AyurBot** is an AI-powered Ayurvedic wellness chatbot embedded inside the AyurPulse web application. It allows logged-in users to ask natural language questions about:

- Ayurvedic doshas (Vata, Pitta, Kapha)
- Herbs, skin care routines, and nutrition
- Wellness plans personalized for them
- General Ayurvedic lifestyle tips

**What makes it unique:**
- Powered by **Meta's LLaMA 3.1 8B Instant** model via the **Groq API** — extremely fast LLM inference
- Supports **multi-turn conversation** (remembers the full chat history)
- Secured behind **JWT authentication** — only logged-in users can access it
- Has a **graceful mock fallback** when no API key is configured (useful for local dev/testing)

---

## 2. Tech Stack Used

| Layer       | Technology                          | Purpose                              |
|-------------|-------------------------------------|--------------------------------------|
| **LLM**     | Meta LLaMA 3.1 8B Instant (via Groq)| Generating Ayurvedic answers         |
| **LLM SDK** | `langchain-groq`, `langchain`       | LLM invocation and message schema    |
| **Backend** | FastAPI (Python)                    | REST API server                      |
| **Auth**    | JWT (HS256) via `python-jose`       | Protect the chatbot endpoint         |
| **Frontend**| React (Vite), Axios                 | Chat UI and API communication        |
| **Styling** | Tailwind CSS                        | Responsive, beautiful chat bubbles   |
| **DB**      | MongoDB (Motor - async driver)      | User data, plans (not chat messages) |

---

## 3. System Architecture

```
User (Browser)
    │
    │  POST /api/v1/chat  { message, history[] }
    │  Authorization: Bearer <JWT>
    ▼
FastAPI Backend (chat.py — Router)
    │
    │  1. Validates JWT token → extracts user_id
    │  2. Calls handle_chat_message(message, user_id, history)
    ▼
chat_controller.py (LLM Logic)
    │
    │  3. Builds message list:
    │     [ SystemMessage ] + [ history turns ] + [ HumanMessage ]
    │
    │  4. Calls Groq API (LLaMA 3.1 8B Instant)
    │     via langchain's ainvoke() (async)
    ▼
Groq Cloud API  ────► LLaMA 3.1 8B Instant Model
    │
    │  5. Returns AI-generated answer
    ▼
FastAPI Response → { answer: "...", sources: [] }
    │
    ▼
React ChatPage (ChatPage.jsx)
    │
    │  6. Appends bot message to UI
    │  7. Scrolls to bottom smoothly
    └─► User reads the answer
```

---

## 4. How It Works — Step by Step Flow

### Step 1: User Types a Message
- User types a question in the input textarea on `ChatPage.jsx`
- They can also click **Suggested Questions** chips (e.g., "What foods should I avoid for Pitta dosha?")

### Step 2: Frontend Sends Request
```js
// From ChatPage.jsx
const response = await api.post('/chat', {
  message: text,
  history: messages.map((m) => ({ role: m.role, content: m.content })),
});
```
- The `api` axios instance auto-attaches the `Bearer <JWT>` token from `localStorage`
- Full conversation history is sent with every request for **context continuity**

### Step 3: Backend Validates JWT
- `Depends(get_current_user)` runs automatically on every request
- If the token is missing, invalid, or expired → **401 Unauthorized** returned
- On success → `user_id` is extracted from the token payload

### Step 4: Controller Builds LLM Messages
```python
messages = [SystemMessage(content=GENERAL_SYSTEM_PROMPT)]

for turn in history:
    if turn["role"] == "user":
        messages.append(HumanMessage(content=turn["content"]))
    elif turn["role"] == "bot":
        messages.append(AIMessage(content=turn["content"]))

messages.append(HumanMessage(content=user_message))
```
- The **system prompt** defines AyurBot's personality and constraints
- Previous turns are **replayed** so the LLM understands full context
- The new question is appended last

### Step 5: LLM is Invoked Asynchronously
```python
response = await llm.ainvoke(messages)
return { "answer": response.content, "sources": [] }
```
- Uses `ainvoke()` (async) — non-blocking, works perfectly with FastAPI's async architecture
- Temperature is set to `0.2` → **more factual, less hallucination**
- Max tokens: `1024` — enough for a thorough Ayurvedic explanation

### Step 6: Response Displayed in UI
- Bot message bubble appears on the left side with smooth animation
- A "Thinking…" spinner is shown while waiting for the response
- If sources are present, they appear as reference pills below the message

---

## 5. Backend: API Endpoint

**File:** `app/routes/chat.py`

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
  ]
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
- `message`: minimum 1 character, maximum 1000 characters (enforced by Pydantic)
- `history`: optional list of `{role, content}` dictionaries (defaults to empty)

**Error Handling:**
- `401 Unauthorized` → JWT missing or expired
- `422 Unprocessable Entity` → validation error (e.g., empty message)
- `500 Internal Server Error` → LLM error, wrapped with a descriptive message

---

## 6. Backend: Chat Controller (LLM Logic)

**File:** `app/controllers/chat_controller.py`

### System Prompt Engineering
```python
GENERAL_SYSTEM_PROMPT = """You are AyurBot, a warm, friendly, and knowledgeable 
Ayurvedic wellness assistant for AyurPulse.
Answer the user's question about Ayurveda, health, herbs, nutrition, recipes, 
wellness, or general life tips based on your comprehensive knowledge of Ayurveda.
Keep your response clear, helpful, well-structured, and easy to read.
Avoid sounding dry or overly clinical...
Do not refer to technical concepts like 'RAG', 'retrieval', or 'database'...
Do not start your response with greetings like 'Namaste' or 'Hello'."""
```

**Why this prompt works:**
- Sets a **warm, friendly persona** (not a cold API)
- Instructs to **avoid technical jargon** (no mention of RAG, databases)
- Prevents unnecessary greetings — user gets answers faster
- Reminds users to consult practitioners for medical advice (legal safety)

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

---

## 7. Frontend: ChatPage UI

**File:** `frontend/src/pages/ChatPage.jsx`

### Key UI Features

| Feature | Implementation |
|---------|---------------|
| **Suggested Questions** | 6 clickable chips shown on empty state |
| **User bubble** | Right-aligned, emerald gradient background |
| **Bot bubble** | Left-aligned, white card with shadow |
| **Loading indicator** | Animated spinner with "Thinking…" text |
| **Auto-scroll** | `useRef` + `scrollIntoView({ behavior: 'smooth' })` |
| **Auto-focus input** | `inputRef.current?.focus()` on mount |
| **Enter to send** | `onKeyDown` handler (Shift+Enter = new line) |
| **Online badge** | Pulsing green indicator in header |
| **Source pills** | References shown below bot messages (when available) |

### State Management
```js
const [messages, setMessages] = useState([]);    // All chat messages
const [inputValue, setInputValue] = useState(''); // Current input text
const [isLoading, setIsLoading] = useState(false); // Loading state
```

### Error Handling in UI
```js
catch (err) {
  const errMsg = err?.response?.data?.detail || 'Something went wrong. Please try again.';
  // Displays the error as a bot message with ⚠️ prefix
}
```
- Errors are shown **inline as bot messages** — no jarring alert popups

---

## 8. Security: JWT Authentication

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

---

## 9. Conversation History (Multi-turn Chat)

**The chatbot supports full multi-turn conversations.** This means AyurBot remembers what was said earlier in the session.

**How it works:**
- The React frontend maintains a `messages` array in state
- On every new message send, the **entire history** is sent to the backend
- The backend replays all previous turns as `HumanMessage` / `AIMessage` objects before the new question
- The LLM sees the full context and can reference previous answers

**Example conversation:**
```
User: "Tell me about Pitta dosha"
Bot:  "Pitta dosha is associated with fire and water elements..."

User: "What foods should I avoid for it?"  ← refers to "it" (Pitta)
Bot:  "For Pitta dosha specifically, you should avoid..."  ← correctly understands context
```

**Note:** History is stored only in **frontend React state** (not in MongoDB), so it resets on page refresh — keeping the architecture simple and stateless.

---

## 10. Mock/Fallback Mode

If no valid Groq API key is configured, the chatbot automatically enters **Mock Mode**:

```python
def _is_dummy_api_key() -> bool:
    key = settings.GROQ_API_KEY or ""
    dummy_prefixes = ["gsk_dummy", "your_key", "change-this", "test_key", "placeholder"]
    return any(key.lower().startswith(p) for p in dummy_prefixes)
```

In mock mode, it returns:
```
[MOCK MODE — Set a real GROQ_API_KEY to get AI-generated answers]

Based on my general knowledge of Ayurveda, here is a mock response
for your question: "What is Pitta dosha?"
```

**Why this is useful:**
- Developers can run the full app locally without needing a real API key
- The frontend and backend integration can be tested without LLM costs
- Prevents crashes — the app always responds gracefully

---

## 11. Key Design Decisions

### 1. Why Groq + LLaMA instead of OpenAI?
- **Groq** offers extremely low latency inference (often sub-second response times)
- **LLaMA 3.1 8B Instant** is free-tier friendly and more than capable for Q&A tasks
- Open-source model = more control and no dependency on a closed ecosystem

### 2. Why `@lru_cache` on the LLM client?
- Creating a `ChatGroq` object on every request would be wasteful
- `lru_cache(maxsize=1)` ensures a **singleton** — created once, reused forever
- This is a standard Python performance optimization for expensive object initialization

### 3. Why temperature = 0.2?
- Ayurvedic advice should be **accurate and consistent**, not creative
- Low temperature = deterministic, factual answers
- Higher temperature would cause the bot to "hallucinate" herbs or dosages

### 4. Why is history sent from the frontend, not stored in DB?
- **Simpler architecture** — no need for a `chat_sessions` MongoDB collection
- Each browser session is independent
- Keeps the backend stateless and scalable
- Trade-off: history is lost on page refresh (acceptable for a wellness chatbot)

### 5. Why async (`ainvoke`) instead of sync?
- FastAPI is an async framework — blocking calls would freeze the event loop
- `ainvoke()` is non-blocking, allowing the server to handle other requests while waiting for Groq

---

## 12. Interview Q&A — Ready Answers

**Q: What is AyurBot and what does it do?**

> AyurBot is an AI-powered Ayurvedic wellness chatbot in AyurPulse. Users can ask it questions about Ayurveda — doshas, herbs, skin routines, nutrition, and their personalized wellness plans. It's powered by Meta's LLaMA 3.1 model running on Groq's ultra-fast inference platform.

---

**Q: How does the chatbot maintain conversation context?**

> The frontend (React) stores all messages in state. Every time the user sends a new message, the entire conversation history is sent to the backend as a JSON array. The backend then reconstructs the full message chain — system prompt, all previous turns, and the new question — before invoking the LLM. This gives the model full context to understand follow-up questions.

---

**Q: How is the chatbot secured?**

> The `/api/v1/chat` endpoint is protected by JWT authentication. A user must be logged in to use it. The React frontend attaches the Bearer token to every request via an Axios interceptor. If the token expires, the interceptor automatically refreshes it using the refresh token, then retries the original request. If refresh also fails, the user is redirected to login.

---

**Q: What LLM did you use and why?**

> I used Meta's LLaMA 3.1 8B Instant model via the Groq API. I chose Groq because it offers industry-leading low-latency inference — responses come back in under a second usually. The 8B model is efficient yet powerful enough for Ayurvedic Q&A. I also set the temperature to 0.2 to keep responses accurate and factual rather than creative.

---

**Q: How did you design the system prompt?**

> The system prompt defines AyurBot's persona as a warm, friendly Ayurvedic assistant. Key decisions: I told it to avoid mentioning technical terms like 'RAG' or 'database', skip generic greetings and get straight to answers, and remind users to consult a practitioner for medical advice. Good prompt engineering directly impacts the quality and professionalism of responses.

---

**Q: What happens if the API key is not set?**

> The controller has a `_is_dummy_api_key()` check that detects placeholder or missing keys. In that case it returns a clearly labeled mock response, so the app never crashes. This was important for local development — the team could run the full stack without needing a real API key.

---

**Q: Why did you use `@lru_cache` on `_get_llm()`?**

> Creating the `ChatGroq` client involves network initialization and config loading. Doing this on every API call would be wasteful. `@lru_cache(maxsize=1)` turns it into a singleton — it's created once on the first request and reused for all subsequent requests. This is a standard Python optimization pattern for expensive resources.

---

**Q: Is the chat history stored in the database?**

> No, and that was a deliberate design decision. Storing chat history in MongoDB would require a `chat_sessions` collection, session IDs, and more complex queries. Instead, I kept it simple — history lives in React state and is sent with every request. The trade-off is that history resets on page refresh, which is acceptable for a wellness assistant use case. The architecture stays stateless and scalable.

---

**Q: How does the frontend handle errors from the chatbot?**

> Instead of showing alert popups (which are jarring), errors are displayed inline as bot messages with a ⚠️ prefix. The error message is extracted from the backend's `detail` field if available, or falls back to a generic "Something went wrong" message. This keeps the user experience smooth and consistent.

---

**Q: What is the API contract for the chatbot endpoint?**

> It's a POST request to `/api/v1/chat` with a JSON body containing `message` (string, 1-1000 chars) and `history` (optional array of `{role, content}` objects). The response is `{answer: string, sources: []}`. Pydantic models enforce the input validation automatically, and FastAPI generates the OpenAPI docs for it.

---

## 📁 Relevant Files — Quick Reference

| File | Purpose |
|------|---------|
| [`app/routes/chat.py`](app/routes/chat.py) | FastAPI router — endpoint definition, request/response models |
| [`app/controllers/chat_controller.py`](app/controllers/chat_controller.py) | LLM logic — system prompt, history building, Groq invocation |
| [`frontend/src/pages/ChatPage.jsx`](frontend/src/pages/ChatPage.jsx) | React chat UI — messages, input, loading state, suggested questions |
| [`frontend/src/services/api.js`](frontend/src/services/api.js) | Axios instance — auto-attaches JWT, handles 401/token refresh |
| [`app/config/settings.py`](app/config/settings.py) | App configuration — GROQ_API_KEY, JWT settings, model params |
| [`app/main.py`](app/main.py) | App entry point — registers the chat router |

---

*Generated for AyurPulse v1.0.0 — AyurBot Chatbot Feature*
