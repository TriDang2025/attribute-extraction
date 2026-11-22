import sys, json; sys.path[:0]=['.','scripts']
import numpy as np, pandas as pd
from collections import Counter
from sklearn.metrics import silhouette_score
import g3_nojoin_v50 as G3, g3_ctxsplit_v50 as G, mainclaim_v46 as M46
from run import encoder
from s1a import ctxsplit_v50 as CS
enc=encoder(); rows=[]
for s in ('dev50',):
    mt,labels,emap,final,step3=G3.load(s)
    cols=json.load(open(step3/'columns.json',encoding='utf-8'))[M46.RUN_OF[s]]
    vec,ctx=G.context_vectors(s,mt,enc)
    v=np.load(f'results/graph_v22_{s}/spans/vectors.npz'); X=dict(zip(v['mention_id'].tolist(),v['x']))
    for k in cols:
        byc={}
        for p in cols[k]['parts']: byc.setdefault(p['cluster'],{})[p['key']]=[int(i) for i in p['mention_ids']]
        for cl,old in byc.items():
            if len(old)<2: continue
            ids=sorted(set().union(*map(set,old.values()))); 
            lab_llm=[next(j for j,(kk,m) in enumerate(old.items()) if i in m) for i in ids]
            if len(set(lab_llm))<2: continue
            xv=np.stack([X[i] for i in ids]); xc=np.stack([vec[i] for i in ids])
            lab_ctx=CS.kmeans_parts(xc,len(old))
            def pur(lb):
                tot=0
                for j in set(lb):
                    ls=[l for i,l2 in zip(ids,lb) if l2==j for l in (labels.get(i) or [''])[:1]]
                    tot+=Counter(ls).most_common(1)[0][1]
                return round(tot/len(ids),2)
            rows.append(dict(cluster=cl,n=len(ids),k=len(old),
                 sil_val_llm=round(silhouette_score(xv,lab_llm,metric='cosine'),3),
                 sil_ctx_llm=round(silhouette_score(xc,lab_llm,metric='cosine'),3),
                 sil_ctx_km=round(silhouette_score(xc,lab_ctx,metric='cosine'),3) if len(set(lab_ctx))>1 else 0,
                 sil_val_km=round(silhouette_score(xv,lab_ctx,metric='cosine'),3) if len(set(lab_ctx))>1 else 0,
                 pur_llm=pur(lab_llm),pur_ctx=pur(lab_ctx)))
df=pd.DataFrame(rows); df['better']=np.sign(df.pur_ctx-df.pur_llm)
pd.set_option('display.width',200)
print(df.sort_values('better').to_string(index=False))
