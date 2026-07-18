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

## Step 2: Install Docker

```bash
apt-get update && apt-get install -y curl git
curl -fsSL https://get.docker.com | bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

## Step 3: Clone the Repository

```bash
cd /opt
git clone https://github.com/alpesh15gb/ApexStudio.git apex-studio
cd apex-studio
```

## Step 4: Configure Environment

```bash
# Copy the .env.example and fill in your VPS IP
cp .env.example .env

# Get your VPS IP automatically
VPS_IP=$(curl -4 -fsSL ifconfig.me)

# Update .env with your IP
sed -i "s/localhost/$VPS_IP/g" .env
sed -i "s/APP_DEBUG=true/APP_DEBUG=false/g" .env

# Generate secure random keys
sed -i "s/change-this-to-a-random-secret-key/$(openssl rand -hex 32)/g" .env
sed -i "s/change-this-to-a-jwt-secret-key/$(openssl rand -hex 32)/g" .env
```

## Step 5: Launch Everything

```bash
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
