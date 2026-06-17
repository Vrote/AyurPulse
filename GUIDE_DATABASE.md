# 🗄️ AyurPulse Database Technical Guide: Interview Perspective

This document serves as the comprehensive source of truth for the **AyurPulse** database architecture. It details why MongoDB was selected, how asynchronous connectivity is configured, collection schemas, indexing strategies, and database-focused interview preparation.

---

## 🏛️ 1. NoSQL MongoDB Choice & Connectivity Rationale

### 1.1. Why MongoDB over PostgreSQL? (Interview Gold)
*   **Hierarchical Document Splicing:** Our core data model is the 7-day health plan (`user_plans`). Each plan is highly hierarchical, containing a nested `weekly_summary`, `patient_metadata` sub-documents, and an array of 7 independent `DayPlan` objects (each having nested `morning` and `evening` RoutineSteps, and `diet` plans). 
    *   In a relational database (SQL), this would require separating the data into **5 tables** (`plans`, `days`, `morning_routines`, `evening_routines`, `diets`) and executing complex **4-way joins** to retrieve a single patient's schedule. This degrades database read speeds and increases join processing overhead.
    *   In MongoDB, the entire plan is stored as a single, self-contained **nested JSON document**, allowing the system to retrieve the complete plan in a single, sub-millisecond query.
*   **Schema Flexibility:** The dynamic rule engine modifies templates based on varying patient characteristics. NoSQL allows us to expand patient attributes (e.g. adding new lifestyle flags or custom doctor annotations) without locking tables or executing risky schema migrations.

### 1.2. Asynchronous Motor Driver Connectivity
Standard Python database drivers (like `pymongo` or `psycopg2`) are blocking: when an API thread queries the database, it freezes, waiting for the database server to reply. In an async web framework like FastAPI, this blocks the entire event loop, eliminating concurrency.
To prevent this, AyurPulse uses **`motor`**, an asynchronous driver for MongoDB. Motor leverages Python's `asyncio` to execute non-blocking database operations, allowing FastAPI's event loop to process other incoming API requests while waiting for the database queries to complete.

```python
# Technical snapshot of connection management in app/db/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient

async def connect_db():
    global _client, _db
    _client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000  # Fail fast (5-second timeout)
    )
    # Ping database to verify connection immediately on boot
    await _client.admin.command("ping")
    _db = _client[settings.DATABASE_NAME]
```

---

## 🧬 2. Database Collections & Schema Definitions

```
                     ┌───────────────────────┐
                     │         users         │
                     └───────────┬───────────┘
                                 │ 1:1
                     ┌───────────▼───────────┐
                     │        doctors        │
                     └───────────┬───────────┘
                                 │ 1:N
                     ┌───────────▼───────────┐
                     │      user_plans       │
                     └───────────▲───────────┘
                                 │ 1:1
                     ┌───────────┴───────────┐
                     │   skin_predictions    │
                     └───────────────────────┘
```

### 2.1. `users` Collection
Stores authentication credentials for patients and global references for doctor logins.
*   **Key Fields:** `full_name` (string), `email` (string, stored in lowercase), `password` (bcrypt hash string), `role` (enum string: `"user"` | `"doctor"`), `is_active` (boolean), `created_at` (datetime), `last_login` (datetime).

### 2.2. `doctors` Collection
Stores professional credentials decoupled from the main `users` collection to keep schemas normalized and queryable.
*   **Key Fields:** `specialization` (string, e.g. `"Ayurvedic Dermatology"`), `experience_years` (integer), `clinic_address` (string), `is_verified` (boolean, controlled by administrators).

### 2.3. `refresh_tokens` & `token_blacklist` Collections
Manages stateful verification for stateless JWTs.
*   **`refresh_tokens` Fields:** `user_id` (string), `token` (string, rotated access key), `created_at` (datetime).
*   **`token_blacklist` Fields:** `token` (string, deactivated token), `blacklisted_at` (datetime).

### 2.4. `skin_predictions` Collection
Logs computer vision scanning metadata, raw probabilities, and threshold evaluations.
*   **Key Fields:** `user_id` (foreign key pointing to users), `filename` (UUID file string in uploads/), `detected_conditions` (array of strings), `all_probabilities` (array of objects storing class and float confidence), `consult_doctor` (boolean).

