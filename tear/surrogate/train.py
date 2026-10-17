"""Fine-tune BART-Large as the TEAR preview surrogate M (Section 4.2.1).

M learns W_l -> Seq(D_l) with standard cross-entropy. Pool rows with
"split": "val" form the early-stopping set (the paper holds out 100); the rest
train. With no "val" rows, training runs a fixed --epochs and keeps the last model.

levels.json (--hidden-schema-file) maps an exploratory level to the attributes
hidden at that level, e.g. {"1": ["Hospital", ...], "2": [...]} or
{"1": {"hidden": [...]}}. Hidden columns are removed from every target table.

Example:
  python -m surrogate.train --pool data/conversation/pool.jsonl --out models/surrogate
"""

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from surrogate.data import drop_hidden, length_batches, load_hidden, load_jsonl, to_model_text  # noqa: E402
from surrogate.serialize import SPECIAL_TOKENS, serialize_table  # noqa: E402

BASE_MODEL = "models/bart-large"  # local copy of facebook/bart-large
WEIGHT_DECAY = 0.01
WARMUP_RATIO = 0.06
MAX_GRAD_NORM = 1.0


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pool", required=True, help="pool JSONL: id, text, table{headers, rows}, optional split")
    p.add_argument("--out", required=True, help="dir for the best checkpoint and train_log.json")
    p.add_argument("--base-model", default=BASE_MODEL,
                   help="local dir with facebook/bart-large (relative paths also resolve from the project root)")
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--patience", type=int, default=2)
    p.add_argument("--lr", type=float, default=3e-5)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--grad-accum", type=int, default=2)
    p.add_argument("--max-source", type=int, default=1024)
    p.add_argument("--max-target", type=int, default=256)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--threads", type=int, default=12)
    p.add_argument("--hidden-schema-file", help="levels.json with hidden attributes per level")
    p.add_argument("--level", type=int, help="exploratory level to hide (needs --hidden-schema-file)")
    args = p.parse_args(argv)
    if (args.hidden_schema_file is None) != (args.level is None):
        p.error("--hidden-schema-file and --level go together")
    base = Path(args.base_model)
    if not base.exists() and (ROOT / base).exists():
        base = ROOT / base
    args.base_model = str(base)
    return args


def log(msg):
    print(msg, flush=True)


def prepare(rows, hidden):
    """Split rows into train/val and attach the serialized target Seq(D)."""
    train, val, skipped = [], [], 0
    for i, row in enumerate(rows):
        split = row.get("split", "train")
        if split not in ("train", "val"):
            skipped += 1
            continue
        item = {
            "id": row.get("id", i),
            "text": row["text"],
            "target": serialize_table(drop_hidden(row["table"], hidden)),
        }
        (val if split == "val" else train).append(item)
    return train, val, skipped


def encode(tok, items, max_source, max_target):
    """Token ids for source and target, truncated with </s> kept. Returns counts of truncations."""
    cut = {"source": 0, "target": 0}
    if not items:
        return [], [], cut
    src = tok([it["text"] for it in items], verbose=False)["input_ids"]
    tgt = tok(text_target=[to_model_text(it["target"]) for it in items], verbose=False)["input_ids"]

    def trim(ids, limit, key):
        if len(ids) > limit:
            cut[key] += 1
            return ids[:limit - 1] + [tok.eos_token_id]
        return ids

    src = [trim(s, max_source, "source") for s in src]
    tgt = [trim(t, max_target, "target") for t in tgt]
    return src, tgt, cut


def collate(torch, idx, src, tgt, pad_id):
    n, s_len, t_len = len(idx), max(len(src[i]) for i in idx), max(len(tgt[i]) for i in idx)
    input_ids = torch.full((n, s_len), pad_id, dtype=torch.long)
    attention = torch.zeros((n, s_len), dtype=torch.long)
    labels = torch.full((n, t_len), -100, dtype=torch.long)
    for row, i in enumerate(idx):
        input_ids[row, :len(src[i])] = torch.tensor(src[i])
        attention[row, :len(src[i])] = 1
        labels[row, :len(tgt[i])] = torch.tensor(tgt[i])
    return {"input_ids": input_ids, "attention_mask": attention, "labels": labels}


def batch_loss(model, batch):
    out = model(**batch, use_cache=False)
    return out.loss, int((batch["labels"] != -100).sum())


def evaluate(torch, model, batches, src, tgt, pad_id):
    model.eval()
    total, tokens = 0.0, 0
    with torch.no_grad():
        for idx in batches:
            loss, n = batch_loss(model, collate(torch, idx, src, tgt, pad_id))
            total += loss.item() * n
            tokens += n
    model.train()
    return total / max(tokens, 1)


