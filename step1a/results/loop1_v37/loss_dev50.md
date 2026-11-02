# wf_v3.7 loss table: where A loses each missed attribute (L2)

Set: dev50. Orders: A r1 = order 0, A r2 = order 1, A s2 = order 2. An attribute A does not find in an order is lost at **Step 1a** when no cluster makes it recoverable (reason as in the ceiling table) and at **Step 3** when some cluster does (the best one is followed): marked_not_attribute (its group is marked), merged_wrongly (its group's purity fails because of a merge), mixed_roles (merged with the role partner), split (its group is a split part), not_in_response (A gave the cluster no decision), other.

## Stage and reason per order (attribute-orders)

| variant | missed | Step 1a | Step 3 | reasons |
|---|---|---|---|---|
| A r1 | 9 | 7 | 2 | Step 1a: diluted 4; Step 1a: mixed_roles 1; Step 1a: never_found 2; Step 3: marked_not_attribute 1; Step 3: merged_wrongly 1 |
| A r2 | 10 | 8 | 2 | Step 1a: diluted 5; Step 1a: mixed_roles 1; Step 1a: never_found 2; Step 3: merged_wrongly 2 |
| A s2 | 9 | 7 | 2 | Step 1a: diluted 4; Step 1a: mixed_roles 1; Step 1a: never_found 2; Step 3: merged_wrongly 2 |

## Attributes missed in at least one order

| ent | attribute | missed | A r1 | A r2 | A s2 |
|---|---|---|---|---|---|
| train | Train arrive by | 3/3 | Step 1a: mixed_roles | Step 1a: mixed_roles | Step 1a: mixed_roles |
| train | Train destination | 3/3 | Step 1a: diluted | Step 1a: diluted | Step 1a: diluted |
| train | Train requested people | 1/3 | found | Step 1a: diluted | found |
| hotel | Hotel internet | 3/3 | Step 1a: never_found | Step 1a: never_found | Step 1a: never_found |
| hotel | Hotel parking | 3/3 | Step 1a: never_found | Step 1a: never_found | Step 1a: never_found |
| restaurant | Taxi arrive by | 3/3 | Step 1a: diluted | Step 1a: diluted | Step 1a: diluted |
| restaurant | Taxi departure | 3/3 | Step 3: merged_wrongly | Step 3: merged_wrongly | Step 3: merged_wrongly |
| restaurant | Taxi destination | 3/3 | Step 3: marked_not_attribute | Step 3: merged_wrongly | Step 3: merged_wrongly |
| restaurant | Taxi leave at | 3/3 | Step 1a: diluted | Step 1a: diluted | Step 1a: diluted |
| restaurant | Taxi phone | 3/3 | Step 1a: diluted | Step 1a: diluted | Step 1a: diluted |

Attributes with a Step-3 loss in at least one order: 2; all missed attributes: 10; recoverable at Step 1a: 29/40.
