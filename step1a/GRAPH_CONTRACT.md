# Step 1a graph tasks: shared data contract

Tasks 0–9 (attribute graph, node signals, filter, draft schema) build on the frozen Step 1a pipeline. Every module codes against this contract. Each module is tested on small toy tables, not on real runs.

## Folder layout
- `results/graph_<split><n>/` holds the files shared by both inputs (e.g. `graph_dev50`, `graph_test50`):
  - `docs.jsonl`: one row per dialogue, `{"dialogue_id", "text", "turns": [[start, end], ...]}` (char spans of turns, from `doc.spans`)
  - `gold_values.csv`: every gold value mention: `dialogue_id, gold_attr, entity_gold, value, char_start, char_end, verbatim` (verbatim True/False; non-verbatim rows have -1 offsets)
  - `gold_attrs.txt`: the 33 gold classes (name and confirmed name merged), one per line
- `results/graph_<split><n>/<input>/`, where `<input>` is `spans` (GLiNER spans) or `gold` (gold values):
  - `mentions.csv`, `clusters.csv`, `instances.csv`, `vectors.npz`: written by Task 0
  - `graphs.pkl`: Task 2
  - `nodes.csv`: Task 3
  - `labels.csv`: Task 4
  - `select/`: Tasks 5–6
  - `schema/`: Tasks 7–8

## mentions.csv (one row per mention)
| column | meaning |
|---|---|
| mention_id | int, 0..n-1, row order |
| input | "spans" or "gold" |
| dialogue_id | str |
| turn | int, index into the dialogue's turns |
| char_start, char_end | int offsets into the dialogue text |
| text | the mention text |
| norm_value | `s1a.step2.normalize(text).lower()` |
| left_word | nearest word to the left inside the same turn, lowercased, punctuation stripped; speaker prefix excluded; "" if none |
| context | ±10 words around the mention inside its turn, plain text |
| cluster_id | str `"<entity>#<k>"` (e.g. `"E2#7"`, `"train#3"`); "" if not clustered |
| entity | `spans`: predicted stage-1 entity `"E0".."E4"`; `gold`: gold entity lowercase (`"train"`, `"hotel"`, ...) |
| entity_gold | gold entity of the mention (gold input: same as entity; spans: entity of the matched gold value, else "") |
| instance_id | entity instance; `spans`: `"<dialogue_id>|<segment index>"`; `gold`: `"<dialogue_id>|<entity>"` |
| gold_attr | gold class of the matched gold value ("" if none; several joined with ";") |
| gliner_score | float; 1.0 for gold |

## clusters.csv (one row per cluster)
`cluster_id, entity, n_mentions, n_values, top_values` (top 5 norm_values by count, joined with "|").

## instances.csv (one row per entity instance, including ones with no mention)
`instance_id, entity, dialogue_id, start_turn, end_turn`
- `spans`: every merged segment is one instance of its predicted entity.
- `gold`: every (dialogue, gold entity) pair present in the gold tables.

## vectors.npz
`mention_id` (int array) and `x` (float32 [n, d], L2-normalised). These are the exact vectors Step 2 clustered on. Steps after Task 0 never call the bge-m3 encoder for new texts; the encoder cache has a single writer.

## Python API (`s1a/mentions.py`, Task 0)
```python
@dataclass
class Export:
    mentions: pd.DataFrame; clusters: pd.DataFrame; instances: pd.DataFrame
    ids: np.ndarray; x: np.ndarray          # vectors.npz
def build(input: str, docs: dict, enc, seed: int = 42) -> Export      # docs: {doc_id: Doc}
def save(e: Export, out_dir: Path) -> None
def load(out_dir: Path) -> Export
def load_shared(run_dir: Path) -> tuple[dict, pd.DataFrame, list[str]]  # docs.jsonl, gold_values, gold_attrs
```
`build` with a subset of docs and another seed is how Task 3 stability re-clusters.

## Labels and pass/fail words
- Node = cluster.
- `labels.csv`: `cluster_id, label, gold_attr, purity, label_by`
  - label ∈ {gold, valid_new, noise, unlabelled}
  - label_by ∈ {rule, model, human}
- Real node = gold or valid_new.
