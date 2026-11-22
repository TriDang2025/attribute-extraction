import sys; sys.path[:0]=['.','scripts']
import pandas as pd, numpy as np
df=pd.read_csv(sys.argv[1])
out=[]
for s,g in df.groupby('set'):
    v=np.load(f'results/graph_v22_{s}/spans/vectors.npz'); X=dict(zip(v['mention_id'].tolist(),v['x']))
    mt=pd.read_csv(f'results/graph_v22_{s}/spans/mentions.csv',dtype=str,keep_default_na=False)
    cen={c:np.mean([X[int(i)] for i in grp.mention_id],axis=0) for c,grp in mt[mt.cluster_id!=''].groupby('cluster_id')}
    cen={c:x/np.linalg.norm(x) for c,x in cen.items()}
    g=g.assign(cos=[float(cen[a]@cen[b]) for a,b in zip(g.a,g.b)])
    print(s); print(g.groupby('same').cos.describe().round(3).to_string())
    for t in (0.5,0.55,0.6,0.65,0.7):
        blk=g.cos<t; print(f' tau {t}: block diff {int((blk&~g.same).sum())}/{int((~g.same).sum())} same {int((blk&g.same).sum())}/{int(g.same.sum())}')
    out.append(g)
pd.concat(out).to_csv(sys.argv[2],index=False)
