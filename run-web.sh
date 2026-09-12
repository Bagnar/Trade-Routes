#!/usr/bin/env bash
# Starts the web app for local development: installs dependencies on first run, then `npm run dev`.
# macOS / Linux: ./run-web.sh   (Windows: double-click run-web.cmd)
set -euo pipefail
cd "$(dirname "$0")/web"
command -v npm >/dev/null || { echo "Node.js 22 is required: https://nodejs.org"; exit 1; }
[ -d node_modules ] || npm install
echo "Site: http://localhost:3000  (Ctrl+C to stop)"
npm run dev
