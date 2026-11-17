# Y2: PK rule (a), frozen v4.3 vs one command v4.5 (dev50, full GT, best design per chain)

| run | chain | table | gt_table | gt_pk | model_pk | credited_as | gt_pk_in_table | rule_a |
|---|---|---|---|---|---|---|---|---|
| frozen v4.3 | a_llama43_dev50_s0 | train | train | Train trainid | reference number key | None | True | False |
| frozen v4.3 | a_llama43_dev50_s0 | hotel | hotel | Hotel name | reference number key | None | True | False |
| frozen v4.3 | a_llama43_dev50_s0 | restaurant | restaurant | Restaurant name | restaurant name key | None | True | False |
| frozen v4.3 | a_llama43_dev50_s1 | train_departure_time | restaurant | Restaurant name | id | Restaurant name | False | True |
| frozen v4.3 | a_llama43_dev50_s1 | train_departure_location | train | Train trainid | departure location key | Train trainid | False | True |
| frozen v4.3 | a_llama43_dev50_s1 | hotel_id_reference_number | hotel | Hotel name | reference number key | None | True | False |
| frozen v4.3 | a_llama43_dev50_s2 | reference | hotel | Hotel name | reference number key | None | True | False |
| frozen v4.3 | a_llama43_dev50_s2 | location | train | Train trainid | location key | Train trainid | False | True |
| frozen v4.3 | a_llama43_dev50_s2 | time | hotel_booking | Hotel booking id | time | Hotel booking id | False | True |
| frozen v4.3 | a_llama43_dev50_s2 | price | restaurant | Restaurant name | price key | None | True | False |
| one command v4.5 | a_llama44_c_n50_s0 | hotel | hotel | Hotel name | reservation number key | None | True | False |
| one command v4.5 | a_llama44_c_n50_s0 | train | train | Train trainid | train id key | None | True | False |
| one command v4.5 | a_llama44_c_n50_s0 | restaurant | restaurant | Restaurant name | id | None | True | False |
| one command v4.5 | a_llama44_c_n50_s0 | attraction | attraction | Attraction name | name id | None | True | False |
| one command v4.5 | a_llama44_c_n50_s1 | hotel | hotel | Hotel name | reservation number key | None | True | False |
| one command v4.5 | a_llama44_c_n50_s1 | train | train | Train trainid | id | None | True | False |
| one command v4.5 | a_llama44_c_n50_s1 | restaurant | restaurant | Restaurant name | reference number key | None | True | False |
| one command v4.5 | a_llama44_c_n50_s1 | attraction | attraction | Attraction name | attraction name key | None | True | False |
| one command v4.5 | a_llama44_c_n50_s2 | hotel | hotel | Hotel name | reservation number key | None | True | False |
| one command v4.5 | a_llama44_c_n50_s2 | train | train | Train trainid | id | None | True | False |
| one command v4.5 | a_llama44_c_n50_s2 | restaurant | restaurant | Restaurant name | reference number key | None | True | False |
| one command v4.5 | a_llama44_c_n50_s2 | attraction | attraction | Attraction name | postcode key | None | True | False |

- frozen v4.3: rule (a) 4/10; model PKs that are new id columns: 10/10; tables that already hold the GT PK column: 6/10

- one command v4.5: rule (a) 0/12; model PKs that are new id columns: 12/12; tables that already hold the GT PK column: 12/12
