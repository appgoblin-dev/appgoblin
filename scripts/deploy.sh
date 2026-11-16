#!/bin/bash
set -euo pipefail
APPDIR="/home/goblin/appgoblin"
FRONTEND_DIR="$APPDIR/frontend"
BUILD_DIR="$FRONTEND_DIR/build"
NEW_BUILD="$FRONTEND_DIR/build_tmp"


echo "Deploying from: $APPDIR"
cd "$APPDIR"

# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "Enabling systemd services..."
sudo systemctl enable "$APPDIR/scripts/appgoblin-api.service"
sudo systemctl enable "$APPDIR/scripts/appgoblin-frontend.service"
sudo systemctl daemon-reload

echo "Restarting backend..."
sudo systemctl restart appgoblin-api

echo "Building frontend..."
cd "$FRONTEND_DIR"

# Only reinstall deps if package-lock.json changed
PREV_HEAD="${ORIG_HEAD:-HEAD~1}"
if git diff "$PREV_HEAD" HEAD --name-only | grep -q "frontend/package-lock.json"; then
    echo "Dependencies changed, reinstalling..."
    npm ci
else
    echo "Dependencies unchanged"
fi


# Clean any previous temp build first
rm -rf "$NEW_BUILD"

# Build to build_tmp
npm run build

if curl -fsSL --connect-timeout 5 --max-time 30 \
    https://raw.githubusercontent.com/ipverse/bot-ip-blocks/master/crawlers.json \
    -o "$NEW_BUILD/crawlers.json"; then
    echo "Downloaded crawler IP ranges"
else
    rm -f "$NEW_BUILD/crawlers.json"
    echo "Crawler IP ranges unavailable; using normal rate limits" >&2
fi

# Atomic swap
rm -rf build_old
if [ -d "$NEW_BUILD" ]; then
  mv build build_old
fi
mv "$NEW_BUILD" build
rm -rf build_old



echo "Restarting frontend..."
sudo systemctl restart appgoblin-frontend

echo "Deploy complete."
systemctl is-active appgoblin-api appgoblin-frontend