#!/usr/bin/env bash
# Shows servers, GPU, run state, and per-file progress with mean seconds per text.
#   bash colab/status.sh
source "$(dirname "$0")/env.sh"
cd "$TEAR_PROJECT"

echo "== servers"
for port in 1234 8082 8081; do
  curl -s "http://localhost:$port/health" 2>/dev/null | grep -q ok && echo "$port up" || echo "$port down"
done
echo "== GPU"
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null
echo "== run_all"
PIDFILE="$TEAR_LOGS/run_all.pid"
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then echo "running (pid $(cat "$PIDFILE"))"; else echo "not running"; fi
tail -n 5 results/run_all.log 2>/dev/null
echo "== shared state (GitHub)"
cat results/RUN_OWNER 2>/dev/null || echo "no RUN_OWNER yet"
(cd "$REPO_ROOT" && git log -1 --format="last commit: %h %an %ar  %s" && git status -sb | head -1)
echo "== results (rows, mean s/text over all rows and over rows after the first 20)"
python - <<'EOF'
import json, pathlib, statistics
for p in sorted(pathlib.Path("results/conversation").glob("*.jsonl")):
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    secs = [r["seconds"] for r in rows if isinstance(r.get("seconds"), (int, float))]
    new = secs[20:]
    print(f"{p.name:28s} {len(rows):4d} rows  all {statistics.mean(secs) if secs else 0:7.1f}s"
          f"  new {statistics.mean(new) if new else 0:7.1f}s")
EOF
