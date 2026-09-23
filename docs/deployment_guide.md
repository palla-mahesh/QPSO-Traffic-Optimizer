# Production Deployment Guide: Quantum Traffic Route Optimization (Q-TRO)

**Problem Statement ID**: 26137  
**Organization**: Egreen Quanta  
**Vertical**: Quantum Technology Vertical (SIH 2026)  

---

## 1. Quick Start: Single-Command Local/Server Launch

The easiest way to run in production on any Linux/macOS server:

```bash
chmod +x start.sh
./start.sh
```

This will automatically configure `.venv`, install requirements, and start the FastAPI production server on `http://0.0.0.0:8000`.

---

## 2. Containerized Deployment with Docker

### Option A: Using Docker Directly
```bash
# Build the optimized multi-stage Docker image
docker build -t qtro-platform:latest .

# Run container exposing port 8000
docker run -d --name qtro_app -p 8000:8000 --restart unless-stopped qtro-platform:latest

# Check health
curl http://localhost:8000/api/health
```

### Option B: Using Docker Compose
```bash
# Start in detached background mode
docker compose up -d

# View real-time logs
docker compose logs -f

# Stop container
docker compose down
```

---

## 3. Serverless Deployment to Google Cloud Run

Deploy directly to Google Cloud Run with automatic SSL and autoscaling:

```bash
# 1. Authenticate with GCP
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID

# 2. Build and deploy directly from source
gcloud run deploy qtro-platform \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10
```

---

## 4. 1-Click Deployment to Render / Railway

### Deploying to Render
1. Push this repository to GitHub or GitLab.
2. In Render Dashboard, click **New +** $\to$ **Blueprint**.
3. Select your repository. Render will automatically detect [`render.yaml`](file:///Users/psryogeshwar/Downloads/MASHI/render.yaml) and provision the web service.

### Deploying to Railway / Heroku
The included [`Procfile`](file:///Users/psryogeshwar/Downloads/MASHI/Procfile) automatically configures the web dyno:
```
web: uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
```

---

## 5. Bare-Metal Linux VPS Deployment (Ubuntu + Systemd + Nginx)

### 1. Create Systemd Service
Create `/etc/systemd/system/qtro.service`:
```ini
[Unit]
Description=Q-TRO Quantum Traffic Route Optimization
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/MASHI
ExecStart=/home/ubuntu/MASHI/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable qtro
sudo systemctl start qtro
```

### 2. Configure Nginx Reverse Proxy with WebSocket Support
Create `/etc/nginx/sites-available/qtro`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/qtro /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```
