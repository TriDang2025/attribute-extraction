# wf_v5.0 G0: dev50c gold build (same recipe as dev50b). Outputs go to logs only; do not read results before the final check.
cd /c/Users/nguye/repos/attribute-extraction-wf-v5.0/step1a
PY=/c/Users/nguye/venvs/chunking/Scripts/python.exe
G=results/wf_v50/g0
start=$(date +%s)
$PY -u scripts/export_mentions.py --split dev50c --unseal --limit 50 --input both --variant F_m2_t06_bk --out $G/graph_v22_dev50c > $G/export.log 2>&1 || { echo export_failed > $G/g0.flag; exit 1; }
echo "export wall $(( $(date +%s) - start ))s" >> $G/export.log
$PY -u scripts/gt_v35.py --run $G/graph_v22_dev50c --mwoz C:/Users/nguye/data/MultiWOZ_2.2 --out $G/gt --auto-entities > $G/gt.log 2>&1 || { echo gt_failed > $G/g0.flag; exit 1; }
echo finished > $G/g0.flag
