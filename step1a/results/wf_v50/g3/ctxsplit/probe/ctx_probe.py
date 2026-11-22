import sys, re; sys.path[:0]=['.','scripts']
import pandas as pd, numpy as np
from collections import Counter
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from run import encoder
from s1a import mentions as MN, step4_inputs as I, step4_gt as SG
W=4
enc=encoder()
rows=[]
for s in ('dev50','dev50b'):
    run=f'results/graph_v22_{s}'
    docs,_,_=MN.load_shared(run)
    mt=pd.read_csv(f'{run}/spans/mentions.csv',dtype=str,keep_default_na=False); mt=mt[mt.cluster_id!='']
    gt=pd.read_csv(I.GT_LEVELS[s],keep_default_na=False); lab=dict(zip(gt.mention_id.astype(str),gt.gt_L2))
    def left(r):
        lo,_=MN.turn_bounds(docs[r.dialogue_id],int(r.turn)); words=re.findall(r"[\w']+",docs[r.dialogue_id].text[lo:int(r.char_start)])
        return ' '.join(words[-W:]) or '[start]'
    mt['ctx']=[left(r) for r in mt.itertuples()]
    uniq=sorted(set(mt.ctx)); X=dict(zip(uniq, enc.encode(uniq)))
    for c,g in mt.groupby('cluster_id'):
        if len(g)<8: continue
        x=np.stack([X[t] for t in g.ctx]); x=x/np.linalg.norm(x,axis=1,keepdims=True)
        km=KMeans(2,n_init=10,random_state=0).fit(x); sil=silhouette_score(x,km.labels_,metric='cosine') if len(set(km.labels_))>1 else 0
        labs=[lab.get(i,'') for i in g.mention_id]
        top,k=Counter(labs).most_common(1)[0]
        parts=[Counter(l for l,p in zip(labs,km.labels_) if p==j) for j in (0,1)]
        rows.append(dict(set=s,cluster=c,n=len(g),sil=round(float(sil),3),purity=round(k/len(g),2),top=top,
             minpart=min(sum(p.values()) for p in parts),
             p0=dict(parts[0].most_common(2)),p1=dict(parts[1].most_common(2)),
             ex0=Counter(t for t,p in zip(g.ctx,km.labels_) if p==0).most_common(2),ex1=Counter(t for t,p in zip(g.ctx,km.labels_) if p==1).most_common(2)))
enc.save()
df=pd.DataFrame(rows); df.to_csv(sys.argv[1],index=False)
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',60)
print(df.sort_values(['set','sil'],ascending=[True,False])[['set','cluster','n','sil','purity','top','minpart','p0','p1']].to_string(index=False))
