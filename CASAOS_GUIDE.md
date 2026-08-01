# CasaOS Integration Guide

This APK Builder integrates seamlessly with CasaOS using Docker Compose. Follow these steps to install and use it.

## Installation Method 1: Direct CLI Installation

### 1. SSH into your CasaOS system
```bash
ssh root@<casaos-ip>
```

### 2. Clone the APK Builder repository
```bash
cd /root
git clone https://github.com/zinngar/APK-builder-.git
cd APK-builder-
```

### 3. Launch with CasaOS
Use the CasaOS AppFile to deploy:
```bash
docker-compose -f casaos-appfile.yml up -d --build
```

### 4. Access the Web UI
- Open your browser and navigate to `http://<casaos-ip>:6050`
- The APK Builder Web UI will be ready to use

---

## Installation Method 2: CasaOS App Store

If CasaOS has indexed this app or you've added a custom app store:

1. Open **CasaOS Dashboard** → **App Store**
2. Search for **APK Builder**
3. Click **Install** and select your desired port (default: 6050)
4. Click **Deploy**
5. Access via the app card in your CasaOS dashboard

---

## Configuration

### Custom Port
Set the `WEBUI_PORT` environment variable when deploying:

```bash
WEBUI_PORT=8080 docker-compose -f casaos-appfile.yml up -d --build
```

### Persistent Storage
- **Output APKs:** Stored in the `apk-builder-output` volume (persisted)
- **Project Source:** Stored in the `apk-builder-project-src` volume (persisted)
- **Build Cache:** Gradle and NPM caches are stored in separate volumes for speed

All volumes are managed by Docker and stored on your CasaOS host.

---

## Usage

### Building an APK

1. **Add Project Source:**
   - **From GitHub:** Paste a repository URL (e.g., `https://github.com/your-org/react-native-app`) and select a branch
   - **From ZIP:** Upload a ZIP file containing your React Native/Expo project

2. **Trigger Build:**
   - Click **🚀 Build Release APK** for production builds
   - Click **🛠️ Build Debug APK** for development/testing

3. **Monitor Progress:**
   - Watch real-time build logs in the Web UI
   - Once complete, the status badge will show `success`

4. **Download APK:**
   - Scroll to **📦 Available APKs**
   - Click **⬇️ Download** next to your APK

---

## Stopping and Removing

### Stop the services
```bash
docker-compose -f casaos-appfile.yml stop
```

### Remove the services (keeps volumes)
```bash
docker-compose -f casaos-appfile.yml down
```

### Remove everything including volumes (destructive)
```bash
docker-compose -f casaos-appfile.yml down -v
```

---

## Troubleshooting

### Services won't start
Check logs:
```bash
docker-compose -f casaos-appfile.yml logs -f
```

### Web UI unreachable
- Verify firewall rules allow port 6050 (or your custom port)
- Check that the webui service is running: `docker ps | grep apk-builder`

### Build fails
- Check build logs in the Web UI
- Ensure your project is a valid React Native/Expo project
- Verify `build.sh` has execute permissions: `chmod +x build.sh`

### Volumes consuming too much space
Clear caches:
```bash
docker volume rm apk-builder-gradle-cache apk-builder-npm-cache
```
(Rebuilds will be slower the next time, but caches will be rebuilt automatically)

---

## System Requirements

- **Docker** and **Docker Compose** installed on CasaOS
- **4GB+ RAM** recommended (builds are memory-intensive)
- **10GB+ free disk space** recommended (for caches and builds)
- **Network access** to GitHub (if pulling from repositories)

---

## Support

For issues or questions:
- Check the main [APK Builder README](README.md)
- Visit the [GitHub repository](https://github.com/zinngar/APK-builder-)
