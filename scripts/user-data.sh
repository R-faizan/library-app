#!/bin/bash
# ---------------------------------------------------------------------------
# EC2 USER DATA for the Launch Template (Amazon Linux 2023)
# Runs automatically as root the FIRST time every new instance boots.
# Because the Auto Scaling Group launches instances from this template,
# every new instance installs Docker and starts the app by itself.
#
# >>> CHANGE REPO_URL to YOUR GitHub repository before using it <<<
# Log of this script on the instance:  /var/log/user-data.log
# ---------------------------------------------------------------------------
REPO_URL="https://github.com/<your-github-username>/library-app.git"
APP_DIR="/opt/library-app"

exec > /var/log/user-data.log 2>&1
set -eux

# 1. Swap space (t2.micro/t3.micro only have 1 GB RAM; MySQL needs some room)
if [ ! -f /swapfile ]; then
  dd if=/dev/zero of=/swapfile bs=1M count=1024
  chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile swap swap defaults 0 0' >> /etc/fstab
fi

# 2. Install Docker + Git, start Docker now and on every reboot
dnf update -y
dnf install -y docker git
systemctl enable --now docker
usermod -aG docker ec2-user          # let ec2-user run docker without sudo

# 3. Install the Docker Compose v2 plugin
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
     -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
docker compose version

# 4. Get the application code
git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR"
cp .env.example .env
chmod 600 .env                       # secrets readable by owner (root) only

# 5. Build the image and start web + db containers
docker compose up -d --build
docker compose ps
