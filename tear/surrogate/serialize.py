"""
Table serialization and deserialization utilities for the TEAR surrogate model.

Based on Section 4.2.1 of the TEAR paper:
- Special tokens: ⟨m⟩ separates spans in a cell value, ⟨s⟩ separates cells in a row,
  ⟨n⟩ separates rows. Unicode angle brackets keep them distinct from BART's "<s>".
- Seq(A) = a1⟨m⟩a2...; Seq(H) = h1⟨s⟩h2...; Seq(R) = Seq(A1)⟨s⟩Seq(A2)...;
  Seq(D) = Seq(H)⟨n⟩Seq(R1)⟨n⟩Seq(R2)...
- The surrogate model generates the table sequence autoregressively from text.
"""

import re

# Special tokens as defined in the paper
SPAN_SEP = "⟨m⟩"   # separates spans in each value
CELL_SEP = "⟨s⟩"   # separates cells in each row
ROW_SEP = "⟨n⟩"    # separates rows
SPECIAL_TOKENS = [SPAN_SEP, CELL_SEP, ROW_SEP]

_TOKEN_SPLIT_RE = re.compile('|'.join(re.escape(t) for t in (ROW_SEP, CELL_SEP, SPAN_SEP)))
# Leftover BART markers in decoded output.
_MARKER_RE = re.compile(r'</?s>|<pad>|<unk>|<mask>')


def _normalize_cell_value(value):
    """Coerce cell values to a serializable string while preserving span structure."""
    if value is None:
        return ""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return str(value).strip()


def _clean(text):
    return _MARKER_RE.sub('', text).strip()


def _norm(text):
    return " ".join(str(text).lower().split())


def serialize_table(table):
    """
    Serialize a table into the sequence format used to train the surrogate model.

    Args:
        table: Dict with keys:
            'headers': List[str] - list of column header names
            'rows': List[List[cell]] - each cell is a string or a list of span strings
                    (an empty list is an empty cell)

    Returns:
        str: h1⟨s⟩h2...⟨n⟩a11⟨s⟩a12...⟨n⟩...
    """
    headers = table.get('headers', [])
    rows = table.get('rows', [])

    # Serialize header row (Equation 4)
    header_seq = CELL_SEP.join(str(h).strip() for h in headers if str(h).strip())

    # Serialize data rows (Equations 5 and 6)
    row_seqs = []
    for row in rows:
        cell_seqs = []
        for cell in row:
            normalized = _normalize_cell_value(cell)
            if isinstance(normalized, list):
                # Cell is a list of spans (Equation 3)
                cell_seqs.append(SPAN_SEP.join(normalized))
            else:
                cell_seqs.append(normalized)
        row_seqs.append(CELL_SEP.join(cell_seqs))

    if not row_seqs:
        return header_seq
    return header_seq + ROW_SEP + ROW_SEP.join(row_seqs)


def probe_sequence(seq):
    """
    Probe a predicted sequence to obtain header preview and value preview (Section 4.2.1).

    Returns:
        tuple: (header_preview, value_preview)
            header_preview: List[str] - header row (before the first ⟨n⟩) split by ⟨s⟩
            value_preview: List[str] - the rest split by all special tokens, empties dropped
    """
    parts = seq.split(ROW_SEP, 1)
    header_preview = [h for h in (_clean(x) for x in parts[0].split(CELL_SEP)) if h]

    value_preview = []
    if len(parts) > 1:
        for token in _TOKEN_SPLIT_RE.split(parts[1]):
            candidate = _clean(token)
            if candidate:
                value_preview.append(candidate)

    return header_preview, value_preview


def parse_table_sequence(seq):
    """
    Parse a full table sequence back into structured table format.

    Returns:
        dict: {'headers': [...], 'rows': [[cell1, cell2, ...], ...]}
              where each cell is a list of spans
    """
    parts = seq.split(ROW_SEP)

    headers = [h for h in (_clean(x) for x in parts[0].split(CELL_SEP)) if h]

    rows = []
    for row_part in parts[1:]:
        if not row_part.strip():
            continue
        cells = []
        for cell_part in row_part.split(CELL_SEP):
            cells.append([s for s in (_clean(x) for x in cell_part.split(SPAN_SEP)) if s])
        rows.append(cells)

    return {'headers': headers, 'rows': rows}


def _restore_row_separator(seq, header_vocab):
    """Our CPU-trained surrogate sometimes writes ⟨s⟩ where the single ⟨n⟩ after the header
    row belongs. Without any ⟨n⟩, the header row is the leading run of cells that are
    attribute names (header_vocab); the first ⟨s⟩ after it becomes ⟨n⟩."""
    if ROW_SEP in seq or not header_vocab:
        return seq
    vocab = {_norm(h) for h in header_vocab}
    cells = seq.split(CELL_SEP)
    k = 0
    while k < len(cells) and _norm(_clean(cells[k])) in vocab:
        k += 1
    if k == 0 or k == len(cells):
        return seq
    return CELL_SEP.join(cells[:k]) + ROW_SEP + CELL_SEP.join(cells[k:])


def preview_for_schema(seq, schema, header_vocab=None):
    """
    Header and value previews restricted to the schema (H_p must be a subset of S).

    Headers match the schema ignoring case and whitespace and are returned in the
    schema's spelling. Values are kept only from cells whose header (same column
    position) survived the filter. header_vocab (e.g. the dataset's full schema)
    lets a sequence that lacks the row separator be split at the end of its header row.

    Returns:
        tuple: (H_p, V_p) as lists of strings
    """
    by_norm = {}
    for s in schema:
        by_norm.setdefault(_norm(s), s)

    seq = _restore_row_separator(seq, header_vocab)
    parts = seq.split(ROW_SEP)
    # Keep column positions (an empty generated header still occupies a column).
    columns = [by_norm.get(_norm(_clean(h))) for h in parts[0].split(CELL_SEP)]
    header_preview = list(dict.fromkeys(c for c in columns if c))

    value_preview = []
    for row_part in parts[1:]:
        for i, cell_part in enumerate(row_part.split(CELL_SEP)):
            if i >= len(columns) or columns[i] is None:
                continue
            value_preview.extend(s for s in (_clean(x) for x in cell_part.split(SPAN_SEP)) if s)

    return header_preview, value_preview
