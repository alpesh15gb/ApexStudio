#!/bin/bash
set -e

# ==============================================================
# Apex Studio — VPS Deployment Script
# ==============================================================
# Run this on your Ubuntu 22.04/24.04 VPS.
# Usage: curl -fsSL https://raw.githubusercontent.com/... | bash
#    or: chmod +x deploy.sh && ./deploy.sh
# ==============================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════════════╗"
echo "  ║         Apex Studio — VPS Deployment          ║"
echo "  ╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

# Configuration
REPO_URL="${REPO_URL:-https://github.com/your-org/apex-studio.git}"
BRANCH="${BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-/opt/apex-studio}"
VPS_IP="$(curl -4 -fsSL ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP')"

# -------------------------------
# Step 1: System Updates
# -------------------------------
echo -e "${YELLOW}[1/7] Updating system packages...${NC}"
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq curl git ufw

# -------------------------------
# Step 2: Install Docker
# -------------------------------
echo -e "${YELLOW}[2/7] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}Docker installed: $(docker --version)${NC}"
else
    echo -e "${GREEN}Docker already installed: $(docker --version)${NC}"
fi

# -------------------------------
# Step 3: Install Docker Compose
# -------------------------------
echo -e "${YELLOW}[3/7] Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose installed${NC}"
else
    echo -e "${GREEN}Docker Compose already installed${NC}"
fi

# -------------------------------
# Step 4: Clone / Update Project
# -------------------------------
echo -e "${YELLOW}[4/7] Setting up project...${NC}"
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
fi

# For now, we'll create the project directly from the local files
# In production, this would clone from git:
# git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"

echo -e "${CYAN}⚠  Project files need to be copied to ${INSTALL_DIR}${NC}"
echo -e "${CYAN}   Run this on your local machine to copy files:${NC}"
echo ""
echo "   rsync -avz --exclude 'node_modules' --exclude '.git' --exclude '.venv' \\"
echo "         ./ $VPS_IP:$INSTALL_DIR"
echo ""

# -------------------------------
# Step 5: Configure Firewall
# -------------------------------
echo -e "${YELLOW}[5/7] Configuring firewall...${NC}"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS (for future SSL)
ufw --force enable
echo -e "${GREEN}Firewall configured (ports 22, 80, 443 open)${NC}"

# -------------------------------
# Step 6: Environment Setup
# -------------------------------
echo -e "${YELLOW}[6/7] Setting up environment...${NC}"
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cat > "$INSTALL_DIR/.env" << 'ENVEOF'
# Apex Studio — Production Environment
APP_ENV=production
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_SECRET_KEY=$(openssl rand -hex 32)
APP_API_URL=http://VPS_IP
APP_FRONTEND_URL=http://VPS_IP

# Database
POSTGRES_USER=apex
POSTGRES_PASSWORD=apex
POSTGRES_DB=apex_studio
DATABASE_URL=postgresql+asyncpg://apex:apex@postgres:5432/apex_studio
DATABASE_SYNC_URL=postgresql://apex:apex@postgres:5432/apex_studio

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Docker
DOCKER_HOST=unix:///var/run/docker.sock
DOCKER_NETWORK_NAME=apex_network
WORKSPACE_BASE_PATH=./workspaces

# S3 (MinIO)
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=apex-studio
S3_REGION=us-east-1
S3_SECURE=false

# AI / Omniroute
OMNIROUTE_API_KEY=
OMNIROUTE_BASE_URL=https://api.omniroute.ai/v1
OMNIROUTE_DEFAULT_MODEL=claude-sonnet-5
OMNIROUTE_FALLBACK_MODEL=gpt-4o

# Stripe (Billing)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
ENVEOF

    # Replace placeholder IP
    sed -i "s/VPS_IP/$VPS_IP/g" "$INSTALL_DIR/.env"
    echo -e "${GREEN}.env file created${NC}"
else
    echo -e "${GREEN}.env file already exists${NC}"
fi

# -------------------------------
# Step 7: Launch Stack
# -------------------------------
echo -e "${YELLOW}[7/7] Launching Apex Studio stack...${NC}"
cd "$INSTALL_DIR"

# Pull latest images
docker-compose -f infra/docker-compose.prod.yml pull 2>/dev/null || true

# Start services
docker-compose -f infra/docker-compose.prod.yml up -d

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       Apex Studio is now LIVE!                ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}🌐  Platform:${NC}  http://$VPS_IP"
echo -e "  ${CYAN}📡  API:${NC}      http://$VPS_IP/api/v1/health"
echo -e "  ${CYAN}📋  Docs:${NC}     http://$VPS_IP/docs"
echo ""
echo -e "  ${YELLOW}Default login:${NC}"
echo -e "    Email:    admin@apexstudio.com"
echo -e "    Password: admin123"
echo ""
echo -e "  ${YELLOW}Management:${NC}"
echo -e "    View logs:    docker-compose -f infra/docker-compose.prod.yml logs -f"
echo -e "    Restart:      docker-compose -f infra/docker-compose.prod.yml restart"
echo -e "    Stop:         docker-compose -f infra/docker-compose.prod.yml down"
echo ""

# Show service status
docker-compose -f infra/docker-compose.prod.yml ps
