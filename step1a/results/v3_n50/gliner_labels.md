# GLiNER label sets (50 dialogues)

One GLiNER pass per turn (speaker prefix removed). Sets: generic (8 labels, windows of 200 words, 225 s extraction); hand (19 labels, windows of 200 words, 287 s extraction); gold (25 labels, windows of 200 words, 175 s extraction). Gold: 378 verbatim values. Segments 5/25,0.40,on,on; stage 1 k-means k=5 (3 seeds, mean); stage 2 original (t 0.4) or chosen Step 2 (`results/v3_n50/chosen_step2_window.json`, booking = (doc, segment)). Run 24.2 min.

Window check: generic 0 of 782 windows over 512 subtokens at 200 words; hand 0 of 782 windows over 512 subtokens at 200 words; gold 0 of 782 windows over 512 subtokens at 200 words.

## Span finding

| Set | Thr | Spans/dlg | Span precision | Tight recall (range) | Mention recall | Value recall (range) | L1 vis / hid | L2 vis / hid | L3 vis / hid |
|---|---|---|---|---|---|---|---|---|---|
| generic | 0.3 | 28.4 | 0.380 | 0.682 (0.629-0.729) | 0.912 | 0.932 (0.909-0.953) | 0.93 / 1.00 | 0.94 / 0.90 | 0.94 / 0.91 |
| generic | 0.5 | 22.5 | 0.437 | 0.643 (0.593-0.690) | 0.834 | 0.887 (0.856-0.912) | 0.88 / 1.00 | 0.89 / 0.86 | 0.90 / 0.85 |
| hand | 0.3 | 26.8 | 0.417 | 0.663 (0.615-0.707) | 0.948 | 0.962 (0.941-0.981) | 0.96 / 1.00 | 0.97 / 0.92 | 0.99 / 0.90 |
| hand | 0.5 | 18.3 | 0.495 | 0.548 (0.497-0.591) | 0.768 | 0.844 (0.809-0.879) | 0.83 / 1.00 | 0.85 / 0.82 | 0.88 / 0.76 |
| gold | 0.3 | 31.4 | 0.333 | 0.633 (0.587-0.680) | 0.883 | 0.930 (0.909-0.950) | 0.93 / 0.97 | 0.95 / 0.86 | 0.96 / 0.86 |
| gold | 0.5 | 17.5 | 0.422 | 0.448 (0.404-0.492) | 0.623 | 0.716 (0.676-0.758) | 0.71 / 0.79 | 0.72 / 0.70 | 0.80 / 0.55 |

Visible / hidden columns are value recall. Value recall by class at 0.5 (n = verbatim values):

| Class | n | generic | hand | gold |
|---|---|---|---|---|
| Train day | 28 | 1.00 | 1.00 | 1.00 |
| Train destination | 27 | 1.00 | 0.81 | 0.93 |
| Train departure | 26 | 1.00 | 0.81 | 0.92 |
| Restaurant area | 22 | 0.86 | 0.64 | 0.55 |
| Restaurant name | 21 | 0.95 | 0.90 | 0.62 |
| Train confirmed reference | 17 | 1.00 | 1.00 | 0.88 |
| Hotel name | 16 | 1.00 | 1.00 | 0.50 |
| Hotel requested stay | 16 | 0.81 | 0.75 | 0.81 |
| Restaurant food | 16 | 0.44 | 0.94 | 0.81 |
| Train leave at | 16 | 1.00 | 1.00 | 0.81 |
| Train requested people | 16 | 0.56 | 0.44 | 0.50 |
| Hotel confirmed reference | 14 | 1.00 | 1.00 | 0.86 |
| Hotel requested day | 14 | 1.00 | 1.00 | 1.00 |
| Restaurant price range | 14 | 0.57 | 0.71 | 0.71 |
| Hotel requested people | 13 | 0.92 | 1.00 | 0.85 |
| Restaurant confirmed reference | 13 | 1.00 | 1.00 | 0.77 |
| Restaurant requested time | 13 | 1.00 | 0.85 | 0.62 |
| Attraction area | 12 | 0.83 | 0.67 | 0.33 |
| Restaurant requested people | 11 | 0.73 | 0.82 | 0.64 |
| Restaurant requested day | 10 | 1.00 | 1.00 | 1.00 |
| Train arrive by | 10 | 1.00 | 1.00 | 0.50 |
| Attraction name | 8 | 1.00 | 0.38 | 0.12 |
| Attraction type | 8 | 0.75 | 0.25 | 0.25 |
| Hotel stars | 8 | 0.75 | 0.88 | 0.62 |
| Hotel type | 8 | 0.62 | 0.88 | 0.00 |
| Hotel area | 7 | 0.86 | 0.57 | 0.57 |
| Hotel price range | 7 | 0.71 | 0.71 | 0.57 |
| Taxi departure | 4 | 1.00 | 1.00 | 0.75 |
| Taxi destination | 4 | 1.00 | 1.00 | 0.75 |
| Taxi arrive by | 3 | 1.00 | 1.00 | 0.67 |
| Taxi leave at | 2 | 1.00 | 1.00 | 1.00 |

## Values GLiNER generic 0.5 missed

41 of 378 values missed; share recovered by each set and threshold:

