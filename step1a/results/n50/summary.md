# Step 1a, results

Units: {'chroma': 157, 'oracle_seg': 97, 'value': 444}; {'values_found': 444, 'values_missing': 16}

## Best configuration per unit type and method (mean over seeds, by B-cubed F1)

| Unit | Variant | Space | Method | Setting | K | Noise % | B-cubed F1 (range) | NMI | ARI | Purity |
|---|---|---|---|---|---|---|---|---|---|---|
| chroma | segment | umap5 | hdbscan | mcs=20,eom,ms=1 | 4 | 4 | 0.593 (0.59–0.60) | 0.517 | 0.407 | 0.699 |
| chroma | segment | umap5 | agglo | k=5 | 5 | 0 | 0.539 (0.52–0.56) | 0.478 | 0.370 | 0.656 |
| chroma | segment | umap5 | kmeans | k=5 | 5 | 0 | 0.532 (0.51–0.54) | 0.471 | 0.363 | 0.650 |
| oracle_seg | segment | umap5 | hdbscan | mcs=10,leaf,ms=1 | 4 | 5 | 0.980 (0.98–0.98) | 0.970 | 0.966 | 0.990 |
| oracle_seg | segment | umap5 | agglo | k=5 | 5 | 0 | 0.974 (0.96–0.98) | 0.961 | 0.958 | 0.986 |
| oracle_seg | segment | umap5 | kmeans | k=5 | 5 | 0 | 0.974 (0.96–0.98) | 0.961 | 0.958 | 0.986 |
| value | turn | raw | hdbscan | mcs=3,eom,ms=1 | 52 | 39 | 0.299 (0.30–0.30) | 0.473 | 0.036 | 0.318 |
| value | turn | raw | agglo | k=50 | 50 | 0 | 0.380 (0.38–0.38) | 0.587 | 0.212 | 0.351 |
| value | turn | umap5 | kmeans | k=35 | 35 | 0 | 0.299 (0.29–0.31) | 0.580 | 0.206 | 0.397 |
| value | value | raw | hdbscan | mcs=10,eom,ms=1 | 13 | 30 | 0.393 (0.39–0.39) | 0.612 | 0.201 | 0.372 |
| value | value | raw | agglo | thr=0.4 | 91 | 0 | 0.520 (0.52–0.52) | 0.722 | 0.349 | 0.543 |
| value | value | raw | kmeans | k=20 | 20 | 0 | 0.397 (0.38–0.41) | 0.656 | 0.298 | 0.407 |
| value | window | umap5 | hdbscan | mcs=10,eom,ms=1 | 15 | 6 | 0.327 (0.32–0.33) | 0.567 | 0.234 | 0.318 |
| value | window | raw | agglo | k=50 | 50 | 0 | 0.365 (0.36–0.36) | 0.599 | 0.240 | 0.351 |
| value | window | umap5 | kmeans | k=20 | 20 | 0 | 0.307 (0.29–0.32) | 0.568 | 0.224 | 0.344 |

## At the gold number of clusters (raw vectors)

| Unit | Variant | Space | Method | Setting | K | Noise % | B-cubed F1 (range) | NMI | ARI | Purity |
|---|---|---|---|---|---|---|---|---|---|---|
| chroma | segment | raw | agglo | k=5 | 5 | 0 | 0.367 (0.37–0.37) | 0.070 | 0.013 | 0.350 |
| chroma | segment | raw | kmeans | k=5 | 5 | 0 | 0.458 (0.43–0.51) | 0.376 | 0.260 | 0.580 |
| oracle_seg | segment | raw | agglo | k=5 | 5 | 0 | 0.796 (0.80–0.80) | 0.786 | 0.642 | 0.753 |
| oracle_seg | segment | raw | kmeans | k=5 | 5 | 0 | 0.837 (0.81–0.87) | 0.823 | 0.765 | 0.914 |
| value | turn | raw | agglo | k=35 | 35 | 0 | 0.335 (0.33–0.33) | 0.554 | 0.197 | 0.286 |
| value | turn | raw | kmeans | k=35 | 35 | 0 | 0.284 (0.27–0.29) | 0.558 | 0.190 | 0.377 |
| value | value | raw | agglo | k=35 | 35 | 0 | 0.339 (0.34–0.34) | 0.489 | 0.067 | 0.284 |
| value | value | raw | kmeans | k=35 | 35 | 0 | 0.375 (0.36–0.39) | 0.657 | 0.277 | 0.462 |
| value | window | raw | agglo | k=35 | 35 | 0 | 0.341 (0.34–0.34) | 0.573 | 0.231 | 0.302 |
| value | window | raw | kmeans | k=35 | 35 | 0 | 0.289 (0.28–0.30) | 0.561 | 0.199 | 0.373 |
