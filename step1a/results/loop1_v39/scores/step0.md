# wf_v3.9 step 0

188 responses for 188 manifest jobs; problems: ['hotel_acue_dev50_s2: finish stop, errors ["clusters[13] attribute \'hotel_phone_number\' not in the attribute list"]', "dupcheck_dev50b_rc1_hotel: finish stop, errors ['joins[2] needs a list of >= 2 distinct columns', 'joins[3] needs a list of >= 2 distinct columns']"].
A-cue parse repairs (llm_cache.repair_undeclared): [{'variant': 'A-cue s2', 'ent': 'hotel', 'job': 'hotel_acue_dev50_s2', 'repaired_names': ['hotel_phone_number']}].
Notes: ['dupcheck_dev50b_rc1_hotel: 2 joins with fewer than 2 distinct columns dropped (parse errors 2), 2 kept.'].
