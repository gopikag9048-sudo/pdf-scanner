#!/usr/bin/env sh
set -eu

# Update virus DB (best-effort; don't fail the container if rate-limited)
freshclam || true

# Ensure writable temp dir (container runs read-only)
mkdir -p /tmp
chmod 1777 /tmp

exec python /app/scanner.py
