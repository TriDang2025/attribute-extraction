"""Schema Coherence Score (paper Section 4.3.3, Eq. 18-19).

sc_s(z, S) = prod_i Prob(tkn_i(z) | SP(S) + tkn_:i-1(z)), with tkn(z) = Tokenizer(z) +
Tokenizer(","). Following Section 6.1.2, the score is computed under 10 random orderings
of the known attributes in the Schema Prefix and the maximum is kept.

The backbone is the same Llama-3-8B-Instruct GGUF file LM Studio serves, run by a
llama.cpp server (tools/llama.cpp, port 8081), because LM Studio returns probabilities only
for tokens it samples. Each candidate's canonical token ids are forced with a token-id
grammar; with top-k, top-p and min-p off, the server reports each forced token's
log-probability under the unmodified next-token distribution.
"""

import json
import math
import random
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Sequence

from .prompts import schema_prefix


class CoherenceScorer:
    def __init__(self, base_url: str = "http://localhost:8081", workers: int = 4, timeout: float = 600) -> None:
        self.base_url = base_url.rstrip("/")
        self.workers = workers
        self.timeout = timeout

    def _post(self, path: str, payload: Dict) -> Dict:
        request = urllib.request.Request(f"{self.base_url}{path}", data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _tokens(self, text: str) -> List[int]:
        return self._post("/tokenize", {"content": text})["tokens"]

    def _candidate_tokens(self, prefix: str, prefix_ids: List[int], candidate: str) -> List[int]:
        full = self._tokens(prefix + " " + candidate + ",")
        if len(full) <= len(prefix_ids) or full[: len(prefix_ids)] != prefix_ids:
            raise ValueError(f"tokenization of {candidate!r} does not extend the schema prefix")
        return full[len(prefix_ids):]

    def _log_prob(self, prefix: str, tokens: List[int]) -> float:
        grammar = "root ::= " + " ".join(f"<[{t}]>" for t in tokens)
        result = self._post("/completion", {
            "prompt": prefix, "n_predict": len(tokens), "n_probs": 1, "temperature": 0, "top_k": 0,
            "top_p": 1, "min_p": 0, "grammar": grammar, "cache_prompt": True})
        probs = result["completion_probabilities"]
        if [p["id"] for p in probs] != tokens:
            raise RuntimeError(f"forced decoding produced {[p['id'] for p in probs]}, expected {tokens}")
        return sum(p["logprob"] for p in probs)

    def log_score(self, prefix: str, candidates: Sequence[str]) -> Dict[str, float]:
        """log sc_s for each candidate after one prefix (the tokens ' <name>,')."""
        prefix_ids = self._tokens(prefix)
        tokens = {c: self._candidate_tokens(prefix, prefix_ids, c) for c in candidates}
        with ThreadPoolExecutor(self.workers) as pool:
            values = list(pool.map(lambda c: self._log_prob(prefix, tokens[c]), candidates))
        return dict(zip(candidates, values))

    def score(self, dataset: str, schema: Sequence[str], candidates: Sequence[str],
              permutations: int = 10, seed: int = 0) -> Dict[str, float]:
        """Max over random schema orderings of sc_s (probabilities, not logs)."""
        rng = random.Random(seed)
        best = {c: float("-inf") for c in candidates}
        for _ in range(permutations):
            order = list(schema)
            rng.shuffle(order)
            for candidate, value in self.log_score(schema_prefix(dataset, order), candidates).items():
                best[candidate] = max(best[candidate], value)
        return {c: math.exp(v) for c, v in best.items()}
