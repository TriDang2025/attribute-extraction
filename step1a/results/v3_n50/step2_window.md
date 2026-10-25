# Step 2 with a narrow context window (dev, 50 dialogues)

591 verbatim gold mentions in 50 dialogues (s1a.gold.mentions_for); groups = gold entity, booking = (dialogue, gold entity); type partition, 1965 cannot-link pairs, average linkage, no C6. Vector = alpha * masked turn context + beta * window + (1 - alpha - beta) * normalized string; window = mean of left and right k-word vectors (lr) or one k + target + k vector (sym), both inside the mention's own turn.

**Tuning and scoring use the same 50 dialogues**, so the best row is optimistic.

210 settings (198 with a window); encoding 636s, grid 41s, total 11.3 min. run_best on the chosen cfg gives the same labels: True; run_best on v2_n50/chosen_step2_joint.json gives the reference labels: True.

Stop rule: "clear gain" only if F1 - reference F1 > half-width of the reference's bootstrap 95% CI (0.031).

## 1. Reference (joint setting, no window)

| Setting | P | R | F1 | K | dF1 vs ref | stop rule |
|---|---|---|---|---|---|---|
| no window, alpha=0.5, t=0.45 | 0.801 | 0.805 | 0.803 | 30 | +0.000 | no gain |

Reference bootstrap 95% CI: 0.771-0.833.

Best without a window (beta = 0, same alpha / t grid): no window, alpha=0.2, t=0.55 F1 0.805.

## 2. Top 15 window settings

| Setting | P | R | F1 | K | dF1 vs ref | stop rule |
|---|---|---|---|---|---|---|
| k=2 lr, beta=0.5, alpha=0.2, t=0.35 | 0.832 | 0.829 | 0.831 | 31 | +0.028 | within CI |
| k=2 lr, beta=0.5, alpha=0.2, t=0.45 | 0.832 | 0.829 | 0.831 | 31 | +0.028 | within CI |
| k=2 lr, beta=0.5, alpha=0.2, t=0.55 | 0.832 | 0.829 | 0.831 | 31 | +0.028 | within CI |
| k=2 lr, beta=0.5, alpha=0.0, t=0.35 | 0.820 | 0.822 | 0.821 | 30 | +0.018 | within CI |
| k=2 lr, beta=0.5, alpha=0.0, t=0.45 | 0.820 | 0.822 | 0.821 | 30 | +0.018 | within CI |
| k=2 lr, beta=0.5, alpha=0.0, t=0.55 | 0.820 | 0.822 | 0.821 | 30 | +0.018 | within CI |
| k=2 lr, beta=0.35, alpha=0.2, t=0.35 | 0.818 | 0.821 | 0.819 | 30 | +0.017 | within CI |
| k=2 lr, beta=0.35, alpha=0.2, t=0.45 | 0.818 | 0.821 | 0.819 | 30 | +0.017 | within CI |
| k=2 lr, beta=0.35, alpha=0.2, t=0.55 | 0.818 | 0.821 | 0.819 | 30 | +0.017 | within CI |
| k=2 sym, beta=0.35, alpha=0.0, t=0.45 | 0.820 | 0.819 | 0.819 | 31 | +0.017 | within CI |
| k=2 sym, beta=0.35, alpha=0.0, t=0.55 | 0.817 | 0.819 | 0.818 | 30 | +0.015 | within CI |
| k=2 sym, beta=0.35, alpha=0.2, t=0.35 | 0.813 | 0.814 | 0.814 | 31 | +0.011 | within CI |
| k=2 lr, beta=0.35, alpha=0.0, t=0.45 | 0.817 | 0.810 | 0.813 | 31 | +0.010 | within CI |
| k=2 lr, beta=0.35, alpha=0.0, t=0.55 | 0.817 | 0.810 | 0.813 | 31 | +0.010 | within CI |
| k=3 sym, beta=0.2, alpha=0.0, t=0.55 | 0.816 | 0.810 | 0.813 | 31 | +0.010 | within CI |

## 3. Plateau

6 window settings within 0.01 of the best F1 (0.831). Ranges: k {2}, side {lr}, alpha {0.0, 0.2}, beta {0.5}, t {0.35, 0.45, 0.55}.

## 4. Best setting: k=2 lr, beta=0.5, alpha=0.2, t=0.35

F1 0.831 (bootstrap 95% CI 0.804-0.856), K 31; reference F1 0.803, K 30.

Per-class recall (role-pair classes):

| Class | n | ref | best | delta |
|---|---|---|---|---|
| Train departure | 44 | 0.50 | 0.50 | +0.00 |
| Train destination | 42 | 0.53 | 0.53 | +0.00 |
| Train leave at | 23 | 1.00 | 1.00 | +0.00 |
| Train arrive by | 11 | 1.00 | 1.00 | +0.00 |
| Hotel requested people | 20 | 0.29 | 0.39 | +0.10 |
| Hotel requested stay | 27 | 0.33 | 0.38 | +0.05 |
| Hotel stars | 21 | 0.50 | 0.55 | +0.04 |
| Attraction name | 12 | 0.35 | 0.72 | +0.38 |
| Attraction area | 13 | 0.49 | 0.94 | +0.45 |

Top-10 confused (gold -> cluster majority):

| ref | n | best | n |
|---|---|---|---|
| Train departure -> Train destination | 21 | Train departure -> Train destination | 21 |
| Train destination -> Train departure | 16 | Train destination -> Train departure | 16 |
| Train arrive by -> Train leave at | 11 | Train arrive by -> Train leave at | 11 |
| Attraction name -> Attraction area | 9 | Hotel requested stay -> Hotel stars | 5 |
| Hotel requested people -> Hotel requested stay | 5 | Restaurant name -> Restaurant food | 3 |
| Hotel name -> Hotel type | 4 | Hotel requested people -> Hotel stars | 3 |
| Hotel stars -> Hotel requested stay | 4 | Taxi leave at -> Taxi arrive by | 2 |
| Hotel requested stay -> Hotel stars | 4 | Attraction name -> Attraction type | 2 |
| Attraction name -> Attraction type | 3 | Hotel name -> Hotel type | 2 |
| Restaurant name -> Restaurant price range | 3 | Hotel name -> Hotel area | 2 |

Visible / hidden attributes per TEAR level (F1):

| Subset | n | ref | best |
|---|---|---|---|
| visible_L1 | 553 | 0.798 | 0.831 |
| hidden_L1 | 38 | 0.851 | 0.807 |
| visible_L2 | 462 | 0.785 | 0.824 |
| hidden_L2 | 129 | 0.865 | 0.852 |
| visible_L3 | 397 | 0.805 | 0.817 |
| hidden_L3 | 194 | 0.796 | 0.855 |

## 5. Best per side and per k

| Group | Best setting | F1 | K | dF1 |
|---|---|---|---|---|
| side=lr | k=2 lr, beta=0.5, alpha=0.2, t=0.35 | 0.831 | 31 | +0.028 |
| side=sym | k=2 sym, beta=0.35, alpha=0.0, t=0.45 | 0.819 | 31 | +0.017 |
| k=2 | k=2 lr, beta=0.5, alpha=0.2, t=0.35 | 0.831 | 31 | +0.028 |
| k=3 | k=3 sym, beta=0.2, alpha=0.0, t=0.55 | 0.813 | 31 | +0.010 |
| k=5 | k=5 sym, beta=0.35, alpha=0.2, t=0.45 | 0.812 | 30 | +0.009 |
