# Dockerization Guide: AyurPulse Full-Stack Deployment

This guide explains the step-by-step process used to containerize the AyurPulse application. Use this for your interview preparation to explain *how* and *why* we chose this architecture.

## 1. System Architecture
The application is split into three main containers orchestrated by **Docker Compose**:
- **MongoDB:** Database for persistence.
- **FastAPI (Backend):** Python-based API for medical logic and AI.
- **Nginx (Frontend):** High-performance server for the React/Vite application.

---

## 2. The Backend Dockerfile (`Ayurpulse/Dockerfile`)
We use a **lightweight Python base** to keep the image size small.

### Key Features:
- **Base Image:** `python:3.11-slim` (Reduced attack surface and faster downloads).
- **Layer Optimization:** We copy `requirements.txt` and run `pip install` *before* copying the rest of the code. This leverages **Docker caching**—if you only change the code, Docker won't re-install dependencies.
- **Process Management:** Running `python run.py` directly for simplicity in development.

---

## 3. The Frontend Dockerfile (`frontend/Dockerfile`)
We use a **Multi-Stage Build**. This is a critical interview concept!

### Stage 1: Build (Node.js)
- Installs dependencies and runs `npm run build`.
- Generates a static production bundle in the `/dist` folder.

### Stage 2: Serve (Nginx)
- Uses the lightweight `nginx:stable-alpine` image.
- **Important:** We only copy the `/dist` folder from Stage 1. We **discard** the Node.js environment and `node_modules`. This results in an extremely small and efficient production image (about 25MB).

---

## 4. Orchestration (`docker-compose.yml`)
Docker Compose manages the lifecycle and networking of the three containers.

### Important Concepts:
- **Networking:** Containers use a shared bridge network (`ayurpulse-network`). This allows the backend to find MongoDB using the hostname `mongodb` instead of an IP address.
- **Volumes:** `mongodb_data:/data/db` ensures that if a container is deleted, the data persists on your host machine.
- **Environment Variables:** We override the `MONGODB_URL` to point to the `mongodb` service name.

---

## 5. Critical Commands
| Command | Purpose |
| :--- | :--- |
| `docker-compose up --build` | Build images and start all services. |
| `docker-compose down` | Stop and remove all containers and networks. |
| `docker-compose logs -f` | View real-time logs from all services. |
| `docker exec -it <name> sh` | Open a shell inside a running container. |

---

## 6. Interview "Pro-Tips"
**Q: Why use `.dockerignore`?**  
A: It prevents large or sensitive files (like `venv/`, `node_modules/`, or `.env`) from being uploaded to the Docker daemon. This makes the build faster and more secure.

**Q: What is the benefit of a multi-stage build?**  
A: It separates the build environment from the runtime environment. This produces a much smaller final image and improves security by excluding build tools.

**Q: How do you handle environment variables?**  
A: In development, we use `.env` files. In Docker, we pass them via the `environment:` section in `docker-compose.yml` to allow for easy overrides during deployment.
