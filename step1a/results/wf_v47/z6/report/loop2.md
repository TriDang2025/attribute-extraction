# Loop 2 with Llama-3.1-8B (wf_v4.7 Z6, Z4 run 1)

## Step 1b and evidence check per entity

GT entity = scoring only (majority of the mentions). Voted = suggested in >= 1 of 3 orders (v4.7 r4).

| set | entity | GT entity | attributes | flagged | suggested names | voted | passed evidence | new columns |
|---|---|---|---|---|---|---|---|---|
| dev50 | accommodation | hotel | 23 | 11 | 15 | 15 | 6 | 6 |
| dev50 | train_info | train | 21 | 6 | 11 | 11 | 2 | 1 |
| dev50 | food_establishment | restaurant | 19 | 7 | 15 | 15 | 1 | 1 |
| dev50 | address | attraction | 13 | 6 | 14 | 14 | 0 | 0 |
| dev50 | location | attraction | 2 | 1 | 12 | 12 | 0 | 0 |
| dev50b | train_schedule | train | 16 | 8 | 12 | 12 | 0 | 0 |
| dev50b | accommodation_option | hotel | 21 | 6 | 12 | 12 | 6 | 6 |
| dev50b | location | attraction | 9 | 4 | 16 | 16 | 2 | 0 |
| dev50b | establishment | restaurant | 23 | 6 | 12 | 12 | 2 | 2 |
| dev50b | phone_number | taxi | 9 | 5 | 23 | 23 | 1 | 1 |

- dev50: failed at vote 0, at evidence 57 (first reason: overlap 28, no spans 16, n_dialogues 13), duplicate of a loop-1 column 1, added 8. Calls 48 (Step 1b 30, Step 3 18), tokens 78,894 / 10,166; finish length 0, retried 0.

- dev50b: failed at vote 0, at evidence 63 (first reason: overlap 38, no spans 14, n_dialogues 11), duplicate of a loop-1 column 2, added 9. Calls 53 (Step 1b 30, Step 3 23), tokens 84,012 / 10,270; finish length 0, retried 0.

## New columns (loop 2)

- **amenities** (dev50, accommodation = GT hotel; from "amenities"; 11 mentions; values: free internet; free parking; free wifi; parking)
  - available in your selected region. It's moderately priced and includes free internet and parking. [MUL0626, value: free internet]
  - I would like a guesthouse with free wifi please. [PMUL4504, value: free wifi]
- **rating** (dev50, accommodation = GT hotel; from "rating"; 13 mentions; values: 0 star; 3-star; 4 star; 4 star rating; star rating)
  - How about a 4 star rating? [PMUL0388, value: 4 star rating]
  - Yes please tell me their postcode and star rating. [PMUL4561, value: star rating]
- **internet_options** (dev50, accommodation = GT hotel; from "internet options"; 13 mentions; values: cityroomz; free internet; free wi-fi; free wifi; wifi)
  - available in your selected region. It's moderately priced and includes free internet and parking. [MUL0626, value: free internet]
  - Yes, can you find a place for me with free wifi in the moderate price range? [PMUL0388, value: free wifi]
- **parking_options** (dev50, accommodation = GT hotel; from "parking options"; 7 mentions; values: free parking; parking)
  - Yes, please try 5-star hotels with free parking. [SNG01551, value: free parking]
  - selected region. It's moderately priced and includes free internet and parking. [MUL0626, value: parking]
- **internet** (dev50, accommodation = GT hotel; from "internet"; 17 mentions; values: cityroomz; free internet; free wi-fi; free wifi; internet)
  - As long as it has free wifi [PMUL0468, value: free wifi]
  - available in your selected region. It's moderately priced and includes free internet and parking. [MUL0626, value: free internet]
- **parking** (dev50, accommodation = GT hotel; from "parking"; 12 mentions; values: free parking; parking)
  - Yes, please try 5-star hotels with free parking. [SNG01551, value: free parking]
  - I need a hotel in the west with free parking please. [PMUL4578, value: free parking]
- **seating_capacity** (dev50, train_info = GT train; from "seating capacity"; 5 mentions; values: 4 people; 4 seat; 5 people; how many seat; number of seat)
  - Before i book it, could you confirm the number of seats you need? [PMUL3238, value: number of seats]
  - Sure. Just to confirm, how many seats will you need? [MUL1989, value: how many seats]
- **menu_type** (dev50, food_establishment = GT restaurant; from "menu"; 8 mentions; values: african food; chinese food; indian food; international food; italian food)
  - They serve indian food. [WOZ20405, value: indian food]
  - need a place to eat in that area. I want Italian food. [PMUL2050, value: Italian food]
- **amenities** (dev50b, accommodation_option = GT hotel; from "amenities"; 10 mentions; values: 3 star; free internet; free parking; free wifi; parking)
  - allenbell is what I found that is cheap and has parking. [MUL1213, value: parking]
  - I've found three, all of them are guesthouses and all of them have free internet and parking. Would [MUL1350, value: guesthouses]
- **internet** (dev50b, accommodation_option = GT hotel; from "internet"; 19 mentions; values: free internet; free wifi; internet; wifi)
  - Does this location include free wifi? [MUL0730, value: free wifi]
  - for a place to stay in the east that includes free wifi. [MUL1213, value: free wifi]
- **parking** (dev50b, accommodation_option = GT hotel; from "parking"; 21 mentions; values: free parking; parking)
  - Does this place include free parking? [SNG0935, value: free parking]
  - a place to stay that is moderately priced and includes free parking? [SNG1024, value: free parking]
- **price_range** (dev50b, accommodation_option = GT hotel; from "price range"; 23 mentions; values: expensive price range; moderate price range; moderately priced; preferred price range; price range)
  - What is the price range for the hotel? [MUL0019, value: price range]
  - There are several hotels of that nature. What is your price range? [MUL1213, value: your price range]
- **facilities** (dev50b, accommodation_option = GT hotel; from "facilities"; 11 mentions; values: 3 star; a and b guest house; free internet; free parking; parking)
  - I've found three, all of them are guesthouses and all of them have free internet and parking. Would [MUL1350, value: guesthouses]
  - for a place to stay in the east that includes free wifi. [MUL1213, value: free wifi]
- **services** (dev50b, accommodation_option = GT hotel; from "services"; 11 mentions; values: free internet; free parking; free wifi; parking; wifi)
  - all of them are guesthouses and all of them have free internet and parking. Would you like me to give your their [MUL1350, value: free internet]
  - for a place to stay in the east that includes free wifi. [MUL1213, value: free wifi]
- **cuisine_type** (dev50b, establishment = GT restaurant; from "menu"; 6 mentions; values: british food; european food; gastropub food; indian food; modern european food)
  - Please find a place to eat that serves Indian food. [PMUL4843, value: Indian food]
  - I am looking for a moderately priced restaurant that serves gastropub food. [WOZ20628, value: gastropub food]
- **cuisine_type** (dev50b, establishment = GT restaurant; from "cuisine type"; 18 mentions; values: british food; creative food; gastropub food; indian food; italian)
  - I'm looking for a restaurant that serves indian food. [SNG02148, value: indian food]
  - Please find a place to eat that serves Indian food. [PMUL4843, value: Indian food]
- **contact_number** (dev50b, phone_number = GT taxi; from "type"; 8 mentions; values: black ford; blue ford; car type; red tesla; taxi)
  - I need the car type please. [MUL1350, value: car type]
  - Booking completed! Booked car type : white ford Contact number : 07267142867 [SNG01476, value: white ford]
