"""Build a self-contained HTML viewer for one run: raw dialogue turns, gold domains, and each method's chunks.

  python scripts/make_viewer.py results/S_n50          # -> results/S_n50/viewer.html
  python scripts/make_viewer.py results/T_seed42 --limit 10
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chk import data, metrics  # noqa: E402


def load_docs(run):
    name = run.name
    limit = int(name.split("_n")[-1]) if "_n" in name else None
    dlg = data.load_dialogues(limit)
    if name.startswith("S"):
        return data.single_docs(dlg)
    seed = int(name.split("seed")[1].split("_")[0])
    return data.stitched_docs(dlg, seed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--limit", type=int, help="only the first N documents")
    a = ap.parse_args()
    run = Path(a.run).resolve()
    docs = load_docs(run)
    if a.limit:
        docs = docs[:a.limit]
    methods = {}
    for f in sorted((run / "chunks").glob("*.jsonl")):
        rows = {json.loads(l)["doc_id"]: json.loads(l) for l in open(f, encoding="utf-8")}
        methods[f.stem.replace("_", "@", 1) if f.stem not in ("fixed", "texttiling") else f.stem] = rows
    out_docs = []
    for d in docs:
        m_out = {}
        for m, rows in methods.items():
            if d.doc_id not in rows:
                continue
            spans, _ = metrics.align(d.text, rows[d.doc_id]["chunks"])
            gaps, inside = metrics.cuts_to_gaps(d, spans)
            m_out[m] = {"spans": spans, "gaps": sorted(gaps), "inside": inside}
        out_docs.append({"id": d.doc_id, "text": d.text, "turns": d.spans, "domains": d.domains,
                         "dialogue": d.dialogue, "gold": sorted(d.gold_gaps), "methods": m_out})
    scores = list(csv.DictReader(open(run / "metrics.csv", encoding="utf-8"))) if (run / "metrics.csv").exists() else []
    payload = json.dumps({"run": run.name, "methods": list(methods), "docs": out_docs, "scores": scores},
                         ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA__", payload).replace("__TITLE__", f"Chunk viewer {run.name}")
    out = run / "viewer.html"
    out.write_text(html, encoding="utf-8")
    print(out, f"{out.stat().st_size / 1e6:.1f} MB, {len(out_docs)} docs, {len(methods)} methods")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#fbfaf7;--fg:#1d1d1b;--mut:#6b6a66;--line:#e3e1db;--card:#fff;--cut:#c2410c;--gold:#15803d;--miss:#a16207;
--d-train:#dbeafe;--d-hotel:#fce7f3;--d-restaurant:#fef3c7;--d-attraction:#dcfce7;--d-taxi:#ede9fe;--d-hospital:#fee2e2;--d-police:#e0e7ff;--d-general:#f1f5f9;--d-bus:#e0f2fe;
--c0:#f3f0e8;--c1:#e6eef7}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#161614;--fg:#ecebe6;--mut:#9b9a94;--line:#33322e;--card:#1f1f1c;--cut:#fb923c;--gold:#4ade80;--miss:#facc15;
--d-train:#1e3a5f;--d-hotel:#5b2140;--d-restaurant:#57430f;--d-attraction:#1f4d2e;--d-taxi:#3b2d63;--d-hospital:#5c1f1f;--d-police:#2b3366;--d-general:#2a2f36;--d-bus:#173a52;--c0:#2a2924;--c1:#22303d}}
:root[data-theme=dark]{--bg:#161614;--fg:#ecebe6;--mut:#9b9a94;--line:#33322e;--card:#1f1f1c;--cut:#fb923c;--gold:#4ade80;--miss:#facc15;
--d-train:#1e3a5f;--d-hotel:#5b2140;--d-restaurant:#57430f;--d-attraction:#1f4d2e;--d-taxi:#3b2d63;--d-hospital:#5c1f1f;--d-police:#2b3366;--d-general:#2a2f36;--d-bus:#173a52;--c0:#2a2924;--c1:#22303d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
header{padding:14px 16px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:10px;align-items:center}
h1{font-size:17px;margin:0 12px 0 0}select,button{font:inherit;padding:4px 8px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:6px}
main{padding:12px 16px;max-width:1500px}.legend{color:var(--mut);font-size:12.5px;margin:6px 0 12px}
.legend b{color:var(--fg)}.sw{display:inline-block;width:10px;height:10px;border-radius:2px;vertical-align:middle;margin:0 3px 0 8px}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card)}
table{border-collapse:collapse;width:100%;min-width:760px}th,td{padding:4px 6px;border-bottom:1px solid var(--line);vertical-align:top}
th{position:sticky;top:0;background:var(--card);font-weight:600;font-size:12px;text-align:left;z-index:1}
td.t{max-width:620px}td.dom{font-size:11.5px;white-space:nowrap}td.n{color:var(--mut);font-size:11.5px;text-align:right}
td.m{text-align:center;font-size:11.5px;width:74px;color:var(--mut);cursor:pointer}
tr.goldcut td{border-bottom:2px solid var(--gold)}tr.dlgcut td{border-bottom:3px double var(--gold)}
.cut{color:var(--cut);font-weight:700}.mid{color:var(--cut);font-weight:700;font-size:10px}
.chunks{margin-top:14px;display:grid;gap:8px}.chunk{border:1px solid var(--line);border-radius:6px;padding:8px;background:var(--card);white-space:pre-wrap}
.chunk .h{font-size:11.5px;color:var(--mut);margin-bottom:4px;white-space:normal}.mark{background:var(--cut);color:#fff;border-radius:3px;padding:0 3px;font-size:10px}
.scores{font-size:12px;margin:10px 0}.scores td,.scores th{padding:2px 8px}
</style></head><body>
<header><h1>__TITLE__</h1>
<label>Document <select id="doc"></select></label>
<button id="prev">&larr;</button><button id="next">&rarr;</button>
<label>Show chunks of <select id="meth"></select></label>
<label><input type="checkbox" id="onlycut"> only docs with gold boundaries</label></header>
<main>
<div class="legend">Rows = turns (raw text). <b>Domain</b> = gold topic of the turn. Green line under a row = gold boundary (double = dialogue boundary).
Method columns: chunk number, shaded by chunk; <span class="cut">✂</span> = the method cuts after this turn;
<span class="mid">✂mid</span> = the method's cut falls inside this turn (snapped for scoring). Click a method column to list its chunks.</div>
<div id="sum" class="legend"></div>
<div class="wrap"><table id="tab"></table></div>
<h3 id="chh" style="font-size:15px;margin:16px 0 4px"></h3><div id="chunks" class="chunks"></div>
<details style="margin-top:16px"><summary>Run scores (metrics.csv)</summary><div class="wrap"><table class="scores" id="scores"></table></div></details>
</main>
<script>
const D=__DATA__;
const $=id=>document.getElementById(id);
const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
let docs=D.docs;
function fillDocs(){const only=$('onlycut').checked;const sel=$('doc');const cur=sel.value;sel.innerHTML='';
 docs.forEach((d,i)=>{if(only&&!d.gold.length)return;const o=document.createElement('option');o.value=i;
 o.textContent=`${d.id} (${d.turns.length} turns, ${d.gold.length} gold)`;sel.appendChild(o)});
 if([...sel.options].some(o=>o.value===cur))sel.value=cur;}
D.methods.forEach(m=>{const o=document.createElement('option');o.value=m;o.textContent=m;$('meth').appendChild(o)});
function chunkOfTurn(spans,turn){const mid=(turn[0]+turn[1])/2;return spans.findIndex(s=>mid>=s[0]&&mid<s[1]);}
function render(){
 const d=docs[+$('doc').value];if(!d)return;const ms=D.methods.filter(m=>d.methods[m]);
 const gold=new Set(d.gold);
 let h='<tr><th>#</th><th>Domain</th><th>Turn text</th>'+ms.map(m=>`<th title="${m}">${m.replace('@','<br>@')}</th>`).join('')+'</tr>';
 const midCut={};ms.forEach(m=>{midCut[m]=new Set();d.methods[m].spans.slice(1).forEach(s=>{d.turns.forEach((t,i)=>{if(s[0]>t[0]&&s[0]<t[1])midCut[m].add(i)})})});
 d.turns.forEach((t,i)=>{const dom=d.domains[i];const dl=i<d.turns.length-1&&d.dialogue[i]!==d.dialogue[i+1];
  const cls=gold.has(i)?(dl?'dlgcut':'goldcut'):'';
  h+=`<tr class="${cls}"><td class="n">${i}</td><td class="dom" style="background:var(--d-${dom},var(--d-general))">${dom}</td><td class="t">${esc(d.text.slice(t[0],t[1]))}</td>`;
  ms.forEach(m=>{const M=d.methods[m];const c=chunkOfTurn(M.spans,t);const cut=M.gaps.includes(i);
   h+=`<td class="m" data-m="${m}" style="background:var(--c${c%2})">${c}${cut?' <span class="cut">✂</span>':''}${midCut[m].has(i)?' <span class="mid">✂mid</span>':''}</td>`});
  h+='</tr>'});
 $('tab').innerHTML=h;
 const parts=ms.map(m=>{const g=new Set(d.methods[m].gaps);let hit=0;g.forEach(x=>{if(gold.has(x))hit++});
  return `<b>${m}</b>: ${d.methods[m].spans.length} chunks, ${hit}/${gold.size} gold cuts hit exactly`});
 $('sum').innerHTML=parts.join(' &nbsp;·&nbsp; ');
 document.querySelectorAll('td.m').forEach(td=>td.onclick=()=>{$('meth').value=td.dataset.m;showChunks()});
 showChunks();}
function showChunks(){const d=docs[+$('doc').value];const m=$('meth').value;const M=d&&d.methods[m];
 $('chh').textContent=M?`Chunks of ${m} (${M.spans.length}, ${M.inside} cut(s) inside a turn)`:'';
 $('chunks').innerHTML=M?M.spans.map((s,i)=>{const txt=d.text.slice(s[0],s[1]);
  return `<div class="chunk"><div class="h">chunk ${i} · ${txt.length} chars · offsets ${s[0]}–${s[1]}</div>${esc(txt)}</div>`}).join(''):'';}
function scores(){if(!D.scores.length)return;const keys=['method','chunks_per_doc','chars_mean','chars_max','pct_outside_limit','cuts_inside_turn_pct','Pk','WindowDiff','F1','F1_tol1','coherence_gap','purity','recall@1','recall@5','mrr@10','char_precision@5','char_recall@5'];
 $('scores').innerHTML='<tr>'+keys.map(k=>`<th>${k}</th>`).join('')+'</tr>'+D.scores.map(r=>'<tr>'+keys.map(k=>`<td>${r[k]??''}</td>`).join('')+'</tr>').join('');}
$('doc').onchange=render;$('meth').onchange=showChunks;$('onlycut').onchange=()=>{fillDocs();render()};
$('prev').onclick=()=>{const s=$('doc');if(s.selectedIndex>0){s.selectedIndex--;render()}};
$('next').onclick=()=>{const s=$('doc');if(s.selectedIndex<s.options.length-1){s.selectedIndex++;render()}};
fillDocs();scores();render();
</script></body></html>"""


if __name__ == "__main__":
    main()
