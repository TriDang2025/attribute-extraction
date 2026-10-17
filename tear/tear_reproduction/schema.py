"""Dataset schemas (paper Table 6), dataset descriptions (Appendix A.1), and conversion
between tables and the entity-grouped JSON the LLM reads and writes.

A table is {"headers": [...], "rows": [[cell, ...], ...]} where a cell is a list of exact
text spans (an empty list is an empty cell). In JSON form a table is
{"<Entity>": {"0": {"<attribute>": [spans], ...}, "1": {...}}, ...}.
Incidents and Weather tables have one record per entity instance; a Conversation table
has a single record that covers every entity (paper Table 5, "Multiple").
"""

from typing import Any, Dict, List, Optional, Sequence

DATASETS: Dict[str, Dict[str, Any]] = {
    "Incidents": {
        "entities": {
            "Accident": ["Accident type", "Accident date", "Accident address", "Number of rounds fired",
                         "Accident number", "Personnel arrived time"],
            "Victim": ["Victim number", "Victim status", "Victim gender", "Victim age", "Victim based",
                       "Hospital name", "Victim name", "Victim race", "Victim occupation", "Victim vehicle"],
            "Suspect": ["Suspect gender", "Suspect number", "Suspect status", "Suspect age", "Suspect name",
                        "Suspect description", "Suspect weapon", "Suspect vehicle", "Suspect occupation",
                        "Suspect based", "Suspect race", "Prison name"],
        },
        "multiple": {"Accident": False, "Victim": True, "Suspect": True},
        "single_record": False,
        "description": "Incidents- There can be three types of entities mentioned in the texts: Accident, "
                       "Victim, and Suspect. There is at most one Accident in the text. There can be multiple "
                       "Victims or Suspects in the text.",
        "sp_description": "criminal incidents or accidents, particularly those involving violence, such as "
                          "shootings or other crimes. The attributes are organized into three main entities: "
                          "the accident itself, the victims, and the suspects.",
        "shots": 5,
    },
    "Weather": {
        "entities": {
            "Weather": ["Temperature", "Snow status", "Cloud type", "Sunset time", "Rain status", "Weather area",
                        "Time", "Weather type", "Wind speed", "Weather compass direction", "Maximum temperature",
                        "Weather frequency", "Wind status", "Minimum temperature", "Sunrise time",
                        "Weather occurring chance", "Wind direction", "Location", "Cloud status"],
        },
        "multiple": {"Weather": True},
        "single_record": False,
        "description": "Weather- There is one type of entity mentioned in the texts: Weather. There can be "
                       "multiple Weather in the text.",
        "sp_description": "weather conditions from news reports, particularly those about location, time, "
                          "temperature, wind, cloud, rain, and snow. The attributes are organized into one main "
                          "entity: the Weather itself",
        "shots": 5,
    },
    "Conversation": {
        "entities": {
            "Attraction": ["Attraction name", "Attraction area", "Attraction type"],
            "Hotel": ["Hotel name", "Hotel area", "Hotel type", "Hotel parking", "Hotel price range",
                      "Hotel internet", "Hotel stars", "Hotel requested day", "Hotel requested people",
                      "Hotel requested stay", "Hotel confirmed name", "Hotel confirmed reference"],
            "Restaurant": ["Restaurant name", "Restaurant area", "Restaurant food", "Restaurant price range",
                           "Restaurant requested day", "Restaurant requested people", "Restaurant requested time",
                           "Restaurant confirmed name", "Restaurant confirmed reference"],
            "Taxi": ["Taxi departure", "Taxi destination", "Taxi leave at", "Taxi arrive by"],
            "Train": ["Train departure", "Train destination", "Train day", "Train leave at", "Train arrive by",
                      "Train requested people", "Train confirmed reference"],
        },
        "multiple": {"Attraction": False, "Hotel": False, "Restaurant": False, "Taxi": False, "Train": False},
        "single_record": True,
        "description": "Conversation- Each input text is a multi-turn dialogue, involving at most 5 entities: "
                       "Attraction, Hotel, Restaurant, Taxi, and Train. You should only extract the final "
                       "agreed-upon state after each turn, covering all confirmed domains and their relevant "
                       "attributes.",
        "sp_description": "multi-turn dialogues, particularly those booking a service. The attributes are "
                          "organized into five main entities: Attraction, Hotel, Restaurant, Taxi, and Train.",
        "shots": 3,
    },
}


def config(dataset: str) -> Dict[str, Any]:
    if dataset not in DATASETS:
        raise ValueError(f"unknown dataset {dataset!r}; expected one of {sorted(DATASETS)}")
    return DATASETS[dataset]


def full_schema(dataset: str) -> List[str]:
    return [a for attrs in config(dataset)["entities"].values() for a in attrs]


def _norm(text: str) -> str:
    return " ".join(str(text).split()).lower()


def entity_of(attribute: str, dataset: str) -> str:
    """Entity of a known attribute; otherwise the entity whose name prefixes it; else the first."""
    entities = config(dataset)["entities"]
    for entity, attrs in entities.items():
        if _norm(attribute) in {_norm(a) for a in attrs}:
            return entity
    for entity in entities:
        if _norm(attribute).startswith(_norm(entity)):
            return entity
    return next(iter(entities))


def spans(cell: Any) -> List[str]:
    if cell is None:
        return []
    if isinstance(cell, list):
        out = []
        for item in cell:
            out.extend(spans(item))
        return out
    if isinstance(cell, dict):
        return []
    text = str(cell).strip()
    return [text] if text else []


# ---------------------------------------------------------------------------
# table <-> entity JSON
# ---------------------------------------------------------------------------

