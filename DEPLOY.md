# Apex Studio — VPS Deployment Guide

Deploy Apex Studio on your Ubuntu VPS with **system-level Nginx**.

## Prerequisites

- Ubuntu 22.04 or 24.04 VPS
- SSH access (root or sudo user)
- Ports 22 (SSH) and 80 (HTTP) open
- Docker & Docker Compose installed (Step 1 handles this)

---

## Step 1: Install Docker (if not installed)

```bash
apt-get update && apt-get install -y curl git
curl -fsSL https://get.docker.com | bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

## Step 2: Clone the Repository

```bash
cd /opt
git clone https://github.com/alpesh15gb/ApexStudio.git apex-studio
cd apex-studio
```

## Step 3: Configure Environment

```bash
cp .env.example .env
VPS_IP=$(curl -4 -fsSL ifconfig.me)
sed -i "s/localhost/$VPS_IP/g" .env
sed -i "s/APP_DEBUG=true/APP_DEBUG=false/g" .env
sed -i "s/change-this-to-a-random-secret-key/$(openssl rand -hex 32)/g" .env
sed -i "s/change-this-to-a-jwt-secret-key/$(openssl rand -hex 32)/g" .env
```

## Step 4: Launch Docker Services

```bash
cd /opt/apex-studio
docker-compose -f infra/docker-compose.vps.yml up -d --build
```

Services will start on local-only ports:
- **Backend API:** `127.0.0.1:8000`
- **Frontend:** `127.0.0.1:8080`

## Step 5: Configure System Nginx

Create the Nginx site config:

```bash
cp infra/nginx/system-nginx.conf /etc/nginx/sites-available/apex-studio
ln -s /etc/nginx/sites-available/apex-studio /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

## Step 6: Verify Deployment

```bash
# Check docker services
docker ps

# Test backend API
curl http://localhost:8000/api/v1/health

# Test via Nginx
curl http://localhost/api/v1/health

# Your public IP
echo "http://$(curl -4 ifconfig.me)"
```

## Step 7: Login

Open `http://your-vps-ip` in your browser.

| Credential | Value |
|---|---|
| URL | `http://your-vps-ip` |
| Email | `admin@apexstudio.com` |
| Password | `admin123` |

---

## Management Commands

```bash
# View all logs
docker-compose -f infra/docker-compose.vps.yml logs -f

# Tail backend logs
docker-compose -f infra/docker-compose.vps.yml logs -f backend

# Restart a service
docker-compose -f infra/docker-compose.vps.yml restart backend

# Full restart
docker-compose -f infra/docker-compose.vps.yml down
docker-compose -f infra/docker-compose.vps.yml up -d

# Update after pulling new code
git pull
docker-compose -f infra/docker-compose.vps.yml up -d --build --force-recreate
```

## Firewall

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS (future)
ufw --force enable
```

## Adding a Domain Later

Once you have a domain (e.g., `apex.yourdomain.com`):

1. Point the domain's A record to your VPS IP
2. Install SSL:
```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d apex.yourdomain.com
```