### 2.5. `user_plans` Collection
Stores spliced 7-day nested plan schedules, quiz data, personalization parameters, and doctor vetting inputs.
*   **Key Fields:** `user_id` (foreign key), `prediction_id` (foreign key), `title` (string), `dosha_focus` (string), `required_specialty` (string), `patient_metadata` (nested sub-document storing quiz answers and customized traits), `days` (array of 7 DayPlan sub-documents), `is_doctor_vetted` (boolean), `doctor_notes` (string), `doctor_name` (string).

---

## ⚡ 3. Indexing Strategies & Database Optimization

Unindexed collections force MongoDB to perform a **collection scan (COLLSCAN)**, reading every document sequentially to find matches. This degrades performance as data grows. We implemented targeted indexing to optimize queries:

### 3.1. Unique Indexes
*   `users.email` & `doctors.email`: Enforces fast email-based credentials search and guarantees email uniqueness at the database level.
*   `refresh_tokens.token`: Ensures instant token verification during the silent refresh cycle.

### 3.2. Self-Cleaning Collections (TTL Indexing)
When a user logs out, their access token is added to the `token_blacklist` collection. Over time, this collection would grow infinitely, wasting storage space and slowing query times.
To prevent this, we configure a **TTL (Time-To-Live) Index** on the `blacklisted_at` field:
```python
await _db["token_blacklist"].create_index("blacklisted_at", expireAfterSeconds=86400)
```
MongoDB runs a background thread that automatically deletes any document once `blacklisted_at` is older than **86,400 seconds (24 hours)**. This keeps the collection lightweight and self-cleaning.

### 3.3. Compound Indexes
To load a patient's scan history or customized plan lists in their dashboard, the API executes:
`db.user_plans.find({"user_id": uid}).sort({"created_at": -1})`.
To optimize this, we created a **Compound Index** on `user_id` and `created_at`:
```python
await _db["user_plans"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
await _db["skin_predictions"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
```
This compound index pre-sorts matching documents in memory, reducing the database lookup time to sub-milliseconds.

---

## 💡 4. Interview Focus: Common Database Questions & Answers

#### Q1: Why did you decouple Doctors and Users into separate collections instead of storing all roles in one collection?
**A:** Storing them in a single collection would lead to a sparse schema containing many null/empty values (e.g. every patient document would have empty fields for `specialization`, `clinic_address`, `is_verified`). This wastes database memory and degrades index performance. Decoupling them keeps the `users` collection exceptionally small and fast for authentication, while allowing us to scale the `doctors` collection and build indexes specifically on specializations.

#### Q2: What is the benefit of using an Asynchronous DB driver like Motor?
**A:** Standard synchronous drivers (like `pymongo`) use blocking network calls. When the API queries the database, the executing thread is blocked until the database server replies. In an asynchronous framework like FastAPI, this blocks the entire event loop, preventing the server from handling other incoming requests concurrently. Motor uses non-blocking sockets and yields control back to the `asyncio` event loop during database operations, allowing FastAPI to handle other incoming API requests while waiting for the database query to return.

#### Q3: How do you prevent your database from filling up with expired blacklisted tokens?
**A:** We use a MongoDB **TTL (Time-To-Live) Index** on the `blacklisted_at` field of our `token_blacklist` collection. When a token is blacklisted during logout, we store the current datetime. MongoDB's background thread automatically purges documents older than 24 hours (86,400 seconds), keeping the collection lightweight and self-cleaning.

#### Q4: Why did you choose a hybrid relational model (referencing `user_id` but nesting day schedules) in your plan collection?
**A:** We used a hybrid approach of **Referencing** and **Embedding**:
*   **Referencing (`user_id`):** The relationship between users and plans is one-to-many. Since a user can have many plans and users are queried independently, we store them in separate collections and reference the `user_id` to keep the database normalized.
*   **Embedding (Day Schedules):** A 7-day plan is always read and written as a single unit. Embedded schemas avoid the need for costly multi-table joins, allowing us to fetch the complete plan in a single query.
