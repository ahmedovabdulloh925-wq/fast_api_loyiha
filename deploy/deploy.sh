#!/usr/bin/env bash
# ==============================================================================
# Warehouse API - Avtomatik Deploy Skripti
# ==============================================================================
set -euo pipefail

APP_DIR="/opt/warehouse-api"
COMMIT_SHA="${1:-HEAD}"

echo ">>> [Deploy] Boshlandi. Maqsadli commit: ${COMMIT_SHA}"
cd "${APP_DIR}"

# 1. Kodni yangilash
echo ">>> [Git] Kod yuklab olinmoqda..."
git fetch origin main
git checkout "${COMMIT_SHA}"

# 2. Virtual environment va dependencylar
echo ">>> [Pip] Kutubxonalar o'rnatilmoqda..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Alembic migratsiyalarini bajarish
echo ">>> [Alembic] Baza migratsiyalari bajarilmoqda..."
alembic upgrade head

# 4. Systemd xizmatini qayta ishga tushirish
echo ">>> [Systemd] Xizmat qayta ishga tushirilmoqda..."
sudo systemctl restart warehouse-api

# 5. /health tekshiruvi (Healthcheck retry)
echo ">>> [Healthcheck] Server salomatligi tekshirilmoqda..."
MAX_RETRIES=10
RETRY_DELAY=2
READY=0

for i in $(seq 1 ${MAX_RETRIES}); do
    if curl -f -s http://127.0.0.1:8000/health > /dev/null; then
        READY=1
        echo ">>> [Healthcheck] Tizim muvaffaqiyatli ishga tushdi! (Urinish: ${i})"
        break
    else
        echo ">>> [Healthcheck] Server hali tayyor emas, ${RETRY_DELAY} soniya kutilmoqda... (${i}/${MAX_RETRIES})"
        sleep ${RETRY_DELAY}
    fi
done

if [ ${READY} -eq 0 ]; then
    echo ">>> [XATOLIK] /health tekshiruvdan o'tmadi! Xizmat loglari:"
    sudo journalctl -u warehouse-api -n 30 --no-pager
    exit 1
fi

echo ">>> [Deploy] Muvaffaqiyatli yakunlandi!"
