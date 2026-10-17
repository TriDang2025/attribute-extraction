"""LLM instructions copied from the paper's Appendix A.1 and A.4.

Placeholders are filled in as the paper describes. Formatting the paper leaves open (how
each demonstration is laid out) is kept minimal and noted where it is chosen here.
"""

import json
from typing import Any, Dict, List, Optional, Sequence

from .schema import config, discovery_structure_text, schema_json_text, table_to_json


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


# Demonstration layout is not given in the paper; one "Text / Output" block per example.
def _extraction_examples(examples: Sequence[Dict[str, Any]], dataset: str) -> str:
    return "\n\n".join(
        f"Text: {ex['text']}\nOutput: {_compact(table_to_json(ex['table'], dataset))}" for ex in examples
    )


def extraction_prompt(
    text: str,
    schema: Sequence[str],
    dataset: str,
    examples: Sequence[Dict[str, Any]],
    header_preview: Optional[Sequence[str]] = None,
    value_preview: Optional[Sequence[str]] = None,
) -> str:
    """Extraction Instruction (EI). Hints are left out when no previews are given (RAG)."""
    prompt = (
        "Your task is to analyze the given text, which may be about incidents, weather, or "
        "conversation, and extract the information according to the specified JSON structure below. "
        f"Provide the extracted information in the JSON structure {schema_json_text(schema, dataset)}.\n"
        "Explanations about the JSON structure:\n"
        "- Output only the JSON data.\n"
        "- For each entity, there are multiple attributes.\n"
        "- For each attribute, its value is a list of exact substrings of the input text. You should "
        "consider every attribute listed in the above structure. If an attribute is not present or "
        "cannot be determined, do not include the attribute in the output.\n"
        f"{config(dataset)['description']}\n"
        f"Here are some examples:\n{_extraction_examples(examples, dataset)}\n"
        f"Here is the input text:\n{text}"
    )
    if header_preview is not None:
        prompt += (
            "\nHere are some hints:\n"
            f"The above text is most likely to contain the attributes: {_compact(list(header_preview))}.\n"
            f"The above text is most likely to contain the following values: {_compact(list(value_preview or []))}."
        )
    return prompt


# Demonstration layout is not given in the paper; one "Text / Known / New" block per example.
def _discovery_examples(examples: Sequence[Dict[str, Any]], dataset: str) -> str:
    return "\n\n".join(
        f"Text: {ex['text']}\n"
        f"Known information: {_compact(table_to_json(ex['known_table'], dataset))}\n"
        f"New information: {_compact(table_to_json(ex['new_table'], dataset))}"
        for ex in examples
    )


def discovery_prompt(
    text: str,
    extracted_table: Dict[str, Any],
    dataset: str,
    examples: Sequence[Dict[str, Any]],
) -> str:
    """Discovery Instruction (DI)."""
    return (
        "Your task is to analyze the given text and discover new information mentioned in the text. "
        f"Provide the discovered information in this JSON structure :{discovery_structure_text(dataset)}\n"
        "Explanations about the JSON structure:\n"
        "- Output only the JSON data.\n"
        "- For each entity, there may be multiple attributes.\n"
        "- For each attribute, its value is a list of exact substrings of the input text.\n"
        f"Here are some examples: {_discovery_examples(examples, dataset)}\n"
        "Explanations about the examples:\n"
        "- Given an input text and the known information, you are encouraged to discover new "
        "information for each entity.\n"
        "- The new information is qualified as a new attribute if and only if (1) it is relevant and "
        "important to the domain, (2) it is unique and not overlapped with the known information, and "
        "(3) it has a proper granularity level compared with the known attributes, which means it is "
        "not too high-level or low-level concepts.\n"
        "- The new attribute must have a meaningful name and actual values from the text.\n"
        "- Output qualified new attributes as many as possible.\n"
        f"Here is the input text: {text}\n"
        f"Here is the known information: {_compact(table_to_json(extracted_table, dataset))}"
    )


def schema_prefix(dataset: str, ordered_schema: Sequence[str]) -> str:
    """Schema Prefix (SP) followed by the known attributes, each ending with the separator ','.
    The candidate's tokens ' <name>,' are scored after this text (Eq. 18-19, Figure 2)."""
    return (
        "Here is a schema designed to document and manage detailed information and facts about "
        f"{config(dataset)['sp_description']} For each entity, there are multiple attributes. The "
        "attributes are unique and in consistent styles. Here are the attributes in this schema: "
        + "".join(f"{a}, " for a in ordered_schema)
    ).rstrip()


def judge_prompt(schema: Sequence[str], proposals: Sequence[Dict[str, str]]) -> str:
    """Judge Instruction (JI) of the Hybrid Integration Strategy (Eq. 17)."""
    concepts = "\n".join(f"- {p['name']}: {p['definition']}" for p in proposals)
    return (
        "Your task is to analyze the given schema and judge whether the given concepts are "
        "semantically similar enough to be merged as one attribute.\n"
        f"Here is the schema: {', '.join(schema)}\n"
        f"Here are the concepts to be judged:\n{concepts}\n"
        "Explanation about the task:\n"
        "- The schema includes several unique attributes, which show the semantic granularity of "
        "attributes.\n"
        "- If the above concepts (1) are semantically equivalent, or (2) one is semantically contained "
        "by the others, or (3) they represent a finer granularity compared with the existing attributes, "
        "they need to be merged into one single attribute. Then, output \"One\".\n"
        "- Else, they should be at least two unique attributes, output \"Two\".\n"
        "- Output only \"Two\" or \"One\"."
    )


def definition_prompt(name: str, contexts: Sequence[Dict[str, Any]], dataset: str,
                      example_definitions: Optional[Dict[str, str]] = None) -> str:
    """Generating context(z) for an attribute proposal (Appendix A.4)."""
    example = (
        "Here are example definitions: " + _compact(example_definitions) + "\n" if example_definitions else ""
    )
    lines = "\n".join(
        f"In the text {c['text']}, the {name} value are: {_compact(c['values'])}" for c in contexts
    )
    return (
        "Your task is to summarize the context of an attribute and write a definition for it.\n"
        "Provide the definition in this JSON structure:\n"
        "{ \"<name>\": \"<definition>\", }\n"
        "Explanations about the JSON structure:\n"
        "- Output only the JSON data, where the key is the name of the attribute and the value is its "
        "definition.\n"
        f"- {config(dataset)['description']}\n"
        "- The name should be concise and in the same style with the examples.\n"
        "- The name should be of proper granularity. Note that if it is too general, it cannot "
        "accurately describe the range of values; if it is too specific, it cannot cover all the values.\n"
        "- The definition should precisely describe the meaning and characteristics of the attribute, "
        "enabling the reliable extraction of the attribute from other texts.\n"
        "- The definition should be less than 50 words.\n"
        f"{example}"
        "Here is the context of the attribute to be defined:\n"
        f"{lines}"
    )
