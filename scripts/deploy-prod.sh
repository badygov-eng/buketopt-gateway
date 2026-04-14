#!/usr/bin/env bash
# Деплой на main-server YC — только после явного «ДА, ДЕПЛОЙ» от владельца.
set -euo pipefail

REMOTE_USER="${DEPLOY_USER:-badygovdaniil}"
REMOTE_HOST="${DEPLOY_HOST:-158.160.153.14}"
REMOTE_DIR="${DEPLOY_DIR:-/opt/buketopt-gateway}"
IMAGE_NAME="${IMAGE_NAME:-buketopt-gateway:latest}"

echo "Сборка образа:"
echo "  docker build -t ${IMAGE_NAME} ."
echo ""
echo "На сервере ${REMOTE_USER}@${REMOTE_HOST}, каталог ${REMOTE_DIR}:"
echo "  rsync -avz --delete ./ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
echo ""
echo "Запуск (только loopback :8600):"
cat << 'EOF'
docker rm -f buketopt-gateway 2>/dev/null || true
docker run -d --name buketopt-gateway --restart unless-stopped \
  -p 127.0.0.1:8600:8600 \
  --env-file /path/to/.secrets/buketopt-gateway.env \
  buketopt-gateway:latest
EOF
echo ""
echo "Проверка: curl -sS http://127.0.0.1:8600/health"
