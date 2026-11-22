import sys, json, itertools, math; sys.path[:0]=['.','scripts']
import pandas as pd, numpy as np
from collections import Counter
import mainclaim_v46 as M46
from s1a import step4_inputs as I, step4_gt as SG
def cos(a,b):
    k=set(a)|set(b); va=np.array([a.get(x,0) for x in k]); vb=np.array([b.get(x,0) for x in k])
    n=np.linalg.norm(va)*np.linalg.norm(vb); return float(va@vb/n) if n else float('nan')
out=[]
for s in ('dev50','dev50b'):
    mt=pd.read_csv(f'results/graph_v22_{s}/spans/mentions.csv',dtype=str,keep_default_na=False); mt['mention_id']=mt.mention_id.astype(int); mt=mt.set_index('mention_id')
    gt=pd.read_csv(I.GT_LEVELS[s],keep_default_na=False)
    lab={int(i):SG.split_labels(v) for i,v in zip(gt.mention_id,gt.gt_L2)}
    final=json.load(open(f'results/wf_v46/y3/{s}/step3/scores/final_columns.json',encoding='utf-8'))[M46.RUN_OF[s]]
    for key,cols in final.items():
        ent=cols[0]['entity'] if 'entity' in cols[0] else None
        sub=mt[mt.cluster_id!='']
        ent=next(c["entity"] for c in cols if c.get("entity")) if any(c.get("entity") for c in cols) else sub.loc[next(int(i) for c in cols for i in c["mention_ids"]),"entity"]
        es=sub[sub.entity==ent]
        df_=Counter(w for c,g in es.groupby('cluster_id') for w in set(g.left_word.str.lower()))
        ncl=es.cluster_id.nunique(); idf={w:math.log((1+ncl)/(1+d)) for w,d in df_.items()}
        def vec(ids): 
            c=Counter(mt.at[i,'left_word'].lower() for i in ids); return {w:n*idf.get(w,0) for w,n in c.items()}
        for c in cols:
            grp={}
            for m in c['members']:
                cl,g=m.split('@'); grp.setdefault(g,set()).add(cl)
            ids=set(int(i) for i in c['mention_ids'])
            for g,cls in grp.items():
                if len(cls)<2: continue
                units={cl:[i for i in ids if mt.at[i,'cluster_id']==cl] for cl in cls}
                for a,b in itertools.combinations(sorted(units),2):
                    la=Counter(l for i in units[a] for l in lab.get(i,[])).most_common(1); lb=Counter(l for i in units[b] for l in lab.get(i,[])).most_common(1)
                    la=la[0][0] if la else ''; lb=lb[0][0] if lb else ''
                    if not la or not lb: continue
                    out.append(dict(set=s,col=c['name'],a=a,b=b,na=len(units[a]),nb=len(units[b]),cos=cos(vec(units[a]),vec(units[b])),la=la,lb=lb,same=la==lb))
df=pd.DataFrame(out)
for s,g in df.groupby('set'):
    print(s); print(g.groupby('same').cos.describe().to_string())
    for t in (0.1,0.2,0.3,0.4,0.5):
        blk=g.cos<t; print(f' tau {t}: block diff {int((blk&~g.same).sum())}/{int((~g.same).sum())}, block same {int((blk&g.same).sum())}/{int(g.same.sum())}')
df.to_csv(sys.argv[1],index=False)
