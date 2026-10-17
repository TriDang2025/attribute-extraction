"""Hand-annotated Incidents/Weather smoke sets in the paper's format.

The paper's Incidents and Weather annotations are not released. These few texts reuse our
earlier hand-made examples, relabeled with Table 6 attribute names, values as exact text
spans, and one record per entity instance. They test the pipeline; their scores are not
comparable with the paper's.
"""

import json
from pathlib import Path

from tear_reproduction.schema import full_schema, json_to_table

ROOT = Path(__file__).resolve().parents[1] / "data"

INCIDENTS = {
    "pool": [
        ("inc-p1", "A 24-year-old man was shot and killed Saturday night outside a bar on Elm Avenue in Dayton. Police arrested a 31-year-old suspect, James Carter, on Sunday.",
         {"Accident": {"0": {"Accident type": ["shot"], "Accident date": ["Saturday night"], "Accident address": ["outside a bar on Elm Avenue in Dayton"]}},
          "Victim": {"0": {"Victim age": ["24-year-old"], "Victim gender": ["man"], "Victim status": ["killed"]}},
          "Suspect": {"0": {"Suspect age": ["31-year-old"], "Suspect name": ["James Carter"], "Suspect status": ["arrested"]}}}),
        ("inc-p2", "Two teenagers were wounded in a drive-by shooting on Monday afternoon near Lincoln Park in Chicago. Both were taken to Stroger Hospital in stable condition. No arrests have been made.",
         {"Accident": {"0": {"Accident type": ["drive-by shooting"], "Accident date": ["Monday afternoon"], "Accident address": ["near Lincoln Park in Chicago"]}},
          "Victim": {"0": {"Victim number": ["Two"], "Victim age": ["teenagers"], "Victim status": ["wounded"], "Hospital name": ["Stroger Hospital"]}}}),
        ("inc-p3", "Maria Lopez, 45, was injured when a stray bullet struck her apartment window on 5th Street in Phoenix early Thursday. Officers are searching for a gray sedan seen leaving the area.",
         {"Accident": {"0": {"Accident date": ["early Thursday"], "Accident address": ["5th Street in Phoenix"]}},
          "Victim": {"0": {"Victim name": ["Maria Lopez"], "Victim age": ["45"], "Victim status": ["injured"]}},
          "Suspect": {"0": {"Suspect vehicle": ["gray sedan"]}}}),
        ("inc-p4", "A shooting at a gas station on Route 9 in Albany left one man dead and another injured late Friday. The victims were identified as Kevin Brooks, 29, who died, and Tyrone Hill, 33. A suspect, 22-year-old Marcus Reed, was taken into custody.",
         {"Accident": {"0": {"Accident type": ["shooting"], "Accident date": ["late Friday"], "Accident address": ["a gas station on Route 9 in Albany"]}},
          "Victim": {"0": {"Victim name": ["Kevin Brooks"], "Victim age": ["29"], "Victim gender": ["man"], "Victim status": ["dead"]},
                     "1": {"Victim name": ["Tyrone Hill"], "Victim age": ["33"], "Victim status": ["injured"]}},
          "Suspect": {"0": {"Suspect name": ["Marcus Reed"], "Suspect age": ["22-year-old"], "Suspect status": ["taken into custody"]}}}),
    ],
    "test": [
        ("inc-1", "Police say a 19-year-old woman was shot and wounded Tuesday evening on Maple Drive in Memphis. Officers arrested 27-year-old Derek Simms at the scene.",
         {"Accident": {"0": {"Accident type": ["shot"], "Accident date": ["Tuesday evening"], "Accident address": ["Maple Drive in Memphis"]}},
          "Victim": {"0": {"Victim age": ["19-year-old"], "Victim gender": ["woman"], "Victim status": ["wounded"]}},
          "Suspect": {"0": {"Suspect age": ["27-year-old"], "Suspect name": ["Derek Simms"], "Suspect status": ["arrested"]}}}),
        ("inc-2", "A 52-year-old man, Robert Hayes, was killed in a shooting outside a convenience store on Pine Street in Tulsa early Sunday. No suspects have been identified.",
         {"Accident": {"0": {"Accident type": ["shooting"], "Accident date": ["early Sunday"], "Accident address": ["outside a convenience store on Pine Street in Tulsa"]}},
          "Victim": {"0": {"Victim name": ["Robert Hayes"], "Victim age": ["52-year-old"], "Victim gender": ["man"], "Victim status": ["killed"]}}}),
    ],
}

