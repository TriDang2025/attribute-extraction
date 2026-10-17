"""Hybrid Integration Strategy (paper Section 4.3.2, Appendix A.2-A.4).

- Diversity checking: Vendi score (Eq. 23) on K(a, b) = (chrF(a, b) + chrF(b, a)) / 2,
  div(p) = max over subsets (Eq. 15), low-diversity sets P* below 1 + delta (Eq. 16),
  found with the pruned bottom-up search of Algorithm 2.
- Contextualized analysis: an LLM definition per proposal (A.4), then the Judge
  Instruction (Eq. 17) on each set chosen by the breadth-first greedy iteration
  (Algorithm 1).

Two points Algorithm 1 leaves implicit are made explicit here:
- Proposals that are in no low-diversity set (or survive every judgment) are kept: the
  remaining elements of B join Z' before Z' \\ S (line 23 implies Z' may hold them).
- A cover set whose remaining part has one element or none is retired from P*, so the
  outer loop always ends.
"""

import itertools
import math
from typing import Any, Callable, Dict, FrozenSet, Iterable, List, Optional, Sequence, Set

import numpy as np

from eval.metrics import chrf
from .data import parse_json_object
from .prompts import definition_prompt, judge_prompt


def kernel(a: str, b: str) -> float:
    return 1.0 if a == b else (chrf(a, b) + chrf(b, a)) / 2


def vendi_score(items: Sequence[str], k: Callable[[str, str], float] = kernel) -> float:
    """Eq. 23: exp(-tr(K/n log K/n)) = exp of the entropy of the eigenvalues of K/n."""
    n = len(items)
    if n == 0:
        return 0.0
    matrix = np.array([[k(a, b) for b in items] for a in items], dtype=float) / n
    eigenvalues = np.clip(np.linalg.eigvalsh((matrix + matrix.T) / 2), 0.0, None)
    eigenvalues = eigenvalues[eigenvalues > 1e-12]
    return float(math.exp(-np.sum(eigenvalues * np.log(eigenvalues))))


def diversity_threshold(schema: Sequence[str], k: Callable[[str, str], float] = kernel) -> float:
    """Eq. 16: 1 + delta = min over distinct schema pairs of div({s_i, s_j})."""
    pairs = list(itertools.combinations(dict.fromkeys(schema), 2))
    if not pairs:
        return 1.0
    return min(vendi_score([a, b], k) for a, b in pairs)


def low_diversity_sets(elements: Sequence[str], threshold: float,
                       k: Callable[[str, str], float] = kernel, max_size: int = 8) -> List[FrozenSet[str]]:
    """Algorithm 2: grow qualified sets one element at a time; a set of size len+1 is
    checked only when all of its size-len subsets are qualified (div is monotonic)."""
    universe = list(dict.fromkeys(elements))
    cache: Dict[FrozenSet[str], float] = {}

    def vds(p: FrozenSet[str]) -> float:
        if p not in cache:
            cache[p] = vendi_score(sorted(p), k)
        return cache[p]

    branches: Dict[FrozenSet[str], Set[str]] = {frozenset([e]): set(universe) - {e} for e in universe}
    found: List[FrozenSet[str]] = []
    size = 1
    while branches and size < min(len(universe), max_size):
        next_branches: Dict[FrozenSet[str], Set[str]] = {}
        for p, candidates in branches.items():
            for z_new in candidates:
                extended = p | {z_new}
                if extended in next_branches:
                    continue
                valid, active = True, set(candidates)
                for z in p:
                    sibling = (p - {z}) | {z_new}
                    if sibling in branches:
                        active &= branches[sibling]
                    else:
                        valid = False
                        break
                if valid and vds(extended) < threshold:
                    found.append(extended)
                    next_branches[extended] = active - extended
        branches = next_branches
        size += 1
    return found


class HybridIntegrator:
    def __init__(self, client: Any, dataset: str, schema: Sequence[str],
                 coherence: Dict[str, float], max_contexts: int = 3, max_attempts: int = 3) -> None:
        self.client = client
        self.dataset = dataset
        self.schema = list(schema)
        self.coherence = coherence
        self.max_contexts = max_contexts
        self.max_attempts = max_attempts
        self.definitions: Dict[str, str] = {}
        self.log: List[Dict[str, Any]] = []

    def define(self, name: str, contexts: Sequence[Dict[str, Any]]) -> str:
        """Appendix A.4; contexts are capped at max_contexts texts to bound prompt length."""
        if name in self.definitions:
            return self.definitions[name]
        prompt = definition_prompt(name, list(contexts)[: self.max_contexts], self.dataset)
        definition = name
        for _ in range(self.max_attempts):
            try:
                obj = parse_json_object(self.client.chat(None, prompt, max_tokens=200), "definition")
                values = [v for v in obj.values() if isinstance(v, str) and v.strip()]
                if values:
                    definition = values[0].strip()
                    break
            except (ValueError, RuntimeError):
                continue
        self.definitions[name] = definition
        return definition

    def judge(self, names: Sequence[str], contexts: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Eq. 17: True when the LLM answers "One" (the concepts should be merged)."""
        proposals = [{"name": n, "definition": self.define(n, contexts.get(n, []))} for n in names]
        prompt = judge_prompt(self.schema, proposals)
        answer = None
        for _ in range(self.max_attempts):
            reply = self.client.chat(None, prompt, max_tokens=8).strip().strip('."\' ').lower()
            if reply.startswith("one") or reply == "1":
                answer = True
            elif reply.startswith("two") or reply == "2":
                answer = False
            if answer is not None:
                break
        answer = bool(answer)
        self.log.append({"set": list(names), "merge": answer})
        return answer

    def integrate(self, proposals: Sequence[str], contexts: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Algorithm 1 over Z (proposals) and S (schema); returns Z' and statistics."""
        schema_set = set(self.schema)
        z = [p for p in dict.fromkeys(proposals) if p not in schema_set]
        threshold = diversity_threshold(self.schema)
        p_star = low_diversity_sets(z + self.schema, threshold)
        b: Set[str] = set(z) | schema_set
        kept: Set[str] = set()
        active: List[FrozenSet[str]] = list(p_star)
        calls = 0
        while b and active:
            active = [p for p in active if len(p & b) > 1]
            if not active:
                break
            remaining, cover = set(b), []
            while remaining:
                best = max(active, key=lambda p: (len(p & remaining), sorted(p)))
                if not best & remaining:
                    break
                cover.append(best)
                remaining -= best
            for q_full in cover:
                if q_full not in active:
                    continue
                q = q_full & b
                if len(q) <= 1:
                    active.remove(q_full)
                    continue
                calls += 1
                if self.judge(sorted(q), contexts):
                    if not q & schema_set:
                        kept.add(max(sorted(q), key=lambda name: self.coherence.get(name, float("-inf"))))
                    b -= q
                    active = [p for p in active if not p & q]
                else:
                    active.remove(q_full)
        result = (kept | b) - schema_set
        return {
            "candidates": [p for p in z if p in result],
            "proposal_count": len(z),
            "low_diversity_sets": len(p_star),
            "largest_set": max((len(p) for p in p_star), default=0),
            "llm_calls": calls,
            "threshold": threshold,
        }
