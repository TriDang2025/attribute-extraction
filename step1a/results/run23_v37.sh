cd /c/Users/nguye/repos/attribute-extraction-wf-v3.7/step1a
PY=/c/Users/nguye/venvs/chunking/Scripts/python.exe
for s in "dev dev50" "dev50b dev50b"; do
  set -- $s; split=$1; name=$2
  out=results/graph_v23_$name
  mkdir -p $out
  start=$(date +%s)
  $PY -u scripts/export_mentions.py --split $split --limit 50 --input spans --variant V23 --from-run results/graph_v22_$name --out $out > $out/export.log 2>&1
  echo "export wall $(( $(date +%s) - start ))s" >> $out/export.log
  start=$(date +%s)
  $PY -u scripts/graph_run.py --run $out --input spans --split $split --limit 50 --variant V23 --stage coverage --stage graph --stage stability --stage signals --stage labels > $out/stages_1_4.log 2>&1
  echo "stages wall $(( $(date +%s) - start ))s" >> $out/stages_1_4.log
done
echo finished > results/graph_v23_done.flag
