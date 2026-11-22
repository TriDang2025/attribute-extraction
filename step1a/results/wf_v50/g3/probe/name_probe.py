import sys, json, glob, re, itertools; sys.path[:0]=['.','scripts']
import pandas as pd
from collections import Counter
import mainclaim_v46 as M46
from s1a import step4_inputs as I, step4_gt as SG
def toks(n): return frozenset(t for t in re.split(r'[_\s]+', n.lower()) if t)
def compat(a,b):
    if not a or not b or 'not_attribute' in (a,b): return True
    A,B=toks(a),toks(b); return A<=B or B<=A
rows=[]
for s in ('dev50','dev50b'):
    run=M46.RUN_OF[s]; d=f'results/wf_v46/y3/{s}/step3'
    names={}  # (cluster, order) -> name
    for fam in ('names','rescuen'):
        for f in glob.glob(f'{d}/responses/*_{fam}_{run}_s*_*.jsonl'):
            o=re.search(r'_s(\d)_',f).group(1)
            for line in open(f,encoding='utf-8'):
                p=json.loads(line).get('parsed') or {}
                if isinstance(p,dict):
                    for k,v in p.items():
                        if isinstance(v,str) and '#' in k: names.setdefault((k,o),v) if fam=='rescuen' else names.__setitem__((k,o),v)
    mt=pd.read_csv(f'results/graph_v22_{s}/spans/mentions.csv',dtype=str,keep_default_na=False); mt['mention_id']=mt.mention_id.astype(int); mt=mt.set_index('mention_id')
    gt=pd.read_csv(I.GT_LEVELS[s],keep_default_na=False); lab={int(i):SG.split_labels(v) for i,v in zip(gt.mention_id,gt.gt_L2)}
    final=json.load(open(f'{d}/scores/final_columns.json',encoding='utf-8'))[run]
    for key,cols in final.items():
        for c in cols:
            grp={}
            for m in c['members']:
                cl,g=m.split('@'); grp.setdefault(g,set()).add(cl)
            ids=set(int(i) for i in c['mention_ids'])
            for g,cls in grp.items():
                for a,b in itertools.combinations(sorted(cls),2):
                    ua=[i for i in ids if mt.at[i,'cluster_id']==a]; ub=[i for i in ids if mt.at[i,'cluster_id']==b]
                    la=Counter(l for i in ua for l in lab.get(i,[])).most_common(1); lb=Counter(l for i in ub for l in lab.get(i,[])).most_common(1)
                    if not la or not lb: continue
                    na=[names.get((a,o),'') for o in '012']; nb=[names.get((b,o),'') for o in '012']
                    inc=[not compat(x,y) for x,y in zip(na,nb)]
                    maj=lambda ns: Counter(n for n in ns if n).most_common(1)[0][0] if any(ns) else ''
                    rows.append(dict(set=s,col=c['name'],a=a,b=b,na='/'.join(na),nb='/'.join(nb),la=la[0][0],lb=lb[0][0],same=la[0][0]==lb[0][0],
                        n_inc=sum(inc),maj_inc=not compat(maj(na),maj(nb)),n=len(ua)+len(ub)))
df=pd.DataFrame(rows); df.to_csv(sys.argv[1],index=False)
for s,g in df.groupby('set'):
    print(s,'pairs',len(g),'diff',int((~g.same).sum()),'same',int(g.same.sum()))
    for nm,blk in [('majority',g.maj_inc),('any order',g.n_inc>=1),('>=2 orders',g.n_inc>=2),('all 3',g.n_inc>=3)]:
        print(f'  {nm:10s} block diff {int((blk&~g.same).sum())}  block same {int((blk&g.same).sum())}')