def main(argv=None):
    args = parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    hidden = load_hidden(args.hidden_schema_file, args.level) if args.hidden_schema_file else set()
    train_items, val_items, skipped = prepare(load_jsonl(args.pool), hidden)
    if not train_items:
        raise SystemExit("no training rows in pool")
    has_val = bool(val_items)
    log(f"pool: {len(train_items)} train, {len(val_items)} val, {skipped} skipped (other split)"
        + (f"; level {args.level} hides {len(hidden)} attributes" if hidden else ""))
    if not has_val:
        log(f"no val rows: training a fixed {args.epochs} epochs, no early stopping")

    t_import = time.time()
    import torch
    from transformers import AutoTokenizer, BartForConditionalGeneration
    from transformers.optimization import get_linear_schedule_with_warmup

    torch.set_num_threads(args.threads)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)

    tok = AutoTokenizer.from_pretrained(args.base_model, local_files_only=True)
    tok.add_special_tokens({"additional_special_tokens": SPECIAL_TOKENS})
    # The checkpoint stores fp16 weights; train in fp32 (fp16 matmuls are very slow on CPU).
    model = BartForConditionalGeneration.from_pretrained(args.base_model, local_files_only=True,
                                                         dtype=torch.float32)
    model.resize_token_embeddings(len(tok))
    # Table sequences repeat n-grams (separators, repeated cells): no n-gram blocking.
    model.generation_config.no_repeat_ngram_size = 0
    model.train()
    log(f"loaded {args.base_model} in {time.time() - t_import:.1f}s; vocab {len(tok)}; threads {torch.get_num_threads()}")

    tr_src, tr_tgt, tr_cut = encode(tok, train_items, args.max_source, args.max_target)
    va_src, va_tgt, va_cut = encode(tok, val_items, args.max_source, args.max_target)
    pad_id = tok.pad_token_id
    tr_len = [(len(s), len(t)) for s, t in zip(tr_src, tr_tgt)]
    va_batches = length_batches([(len(s), len(t)) for s, t in zip(va_src, va_tgt)], args.batch_size)
    log(f"train tokens/sample: source mean {sum(a for a, _ in tr_len) / len(tr_len):.0f} max {max(a for a, _ in tr_len)}, "
        f"target mean {sum(b for _, b in tr_len) / len(tr_len):.0f} max {max(b for _, b in tr_len)}; "
        f"truncated train {tr_cut}, val {va_cut}")

    steps_per_epoch = math.ceil(len(train_items) / args.batch_size)
    updates_per_epoch = math.ceil(steps_per_epoch / args.grad_accum)
    total_updates = updates_per_epoch * args.epochs
    no_decay = ["bias", "layer_norm.weight", "layernorm_embedding.weight"]
    params = [
        {"params": [p for n, p in model.named_parameters() if not any(d in n for d in no_decay)], "weight_decay": WEIGHT_DECAY},
        {"params": [p for n, p in model.named_parameters() if any(d in n for d in no_decay)], "weight_decay": 0.0},
    ]
    optimizer = torch.optim.AdamW(params, lr=args.lr)
    scheduler = get_linear_schedule_with_warmup(optimizer, int(WARMUP_RATIO * total_updates), total_updates)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    record = {
        "args": vars(args), "special_tokens": SPECIAL_TOKENS,
        "n_train": len(train_items), "n_val": len(val_items), "hidden": sorted(hidden),
        "truncated": {"train": tr_cut, "val": va_cut}, "steps_per_epoch": steps_per_epoch,
        "epochs": [], "best_epoch": None, "best_val_loss": None, "estimated_epoch_seconds": None,
    }

    def write_log():
        (out / "train_log.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf8")

    def save():
        t = time.time()
        model.save_pretrained(out)
        tok.save_pretrained(out)
        log(f"  saved checkpoint to {out} ({time.time() - t:.1f}s)")

    best, bad = float("inf"), 0
    train_start = time.time()
    for epoch in range(1, args.epochs + 1):
        batches = length_batches(tr_len, args.batch_size, rng)
        t0 = time.time()
        total, tokens = 0.0, 0
        optimizer.zero_grad()
        for step, idx in enumerate(batches, 1):
            group_start = (step - 1) // args.grad_accum * args.grad_accum
            group_size = min(args.grad_accum, len(batches) - group_start)
            loss, n = batch_loss(model, collate(torch, idx, tr_src, tr_tgt, pad_id))
            (loss / group_size).backward()
            total += loss.item() * n
            tokens += n
            if step - group_start == group_size:
                torch.nn.utils.clip_grad_norm_(model.parameters(), MAX_GRAD_NORM)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
            if epoch == 1 and step == min(20, len(batches)):
                per_step = (time.time() - t0) / step
                est = per_step * len(batches) + (per_step / 3) * len(va_batches)
                record["estimated_epoch_seconds"] = round(est, 1)
                log(f"  {per_step:.2f}s/step over {step} steps -> estimated {est / 60:.1f} min/epoch "
                    f"({len(batches)} train steps + {len(va_batches)} val batches)")
            elif step % 10 == 0:
                log(f"  epoch {epoch} step {step}/{len(batches)} loss {total / tokens:.4f} "
                    f"{(time.time() - t0) / step:.2f}s/step")
        train_loss = total / max(tokens, 1)
        train_secs = time.time() - t0
        val_loss = evaluate(torch, model, va_batches, va_src, va_tgt, pad_id) if has_val else None
        secs = time.time() - t0
        entry = {"epoch": epoch, "train_loss": round(train_loss, 5),
                 "val_loss": None if val_loss is None else round(val_loss, 5),
                 "seconds": round(secs, 1), "train_seconds": round(train_secs, 1),
                 "sec_per_step": round(train_secs / len(batches), 2), "lr": scheduler.get_last_lr()[0]}
        record["epochs"].append(entry)
        log(f"epoch {epoch}: train_loss {train_loss:.4f}"
            + (f" val_loss {val_loss:.4f}" if has_val else "") + f" ({secs:.0f}s)")

        stop = False
        if has_val:
            if val_loss < best:
                best, bad = val_loss, 0
                record["best_epoch"], record["best_val_loss"] = epoch, round(val_loss, 5)
                save()
            else:
                bad += 1
                stop = bad >= args.patience
                if stop:
                    log(f"early stop: no val improvement for {bad} epochs (best epoch {record['best_epoch']})")
        elif epoch == args.epochs:
            record["best_epoch"] = epoch
            save()
        write_log()
        if stop:
            break

    record["total_seconds"] = round(time.time() - train_start, 1)
    write_log()
    log(f"done in {record['total_seconds'] / 60:.1f} min; checkpoint (epoch {record['best_epoch']}) in {out}")


if __name__ == "__main__":
    main()
