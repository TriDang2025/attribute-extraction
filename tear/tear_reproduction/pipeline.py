"""TEAR inference: Table Extraction Workflow and the per-text Discovery Mechanism.

Corpus-level steps of the Attribute Recommendation Workflow (integration and ranking over
the proposals of all texts) are in integration.py and coherence.py.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Sequence

from .data import parse_json_object, validate_example, validate_headers
from .prompts import discovery_prompt, extraction_prompt
from .retrieval import _norm, _top_k, discovery_examples, rank_examples, semantic_utilities
from .schema import json_to_table, project, spans


PLACEHOLDER = re.compile(r"^[<⟨\s]*new attribute\s*\d*[>⟩\s]*$", re.IGNORECASE)


class TearPipeline:
    def __init__(
        self,
        client: Any,
        labeled_pool: Sequence[Dict[str, Any]],
        dataset: str,
        schema: Sequence[str],
        shots: int,
        retrieval: str = "tear",
        embedder: Optional[Any] = None,
        max_attempts: int = 3,
        max_prompt_chars: int = 24000,
    ) -> None:
        # About 6,000 Llama-3 tokens: leaves room for the reply in the 8,192-token context.
        # Longest demonstrations are dropped only when a prompt would not fit (not in the paper).
        self.max_prompt_chars = max_prompt_chars
        if not labeled_pool:
            raise ValueError("The labeled pool must contain at least one example")
        if retrieval not in ("tear", "rag"):
            raise ValueError("retrieval must be 'tear' or 'rag'")
        if shots < 0 or max_attempts < 1:
            raise ValueError("shots must be >= 0 and max_attempts >= 1")
        self.client = client
        self.dataset = dataset
        self.schema = validate_headers(schema)
        # Attributes outside the (heuristic) schema are hidden from the system (Sec. 5.1).
        self.pool = []
        for index, item in enumerate(labeled_pool):
            example = validate_example(item, f"labeled_pool[{index}]")
            self.pool.append({"text": example["text"], "table": project(example["table"], self.schema)})
        self.shots = shots
        self.retrieval = retrieval
        self.embedder = embedder
        self.max_attempts = max_attempts
        self.calls: List[Dict[str, Any]] = []

    def _json_call(self, prompt: str, source: str, check: Callable[[Dict[str, Any]], Any]) -> Any:
        """Call the model; on unparseable output retry with the error appended (not in the paper)."""
        user = prompt
        for attempt in range(1, self.max_attempts + 1):
            reply = self.client.chat(None, user)
            try:
                result = check(parse_json_object(reply, source))
                self.calls.append({"stage": source, "attempts": attempt})
                return result
            except ValueError as error:
                if attempt == self.max_attempts:
                    self.calls.append({"stage": source, "attempts": attempt, "failed": True, "reply": reply[:3000]})
                    raise
                user = f"{prompt}\n\nYour previous reply was invalid: {error}. Output only the JSON data."

    def _semantic(self, text: str):
        return semantic_utilities(text, self.pool, self.embedder)

    def extract(
        self,
        text: str,
        header_preview: Optional[Sequence[str]] = None,
        value_preview: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        """Eq. 11-12 (TEAR) or dense top-k retrieval without previews (RAG)."""
        text = text.strip()
        semantic = self._semantic(text)
        if self.retrieval == "rag":
            scores, method = semantic
            demos = [{"index": i, "example": self.pool[i], "utilities": {"semantic": scores[i]}}
                     for i in _top_k(scores, self.shots)]
            hp = vp = None
        else:
            if header_preview is None:
                raise ValueError("TEAR extraction needs surrogate previews (header_preview, value_preview)")
            hp = [h for h in header_preview if _norm(h) in {_norm(s) for s in self.schema}]
            vp = list(value_preview or [])
            demos = rank_examples(text, hp, vp, self.pool, self.shots, schema=self.schema, semantic=semantic)
        examples = [d["example"] for d in demos]
        prompt = extraction_prompt(text, self.schema, self.dataset, examples, hp, vp)
        while len(prompt) > self.max_prompt_chars and len(examples) > 1:
            examples.remove(max(examples, key=lambda e: len(e["text"])))
            prompt = extraction_prompt(text, self.schema, self.dataset, examples, hp, vp)
        table = self._json_call(prompt, "extraction", lambda obj: json_to_table(obj, self.dataset, self.schema))
        return {
            "table": table,
            "preview": None if hp is None else {"headers": hp, "values": vp},
            "demonstration_indices": [d["index"] for d in demos],
            "demonstrations_dropped_for_context": len(demos) - len(examples),
            "retrieval": self.retrieval,
            "semantic_method": semantic[1],
        }

    def discover(self, text: str, table: Dict[str, Any]) -> Dict[str, Any]:
        """Discovery Mechanism (Eq. 13-14): the pseudo-table D_u+ of new attributes."""
        text = text.strip()
        if not table.get("headers"):
            table = {"headers": [], "rows": []}
        demos = discovery_examples(text, self.schema, table, self.pool, self.shots, semantic=self._semantic(text))
        kept = list(demos)
        prompt = discovery_prompt(text, table, self.dataset, kept)
        while len(prompt) > self.max_prompt_chars and len(kept) > 1:
            kept.remove(max(kept, key=lambda e: len(e["text"])))
            prompt = discovery_prompt(text, table, self.dataset, kept)
        def check(obj):
            table_plus = json_to_table(obj, self.dataset)
            # Small models copy the DI's "<new attribute 1>" placeholders instead of naming
            # the attribute; ask again (the retry note is ours, not the paper's).
            if any(PLACEHOLDER.match(h) for h in table_plus["headers"]):
                raise ValueError("replace the placeholder names like <new attribute 1> with meaningful attribute names")
            return table_plus

        pseudo = self._json_call(prompt, "discovery", check)
        known = {_norm(h) for h in self.schema} | {_norm(h) for h in table.get("headers", [])}
        proposals = []
        for j, header in enumerate(pseudo["headers"]):
            if _norm(header) in known:
                continue
            values = list(dict.fromkeys(v for row in pseudo["rows"] for v in spans(row[j])))
            if values:
                proposals.append({"name": header, "values": values})
        return {"pseudo_table": pseudo, "proposals": proposals, "demonstration_count": len(demos),
                "demonstrations_dropped_for_context": len(demos) - len(kept)}