| Group | Missed | generic 0.3 | hand 0.3 | hand 0.5 | gold 0.3 | gold 0.5 |
|---|---|---|---|---|---|---|
| all classes | 41 | 0.37 | 0.76 | 0.61 | 0.61 | 0.41 |
| food | 9 | 0.22 | 1.00 | 1.00 | 1.00 | 0.89 |
| type | 5 | 0.20 | 0.40 | 0.40 | 0.20 | 0.00 |
| area | 4 | 0.50 | 0.75 | 0.50 | 0.75 | 0.25 |
| price range | 7 | 0.29 | 0.86 | 0.57 | 0.57 | 0.57 |
| numbers (people/stay/stars) | 15 | 0.47 | 0.67 | 0.47 | 0.47 | 0.20 |

## Two-stage clustering

Attribute B-cubed (lenient) on matched spans; end to end = recall x F1. The LEAKY row runs stage 2 separately inside each (entity group, GLiNER label): the label becomes a clustering feature, and for set gold the labels are the gold slot names, so it is near-oracle. Not a fair pipeline row.

| Set | Thr | Stage 2 | P | R | F1 (range) | K | Value x F1 | Tight x F1 |
|---|---|---|---|---|---|---|---|---|
| generic | 0.3 | original | 0.816 | 0.485 | **0.609** (0.590-0.631) | 239 | 0.567 | 0.415 |
| generic | 0.3 | chosen | 0.712 | 0.400 | **0.512** (0.487-0.535) | 126 | 0.477 | 0.349 |
| generic | 0.3 | **LEAKY: partition by GLiNER label** | 0.757 | 0.352 | **0.481** (0.459-0.498) | 178 | 0.448 | 0.328 |
| generic | 0.5 | original | 0.809 | 0.495 | **0.614** (0.595-0.633) | 223 | 0.545 | 0.395 |
| generic | 0.5 | chosen | 0.759 | 0.466 | **0.577** (0.554-0.600) | 105 | 0.512 | 0.371 |
| generic | 0.5 | **LEAKY: partition by GLiNER label** | 0.777 | 0.407 | **0.535** (0.511-0.555) | 141 | 0.474 | 0.344 |
| hand | 0.3 | original | 0.781 | 0.520 | **0.624** (0.606-0.645) | 241 | 0.600 | 0.414 |
| hand | 0.3 | chosen | 0.737 | 0.407 | **0.524** (0.498-0.544) | 117 | 0.504 | 0.348 |
| hand | 0.3 | **LEAKY: partition by GLiNER label** | 0.794 | 0.287 | **0.422** (0.403-0.445) | 202 | 0.406 | 0.280 |
| hand | 0.5 | original | 0.826 | 0.534 | **0.649** (0.626-0.669) | 205 | 0.548 | 0.356 |
| hand | 0.5 | chosen | 0.748 | 0.500 | **0.600** (0.572-0.622) | 85 | 0.506 | 0.329 |
| hand | 0.5 | **LEAKY: partition by GLiNER label** | 0.815 | 0.342 | **0.482** (0.455-0.506) | 148 | 0.407 | 0.264 |
| gold | 0.3 | original | 0.810 | 0.486 | **0.608** (0.590-0.629) | 248 | 0.565 | 0.385 |
| gold | 0.3 | chosen | 0.718 | 0.427 | **0.535** (0.512-0.559) | 129 | 0.498 | 0.339 |
| gold | 0.3 | **LEAKY: partition by GLiNER label** | 0.798 | 0.342 | **0.479** (0.458-0.504) | 240 | 0.445 | 0.303 |
| gold | 0.5 | original | 0.851 | 0.563 | **0.678** (0.653-0.702) | 178 | 0.485 | 0.304 |
| gold | 0.5 | chosen | 0.764 | 0.514 | **0.614** (0.586-0.639) | 85 | 0.440 | 0.275 |
| gold | 0.5 | **LEAKY: partition by GLiNER label** | 0.801 | 0.437 | **0.565** (0.537-0.591) | 158 | 0.405 | 0.253 |

## Verdict

Rule, fixed in advance: labels are the bottleneck if set hand or gold gains >= 0.10 tight recall or >= 0.05 end to end (value recall x F1, chosen Step 2, not the leaky row) over generic and the bootstrap ranges (dialogue resamples; end-to-end range = product of the recall and F1 bounds) do not overlap; GLiNER is the bottleneck if gold beats generic by < 0.03 tight recall; otherwise unclear. The threshold 0.5 decides; 0.3 is shown for reference.

**Threshold 0.5: GLiNER is the bottleneck** (decisive)

- hand vs generic: tight recall 0.643 -> 0.548 (-0.095, ranges disjoint); end to end 0.512 -> 0.506 (-0.006, ranges overlap).
- gold vs generic: tight recall 0.643 -> 0.448 (-0.195, ranges disjoint); end to end 0.512 -> 0.440 (-0.072, ranges overlap).

**Threshold 0.3: GLiNER is the bottleneck**

- hand vs generic: tight recall 0.682 -> 0.663 (-0.019, ranges overlap); end to end 0.477 -> 0.504 (+0.027, ranges overlap).
- gold vs generic: tight recall 0.682 -> 0.633 (-0.049, ranges overlap); end to end 0.477 -> 0.498 (+0.020, ranges overlap).

