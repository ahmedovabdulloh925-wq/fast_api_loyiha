#!/usr/bin/env bash
# ==============================================================================
# AWS EC2 Ubuntu Serverini Boshlang'ich Sozlash Skripti (Bootstrap)
# ==============================================================================
set -euo pipefail

echo ">>> 1. Tizim paketlarini yangilash..."
sudo apt-get update && sudo apt-get upgrade -y

echo ">>> 2. Kerakli dasturlarni o'rnatish (Python, Git, PostgreSQL, Nginx)..."
sudo apt-get install -y python3 python3-venv python3-pip git postgresql postgresql-contrib nginx curl ufw

echo ">>> 3. Papka va ruxsatlarni sozlash..."
sudo mkdir -p /opt/warehouse-api
sudo chown -R ubuntu:ubuntu /opt/warehouse-api

echo ">>> 4. PostgreSQL bazasi va foydalanuvchisini yaratish..."
sudo -u postgres psql -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'warehouse_user') THEN CREATE ROLE warehouse_user WITH LOGIN PASSWORD 'warehouse_password' CREATEDB; END IF; END \$\$;"
sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname = 'warehouse_db';" | grep -q 1 || sudo -u postgres createdb -O warehouse_user warehouse_db
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE warehouse_db TO warehouse_user;"

echo ">>> 5. Nginx konfiguratsiyasini o'rnatish..."
sudo cp /opt/warehouse-api/deploy/nginx.conf /etc/nginx/sites-available/warehouse-api
sudo ln -sf /etc/nginx/sites-available/warehouse-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo ">>> 6. Systemd xizmatini o'rnatish..."
sudo cp /opt/warehouse-api/deploy/warehouse-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable warehouse-api

echo ">>> 7. Xavfsizlik devori (UFW) sozlash..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo ">>> Bootstrap muvaffaqiyatli yakunlandi!"
echo ">>> Endi /opt/warehouse-api/.env fayliga ishlab chiqarish kalitlarini yozing va birinchi marta deploy.sh ni ishga tushiring."
