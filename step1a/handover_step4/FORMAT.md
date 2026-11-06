# Step 4 handover (wf_v4, chosen setting)

Setting: main (input a, no signals), column order seed 0, run `a_<set>_s0` of `results/wf_v4/colab/final/`. Written by `scripts/handover_v4.py` (`s1a/step4_handover.py`). Files per set (`dev50`, `dev50b`): `schema.json`, `schema.sql`, `operations.json`.

## schema.json
| field | meaning |
|---|---|
| set, setting | set name; the run and its setting |
| tables[] | `name`, `description`, `row`, `columns[]`, `primary_key` [col names], `foreign_keys` [{columns, ref_table, ref_columns}] |
| tables[].columns[] | `name`, `type` (text, integer, decimal, time, day, date, boolean, id, duration, price), `source` (Step-3 column id `"<entity>:<id>"`, null for a column Step 4 added), `new` (true when added), `gt` (always null), `step3` (the Step-3 column: entity, id, name, description, n_mentions, n_dialogues, value_type, top_values; null when added) |
| relationships[] | `from` (referring table), `to`, `kind` (one_to_many / many_to_many), `reason` |
| unused[] | Step-3 columns Step 4 left out: `source`, `reason`, `step3` |
| duplicate_flags[] | `{source, duplicate_of}` Step-3 column ids |
| source_to_table | every Step-3 column id of the set -> its table name, or null when unused |

Every Step-3 column of the set is in exactly one table or in `unused` (checked). `<id>` is `columns[].id` of `handover/<set>/<entity>.json`; the mention ids of a column are there.

## schema.sql, operations.json
`schema.sql`: CREATE TABLE statements with PRIMARY KEY and FOREIGN KEY. `operations.json`: list of CREATE_ENTITY, ADD_ATTR (with `source`, `is_key`), CREATE_REL (with `fk_columns`), in that order (`s1a/step4_sql.py`). Same content as `final/a_<set>_s0/{schema.sql, operations.json}`.
