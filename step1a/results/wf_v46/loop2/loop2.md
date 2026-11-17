# Loop 2 with Llama-3.1-8B (wf_v4.6 Y5-Y7)

## Step 1b and evidence check per entity

GT entity = scoring only (majority of the mentions). Voted = suggested in >= 2 of 3 orders.

| set | entity | GT entity | attributes | flagged | suggested names | voted | passed evidence | new columns |
|---|---|---|---|---|---|---|---|---|
| dev50 | accommodation | hotel | 23 | 9 | 13 | 7 | 2 | 2 |
| dev50 | train_info | train | 21 | 8 | 12 | 8 | 0 | 0 |
| dev50 | food_establishment | restaurant | 19 | 6 | 14 | 9 | 0 | 0 |
| dev50 | address | attraction | 13 | 10 | 16 | 8 | 1 | 0 |
| dev50 | location | attraction | 2 | 1 | 14 | 10 | 0 | 0 |
| dev50b | train_schedule | train | 16 | 8 | 14 | 7 | 0 | 0 |
| dev50b | accommodation_option | hotel | 21 | 6 | 20 | 4 | 2 | 1 |
| dev50b | location | attraction | 9 | 4 | 19 | 5 | 1 | 0 |
| dev50b | establishment | restaurant | 23 | 5 | 15 | 8 | 2 | 1 |
| dev50b | phone_number | taxi | 9 | 5 | 20 | 6 | 1 | 1 |

- dev50: failed at vote 27, at evidence 39 (first reason: overlap 20, no spans 10, n_dialogues 9), duplicate of a loop-1 column 1, added 2. Calls 40 (Step 1b 30, Step 3 10), tokens 65,089 / 12,778; finish length 2, retried 2.

- dev50b: failed at vote 58, at evidence 24 (first reason: overlap 16, n_dialogues 6, no spans 2), duplicate of a loop-1 column 2, added 4. Calls 50 (Step 1b 30, Step 3 20), tokens 73,871 / 11,001; finish length 0, retried 1.

## New columns (loop 2)

- **amenities** (dev50, accommodation = GT hotel; from "amenities"; 8 mentions; values: free internet; free parking; free wifi; parking)
  - available in your selected region. It's moderately priced and includes free internet and parking. [MUL0626, value: free internet]
  - I would like a guesthouse with free wifi please. [PMUL4504, value: free wifi]
- **star_rating** (dev50, accommodation = GT hotel; from "rating"; 14 mentions; values: 0 star; 4 star; 4 star rating; 5 star; star rating)
  - How about a 4 star rating? [PMUL0388, value: 4 star rating]
  - Yes please tell me their postcode and star rating. [PMUL4561, value: star rating]
- **amenities** (dev50b, accommodation_option = GT hotel; from "amenities; parking"; 35 mentions; values: 3 star; free internet; free parking; free wifi; parking)
  - allenbell is what I found that is cheap and has parking. [MUL1213, value: parking]
  - Yes, I need internet and free parking. [PMUL3468, value: internet]
- **area** (dev50b, establishment = GT restaurant; from "area"; 12 mentions; values: area; centre; centre of town; north side of town; specific area)
  - a bunch of options for you. Do you have a specific area or price range you are interested in? [SNG02148, value: specific area]
  - get a couple of options for you, is there a certain area you would like to go to? [SNG0670, value: certain area]
- **pickup_time** (dev50b, phone_number = GT taxi; from "service provider"; 6 mentions; values: a white audi; ask; red tesla; taxi; we)
  - Please let us know if we can do anything else for you. [MUL2510, value: we]
  - I have confirmed a taxi booking for you, a red tesla will be picking you up. [SNG01631, value: red tesla]
