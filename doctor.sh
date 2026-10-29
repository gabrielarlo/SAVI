#!/usr/bin/env bash
# Doctor: verify HOST machine requirements for a dockerized LocalRAG deployment.
#
# The application itself runs inside Docker (see docker-compose.yml); this script
# checks that the HOST has everything needed to run it in staging/production:
# Docker, an Ollama instance with the required models, the environment config,
# and minimum machine resources (RAM/CPU/disk).
#
# Exit code 0 if every required check passes, 1 otherwise.
# Usage: ./doctor.sh   (sources ./.env automatically if present)

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ERRORS=0
WARNINGS=0

ok()   { echo "[OK]   $*"; }
fail() { ERRORS=$((ERRORS+1)); echo "[FAIL] $*"; }
warn() { WARNINGS=$((WARNINGS+1)); echo "[WARN] $*"; }

# --- Source .env if present ---
if [ -f "$ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$ROOT/.env"
    set +a
    ok "loaded $ROOT/.env"
fi

# --- Host machine resources ---
CPU_CORES="$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1)"
if [ "$CPU_CORES" -ge 2 ]; then ok "CPU cores: $CPU_CORES"; else warn "only $CPU_CORES CPU core(s); 2+ recommended"; fi

# RAM (Linux /proc/meminfo, macOS sysctl)
RAM_GB=""
if [ -r /proc/meminfo ]; then
    MEM_KB="$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)"
    RAM_GB="$(awk -v kb="$MEM_KB" 'BEGIN {printf "%.1f", kb/1024/1024}')"
elif command -v sysctl >/dev/null 2>&1; then
    MEM_BYTES="$(sysctl -n hw.memsize 2>/dev/null || echo 0)"
    RAM_GB="$(awk -v b="$MEM_BYTES" 'BEGIN {printf "%.1f", b/1024/1024/1024}')"
fi
if [ -z "$RAM_GB" ]; then
    warn "could not determine total RAM"
elif awk -v r="$RAM_GB" 'BEGIN {exit !(r>=8)}'; then
    ok "RAM: ${RAM_GB} GB"
elif awk -v r="$RAM_GB" 'BEGIN {exit !(r>=4)}'; then
    warn "RAM: ${RAM_GB} GB (8 GB+ recommended for Ollama models)"
else
    fail "RAM: ${RAM_GB} GB (minimum 4 GB required)"
fi

# Free disk on project filesystem
if command -v df >/dev/null 2>&1; then
    FREE_KB="$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')"
    FREE_GB="$(awk -v kb="$FREE_KB" 'BEGIN {printf "%.1f", kb/1024/1024}')"
    if awk -v g="$FREE_GB" 'BEGIN {exit !(g>=10)}'; then
        ok "free disk: ${FREE_GB} GB"
    elif awk -v g="$FREE_GB" 'BEGIN {exit !(g>=5)}'; then
        warn "free disk: ${FREE_GB} GB (10 GB+ recommended for models/images)"
    else
        fail "free disk: ${FREE_GB} GB (minimum 5 GB required)"
    fi
else
    warn "df not available; skipping disk check"
fi

# --- Docker ---
if command -v docker >/dev/null 2>&1; then
    ok "docker on PATH"
else
    fail "docker not found on PATH (required to run the containerized app)"
fi
COMPOSE_OK=0
if docker compose version >/dev/null 2>&1; then
    COMPOSE_OK=1
elif command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then
    COMPOSE_OK=1
fi
if [ "$COMPOSE_OK" -eq 1 ]; then ok "docker compose available"; else fail "docker compose not available (required)"; fi

# --- Required env vars ---
check_env() {
    local name="$1" required="$2"
    local val="${!name:-}"
    if [ -n "$val" ]; then
        ok "env $name set"
    elif [ "$required" = "1" ]; then
        fail "required env var $name is not set"
    else
        warn "optional env var $name unset (default will be used)"
    fi
}
check_env ADMIN_SECRET 1
check_env OLLAMA_URL 1
for v in QDRANT_URL DATABASE_URL CHAT_MODEL ENV CHAT_THINK CHAT_NUM_CTX CHAT_NUM_PREDICT; do
    check_env "$v" 0
done

# --- HTTP helper ---
http_code() {
    # prints HTTP status code or 000 on failure
    curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$1" 2>/dev/null || echo "000"
}

# --- Ollama on host ---
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
OLLAMA_URL="${OLLAMA_URL%/}"
CHECK_URL="${OLLAMA_URL//host.docker.internal/localhost}"
TAGS_URL="$CHECK_URL/api/tags"
CODE="$(http_code "$TAGS_URL")"
if [ "$CODE" -ge 200 ] && [ "$CODE" -lt 500 ]; then
    ok "Ollama reachable at $CHECK_URL"
    CHAT_MODEL="${CHAT_MODEL:-llama3.2:3b}"
    TAGS_JSON="$(curl -s --max-time 5 "$TAGS_URL" 2>/dev/null || true)"
    if echo "$TAGS_JSON" | grep -q "\"name\"[[:space:]]*:[[:space:]]*\"${CHAT_MODEL}\""; then
        ok "chat model '$CHAT_MODEL' is pulled in Ollama"
    else
        fail "chat model '$CHAT_MODEL' is NOT pulled in Ollama (run: ollama pull $CHAT_MODEL)"
    fi
    if echo "$TAGS_JSON" | grep -q '"name"[[:space:]]*:[[:space:]]*"nomic-embed-text'; then
        ok "embedding model 'nomic-embed-text' is pulled"
    else
        fail "embedding model 'nomic-embed-text' is NOT pulled (run: ollama pull nomic-embed-text)"
    fi
else
    fail "Ollama not reachable at $CHECK_URL (start Ollama on the host)"
fi

# --- Qdrant (runs in compose; check host port) ---
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
QDRANT_URL="${QDRANT_URL%/}"
QDRANT_CHECK="${QDRANT_URL//qdrant/localhost}"
QCODE="$(http_code "$QDRANT_CHECK/")"
if [ "$QCODE" -ge 200 ] && [ "$QCODE" -lt 500 ]; then
    ok "Qdrant reachable at $QDRANT_CHECK"
else
    warn "Qdrant not reachable at $QDRANT_CHECK (ok if compose not started yet)"
fi

# --- Project files ---
for rel in app/main.py migrations requirements.txt docker-compose.yml Dockerfile; do
    if [ -e "$ROOT/$rel" ]; then ok "project file present: $rel"; else fail "missing project file: $rel"; fi
done
if [ -d "$ROOT/ui/build" ]; then ok "ui/build present (admin console)"; else warn "ui/build missing (admin console will not be served; run the UI build)"; fi

# --- DNS sanity for host.docker.internal ---
HOST="$(echo "$OLLAMA_URL" | sed -E 's#https?://##' | cut -d/ -f1 | cut -d: -f1)"
if [ "$HOST" = "host.docker.internal" ]; then
    if getent hosts "$HOST" >/dev/null 2>&1 || (command -v dscacheutil >/dev/null 2>&1 && dscacheutil -q host -a name "$HOST" >/dev/null 2>&1); then
        ok "DNS resolves: $HOST"
    else
        warn "$HOST does not resolve (only an issue when running outside Docker Desktop)"
    fi
fi

echo
if [ "$ERRORS" -gt 0 ]; then
    echo "Doctor: $ERRORS failure(s), $WARNINGS warning(s)."
    exit 1
fi
echo "Doctor: all checks passed ($WARNINGS warning(s))."
exit 0
PYEOF
chmod +x /Volumes/PANDORA/PROJECTS/LocalRAG/doctor.sh
echo written