WEATHER = {
    "pool": [
        ("wx-p1", "Tonight: Mostly cloudy, with a low around 48. South wind 5 to 10 mph. Chance of rain 30 percent.",
         {"Weather": {"0": {"Time": ["Tonight"], "Cloud status": ["Mostly cloudy"], "Minimum temperature": ["48"], "Wind direction": ["South"],
                            "Wind speed": ["5 to 10 mph"], "Weather type": ["rain"], "Weather occurring chance": ["30 percent"]}}}),
        ("wx-p2", "Wednesday: Sunny, with a high near 82. Light and variable wind becoming west around 6 mph in the afternoon.",
         {"Weather": {"0": {"Time": ["Wednesday"], "Weather type": ["Sunny"], "Maximum temperature": ["82"], "Wind status": ["Light and variable"],
                            "Wind direction": ["west"], "Wind speed": ["around 6 mph"]}}}),
        ("wx-p3", "Friday Night: Showers and thunderstorms likely, mainly before 2am. Cloudy, with a low around 61. Northwest wind 10 to 15 mph, with gusts as high as 25 mph. Chance of precipitation is 70%.",
         {"Weather": {"0": {"Time": ["Friday Night"], "Weather type": ["Showers and thunderstorms"], "Cloud status": ["Cloudy"], "Minimum temperature": ["61"],
                            "Wind direction": ["Northwest"], "Wind speed": ["10 to 15 mph", "25 mph"], "Weather occurring chance": ["70%"]}}}),
        ("wx-p4", "Sunday: Snow likely after 10am. Cloudy, with a high near 30. North wind around 10 mph. New snow accumulation of 1 to 2 inches possible.",
         {"Weather": {"0": {"Time": ["Sunday"], "Weather type": ["Snow"], "Snow status": ["1 to 2 inches"], "Cloud status": ["Cloudy"],
                            "Maximum temperature": ["30"], "Wind direction": ["North"], "Wind speed": ["around 10 mph"]}}}),
    ],
    "test": [
        ("wx-1", "Thursday: Partly sunny, with a high near 67. Southwest wind 10 to 15 mph. Chance of showers 20 percent.",
         {"Weather": {"0": {"Time": ["Thursday"], "Weather type": ["Partly sunny"], "Maximum temperature": ["67"], "Wind direction": ["Southwest"],
                            "Wind speed": ["10 to 15 mph"], "Weather occurring chance": ["20 percent"]}}}),
    ],
}


def build(name, dataset, data):
    out = ROOT / name
    out.mkdir(parents=True, exist_ok=True)
    schema = full_schema(dataset)
    files = {"pool": [], "test": [], "input": []}
    for split in ("pool", "test"):
        for ident, text, obj in data[split]:
            for entity in obj.values():
                for record in entity.values():
                    for attribute, values in record.items():
                        assert attribute in schema, (ident, attribute)
                        for value in values:
                            assert value in text, (ident, attribute, value)
            row = {"id": ident, "text": text, "table": json_to_table(obj, dataset, schema)}
            files[split].append(row)
            if split == "test":
                files["input"].append({"id": ident, "text": text, "schema": schema})
    for split, rows in files.items():
        (out / f"{split}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf8")
    print(name, {k: len(v) for k, v in files.items()})


if __name__ == "__main__":
    build("incidents_small", "Incidents", INCIDENTS)
    build("weather_small", "Weather", WEATHER)