def table_to_json(table: Dict[str, Any], dataset: str) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    """Group each record's non-empty cells by entity; each group is one entity instance."""
    out: Dict[str, Dict[str, Dict[str, List[str]]]] = {}
    for row in table.get("rows", []):
        groups: Dict[str, Dict[str, List[str]]] = {}
        for header, cell in zip(table.get("headers", []), row):
            values = spans(cell)
            if values:
                groups.setdefault(entity_of(header, dataset), {})[header] = values
        for entity in config(dataset)["entities"]:
            if entity in groups:
                instances = out.setdefault(entity, {})
                instances[str(len(instances))] = groups[entity]
        for entity, attrs in groups.items():  # attributes of entities outside the config
            if entity not in config(dataset)["entities"]:
                instances = out.setdefault(entity, {})
                instances[str(len(instances))] = attrs
    return out


def _instances(value: Any) -> List[Dict[str, Any]]:
    """Accept {"0": {...}, "1": {...}}, [{...}, ...] or a bare {attribute: value} dict."""
    if isinstance(value, list):
        return [v for v in value if isinstance(v, dict)]
    if not isinstance(value, dict):
        return []
    if value and all(isinstance(v, dict) for v in value.values()):
        return list(value.values())
    return [value]


def _lift_entities(obj: Dict[str, Any], dataset: str) -> Dict[str, Any]:
    """Move an entity block that a missing brace nested inside another entity back to the
    top level (e.g. {"Victim": {"0": {...}, "Suspect": {...}}})."""
    names = set(config(dataset)["entities"])
    out: Dict[str, Any] = {}
    for entity, value in obj.items():
        if isinstance(value, dict):
            inner = {k: v for k, v in value.items() if k in names and k != entity and isinstance(v, dict)}
            if inner:
                value = {k: v for k, v in value.items() if k not in inner}
                for k, v in _lift_entities(inner, dataset).items():
                    out.setdefault(k, v)
        out.setdefault(entity, value)
    return out


def json_to_table(obj: Dict[str, Any], dataset: str, schema: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Records from entity JSON. Header order follows `schema`, then first appearance.
    Attributes outside the schema are kept: the evaluator scores whatever the model output."""
    if not isinstance(obj, dict):
        raise ValueError("extraction output must be a JSON object keyed by entity")
    obj = _lift_entities(obj, dataset)
    records: List[Dict[str, List[str]]] = []
    for entity, value in obj.items():
        for instance in _instances(value):
            record = {}
            for attribute, cell in instance.items():
                if isinstance(attribute, str) and attribute.strip() and spans(cell):
                    record[attribute.strip()] = list(dict.fromkeys(spans(cell)))
            if record:
                records.append(record)
    if config(dataset)["single_record"] and records:
        merged: Dict[str, List[str]] = {}
        for record in records:
            for attribute, values in record.items():
                merged[attribute] = list(dict.fromkeys(merged.get(attribute, []) + values))
        records = [merged]
    order = list(schema or [])
    seen = {_norm(h): h for h in order}
    headers: List[str] = []
    for header in order:
        if any(header in r for r in records):
            headers.append(header)
    for record in records:
        for attribute in record:
            canonical = seen.get(_norm(attribute), attribute)
            if canonical not in headers:
                headers.append(canonical)
    rows = []
    for record in records:
        by_norm = {_norm(a): v for a, v in record.items()}
        rows.append([by_norm.get(_norm(h), []) for h in headers])
    return {"headers": headers, "rows": rows}


def project(table: Dict[str, Any], keep: Sequence[str]) -> Dict[str, Any]:
    """Keep only the given columns and drop records left empty (hidden attributes, Sec. 5.1)."""
    allowed = {_norm(h) for h in keep}
    idx = [i for i, h in enumerate(table["headers"]) if _norm(h) in allowed]
    rows = [[row[i] for i in idx] for row in table["rows"]]
    rows = [row for row in rows if any(spans(c) for c in row)]
    return {"headers": [table["headers"][i] for i in idx], "rows": rows}


def schema_json_text(schema: Sequence[str], dataset: str, empty: bool = True) -> str:
    """The '{schema in json}' / DI structure: entities with instance "0" (and "1":{...}, ...
    for entities that may repeat), attributes mapped to empty lists."""
    cfg = config(dataset)
    by_entity: Dict[str, List[str]] = {}
    for attribute in schema:
        by_entity.setdefault(entity_of(attribute, dataset), []).append(attribute)
    lines = ["{"]
    entities = [e for e in cfg["entities"] if e in by_entity] + [e for e in by_entity if e not in cfg["entities"]]
    for e_index, entity in enumerate(entities):
        lines.append(f'"{entity}": {{')
        lines.append('"0":{')
        attrs = by_entity[entity]
        for a_index, attribute in enumerate(attrs):
            comma = "," if a_index < len(attrs) - 1 else ""
            lines.append(f'"{attribute}": []{comma}')
        if cfg["multiple"].get(entity, False):
            lines.append("},")
            lines.append('"1":{...},')
            lines.append("...")
        else:
            lines.append("}")
        lines.append("}," if e_index < len(entities) - 1 else "}")
    lines.append("}")
    return "\n".join(lines)


def discovery_structure_text(dataset: str) -> str:
    """The DI output structure with placeholder new attributes (Appendix A.1)."""
    cfg = config(dataset)
    lines = ["{"]
    for entity in cfg["entities"]:
        lines.append(f'"{entity}": {{')
        lines.append('"0":{')
        lines.append('"<new attribute 1>": [],')
        lines.append('"<new attribute 2>": []')
        if cfg["multiple"].get(entity, False):
            lines.append("},")
            lines.append('"1":{...},')
            lines.append("...")
        else:
            lines.append("}")
        lines.append("},")
    lines.append("}")
    return "\n".join(lines)
