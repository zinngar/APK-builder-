# Trafficlites APK Builder 📦🤖

A powerful, streamlined Docker-based utility to manage, build, and distribute Android APKs for React Native and Expo applications. It provides a simple, beautiful dark-themed Web UI to ingest projects, execute compilation, stream real-time logs, and download final APK packages directly from your browser.

---

## ✨ Features

- **GitHub Ingestion:** Instantly pull or clone any public React Native / Expo repository directly from GitHub via the Web UI (with custom branch/tag/commit support).
- **Manual ZIP Upload:** Upload project source files as a `.zip` archive. The builder automatically extracts and cleans the files, automatically flattening any nested top-level folder wrappers (e.g. from GitHub zip downloads).
- **Interactive Build Suite:** One-click triggers for **Release** or **Debug** Android builds.
- **Real-Time Streaming Logs:** Watch build progress live (dependency install, prebuild generation, and Gradle compilation logs stream in real-time).
- **APKs Management:** Downloads, timestamps, and sizes are listed in a clean table immediately upon completion.
- **High-Performance Caching:** Persists Gradle and NPM dependencies in Docker volumes, ensuring subsequent builds are lightning-fast.

---

## 🚀 Quick Start / Installation

Setting up the APK Builder is incredibly easy.

### 1. Prerequisites
Make sure you have [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your host system.

### 2. Clone this Builder Repository
```bash
git clone https://github.com/zinngar/APK-builder-.git
cd APK-builder-
```

### 3. Launch the Services
Start the builder and Web UI using Docker Compose:
```bash
docker compose up -d --build
```

### 4. Access the Web UI
Open your browser and navigate to:
```
http://localhost:6050
```

---

## 🛠️ Usage Guide

### A. Set Up Your React Native / Expo Project
The builder supports two convenient ways to ingest project source files:

1. **Pull from GitHub:**
   - Under **Source Code Setup**, enter your repository's Git URL (e.g. `https://github.com/zinngar/7Eleven-app`).
   - Specify the branch name (e.g., `master` or `main`), then click **Pull Repository**.
   - The log box will show real-time cloning status.

2. **Upload Project ZIP:**
   - Choose a `.zip` file containing your React Native/Expo project.
   - Click **Upload & Extract**. The backend extracts it directly into the shared workspace volume and prepares it for building.

### B. Trigger a Build
- Click **🚀 Build Release APK** to assemble a production-ready package.
- Click **🛠️ Build Debug APK** to assemble a development/testing package.
- The build status badge will change to `running (release)` or `running (debug)`.
- Watch the **Build Operations Log** window below to view dependency installations, Expo prebuild steps, and Gradle tasks in real-time.

### C. Download the APK
- Once the build succeeds, the status badge will update to `success`.
- The **📦 Available APKs** table at the bottom of the page will list your freshly compiled `.apk` file, showing its size and build timestamp.
- Click **⬇️ Download** to save the APK directly to your device!

---

## 📂 Project Directory Structure

```
.
├── app.py                  # Flask web controller (handles routes, Git pulls, and uploads)
├── Dockerfile              # Web UI Docker build script
├── docker-compose.yml      # Orchestrates the web UI and build containers
├── requirements.txt        # Python backend dependencies
├── build.sh                # Main compilation runner (runs npm install, Expo prebuild, Gradle build)
├── templates/
│   └── index.html          # Beautiful modern dark-theme user interface
└── project_src/            # Shared codebase workspace folder (automatically created)
```

---

## ⚙️ How It Works (Under the Hood)

1. **Shared Workspace:** The `webui` and `trafficlites-build` services share a local host-backed folder called `./project_src`.
2. **Docker Control:** The Web UI container has access to `/var/run/docker.sock`, letting Flask safely launch the build container via `docker compose run`.
3. **Build Runner (`build.sh`):**
   - Automatically detects lockfiles (`yarn.lock` vs `package-lock.json`) and runs `yarn install` or `npm install`.
   - Runs `npx expo prebuild` if the native `android` directory is missing.
   - Grants permissions and launches Gradle wrapper (`./gradlew assembleRelease` or `./gradlew assembleDebug`).
   - Copies the compiled APK to the mapped `./output` directory, which instantly makes it downloadable in the browser.
