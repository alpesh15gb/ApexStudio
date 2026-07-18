# Apex Studio — VPS Deployment Guide

Deploy Apex Studio on your Ubuntu VPS (no domain required — works over IP).

## Prerequisites

- Ubuntu 22.04 or 24.04 VPS
- SSH access (root or sudo user)
- Ports 22 (SSH) and 80 (HTTP) open

## Step 1: SSH into Your VPS

```bash
ssh root@your-vps-ip
```

## Step 2: Run the Deployment Script

```bash
# Install dependencies & Docker
apt-get update && apt-get install -y curl git
curl -fsSL https://get.docker.com | bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

## Step 3: Copy Project Files to VPS

**On your local machine** (where Apex Studio code is), run:

```bash
# Replace with your VPS IP
export VPS_IP=your-vps-ip

# Copy all files (excluding dev artifacts)
rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '.venv' \
      --exclude 'node_modules' --exclude 'frontend/build' \
      ./ root@$VPS_IP:/opt/apex-studio/
```

## Step 4: Configure & Launch on VPS

**Back on the VPS** (or continue in SSH):

```bash
cd /opt/apex-studio

# Create environment file
cat > .env << 'EOF'
APP_ENV=production
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_SECRET_KEY=$(openssl rand -hex 32)
APP_API_URL=http://YOUR_VPS_IP
APP_FRONTEND_URL=http://YOUR_VPS_IP

DATABASE_URL=postgresql+asyncpg://apex:apex@postgres:5432/apex_studio
REDIS_URL=redis://redis:6379/0

JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

DOCKER_HOST=unix:///var/run/docker.sock
WORKSPACE_BASE_PATH=./workspaces

S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=apex-studio

OMNIROUTE_API_KEY=your-key-here
OMNIROUTE_DEFAULT_MODEL=claude-sonnet-5
EOF

# Replace IP placeholder
sed -i "s/YOUR_VPS_IP/$(curl -4 -fsSL ifconfig.me)/g" .env

# Launch everything
docker-compose -f infra/docker-compose.vps.yml up -d --build
```

## Step 5: Verify Deployment

```bash
# Check all services are running
docker-compose -f infra/docker-compose.vps.yml ps

# Check API health
curl http://localhost:8000/api/v1/health

# Check from outside
curl http://$(curl -4 ifconfig.me)/api/v1/health
```

## Step 6: Default Login

Open `http://your-vps-ip` in a browser.

| Field | Value |
|---|---|
| URL | `http://your-vps-ip` |
| Email | `admin@apexstudio.com` |
| Password | `admin123` |

## Management Commands

```bash
# View logs
docker-compose -f infra/docker-compose.vps.yml logs -f

# Tail specific service
docker-compose -f infra/docker-compose.vps.yml logs -f backend

# Restart
docker-compose -f infra/docker-compose.vps.yml restart

# Stop
docker-compose -f infra/docker-compose.vps.yml down

# Update (after pulling new code)
docker-compose -f infra/docker-compose.vps.yml up -d --build --force-recreate
```

## Firewall Setup

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp   # For future SSL
ufw --force enable
```

## Adding a Domain Later

Once you have a domain (e.g., `apex.yourdomain.com`):

1. Point the domain's A record to your VPS IP
2. Run the SSL setup:
```bash
docker-compose -f infra/docker-compose.prod.yml up -d certbot
```
3. Switch to the production compose:
```bash
docker-compose -f infra/docker-compose.vps.yml down
docker-compose -f infra/docker-compose.prod.yml up -d
```
