#!/usr/bin/env bash
# Starts tools/run_all.py in the background, with results committed to GitHub every 30 min and at the end.
#   bash colab/run.sh N [ALL_LEVELS]      N = first N Conversation test texts; ALL_LEVELS = 1 (default) or 0
#   FORCE=1 bash colab/run.sh N           start even if results/RUN_OWNER says someone else's run is active
# Rerun the same command after a disconnect: every step skips texts already in the committed results.
# Only one TEAR run at a time across all collaborators: they write the same result files.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$TEAR_PROJECT"

if [ "${1:-}" = _worker ]; then
  # ---- background worker ----
  N=$2
  python tools/run_all.py > "$TEAR_LOGS/run_all_N$N.out" 2>&1 &
  RUN=$!
  while kill -0 "$RUN" 2>/dev/null; do
    for _ in $(seq 180); do kill -0 "$RUN" 2>/dev/null || break; sleep 10; done
    bash colab/sync.sh push-data || true
    bash colab/sync.sh push-results "N=$N in progress" || true
  done
  wait "$RUN" && STATE=done || STATE=failed
  sed -i "s/^state=.*/state=$STATE/" results/RUN_OWNER
  bash colab/sync.sh push-data || true
  bash colab/sync.sh push-results "N=$N $STATE"
  exit 0
fi

N=${1:?usage: bash colab/run.sh N [ALL_LEVELS]}
ALL=${2:-1}
PIDFILE="$TEAR_LOGS/run_all.pid"
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "run already going on this VM (pid $(cat "$PIDFILE")); see bash colab/status.sh"; exit 1
fi
for port in 1234 8082; do
  curl -s "http://localhost:$port/health" | grep -q ok || { echo "port $port down: bash colab/start_servers.sh"; exit 1; }
done

# Claim the run: refuse if another person's run is still marked running (less than 24 h old).
(cd "$REPO_ROOT" && git pull -q --rebase --autostash)
ME="$(git config user.name)"
if [ -f results/RUN_OWNER ] && grep -q '^state=running' results/RUN_OWNER && [ "${FORCE:-0}" != 1 ]; then
  OWNER=$(sed -n 's/^owner=//p' results/RUN_OWNER); STARTED=$(sed -n 's/^started=//p' results/RUN_OWNER)
  AGE=$(( $(date -u +%s) - $(date -u -d "$STARTED" +%s 2>/dev/null || echo 0) ))
  if [ "$OWNER" != "$ME" ] && [ "$AGE" -lt 86400 ]; then
    echo "results/RUN_OWNER: $OWNER started a run at $STARTED and it is still marked running."
    echo "Ask them first, or rerun with FORCE=1 if that run is dead."; exit 1
  fi
fi
printf 'owner=%s\nstarted=%s\nN=%s\nall_levels=%s\nstate=running\n' "$ME" "$(date -u '+%F %T')" "$N" "$ALL" > results/RUN_OWNER
bash colab/sync.sh push-results "N=$N started by $ME"

export TEAR_N=$N
if [ "$ALL" = 1 ]; then export TEAR_ALL_LEVELS=1; else unset TEAR_ALL_LEVELS; fi
setsid nohup bash "$0" _worker "$N" > "$TEAR_LOGS/worker_N$N.out" 2>&1 &
echo $! > "$PIDFILE"
echo "started run_all N=$N all_levels=$ALL (pid $!). Progress: results/run_all.log; bash colab/status.sh"
