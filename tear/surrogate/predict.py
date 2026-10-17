"""Generate M(W_u) with the trained surrogate and probe it into previews (Section 4.2.1).

Input rows: {"id", "text", "schema"}. Output rows: {"id", "sequence", "header_preview",
"value_preview"}, where the previews come from preview_for_schema(sequence, schema).

Example:
  python -m surrogate.predict --model models/surrogate --input data/samples/input.jsonl --out preview.jsonl
"""

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from surrogate.data import from_model_text, length_batches, load_jsonl, write_jsonl  # noqa: E402
from surrogate.serialize import preview_for_schema, probe_sequence  # noqa: E402


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, help="checkpoint dir written by surrogate.train")
    p.add_argument("--input", required=True, help="JSONL with id, text, schema")
    p.add_argument("--out", required=True, help="output JSONL")
    p.add_argument("--num-beams", type=int, default=4)
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--max-source", type=int, default=1024)
    p.add_argument("--threads", type=int, default=12)
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    rows = load_jsonl(args.input)

    t0 = time.time()
    import torch
    from transformers import AutoTokenizer, BartForConditionalGeneration

    torch.set_num_threads(args.threads)
    tok = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    model = BartForConditionalGeneration.from_pretrained(args.model, local_files_only=True, dtype=torch.float32)
    device = "cuda" if torch.cuda.is_available() else "cpu"  # GPU on Colab; same fp32 weights
    model.to(device).eval()
    print(f"loaded {args.model} on {device} in {time.time() - t0:.1f}s", flush=True)

    src = []
    for ids in tok([r["text"] for r in rows], verbose=False)["input_ids"]:
        src.append(ids if len(ids) <= args.max_source else ids[:args.max_source - 1] + [tok.eos_token_id])
    drop = {tok.pad_token_id, tok.bos_token_id, tok.eos_token_id}

    sequences = [None] * len(rows)
    t_gen = time.time()
    for idx in length_batches([len(s) for s in src], args.batch_size):
        t = time.time()
        width = max(len(src[i]) for i in idx)
        input_ids = torch.full((len(idx), width), tok.pad_token_id, dtype=torch.long)
        attention = torch.zeros((len(idx), width), dtype=torch.long)
        for row, i in enumerate(idx):
            input_ids[row, :len(src[i])] = torch.tensor(src[i])
            attention[row, :len(src[i])] = 1
        with torch.no_grad():
            out = model.generate(
                input_ids=input_ids.to(device), attention_mask=attention.to(device), num_beams=args.num_beams,
                max_new_tokens=args.max_new_tokens, no_repeat_ngram_size=0, early_stopping=True,
            )
        for row, i in enumerate(idx):
            ids = [t_id for t_id in out[row].tolist() if t_id not in drop]
            text = tok.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
            sequences[i] = from_model_text(text)
        print(f"  batch of {len(idx)}: {time.time() - t:.1f}s", flush=True)

    results = []
    for row, seq in zip(rows, sequences):
        schema = row.get("schema")
        header_preview, value_preview = (
            preview_for_schema(seq, schema) if schema is not None else probe_sequence(seq)
        )
        results.append({"id": row.get("id"), "sequence": seq,
                        "header_preview": header_preview, "value_preview": value_preview})
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out, results)
    print(f"wrote {len(results)} rows to {args.out}; generation {time.time() - t_gen:.1f}s "
          f"({(time.time() - t_gen) / max(len(rows), 1):.1f}s/text)", flush=True)


if __name__ == "__main__":
    main()
