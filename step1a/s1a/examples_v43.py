"""wf_v4.3 (diary Nov 13, U1): made-up worked examples for the Llama-8B prompts. One small domain, a car rental (customers, cars,
rentals), with no MultiWOZ words or labels. Step 3 gets 2 examples (3-4 clusters with values and the right name each); Step 4 gets
1 example (9 columns -> tables, links, keys). Each example text stays under about 300 tokens (test_examples_v43 checks a
4-characters-per-token estimate; the Llama tokenizer is not on the laptop).

The texts are plain prompt blocks: the Step 3 / Step 4 v4.3 prompt builders paste them as they are, under a line such as
"Worked example (other domain):". Answers are written in the v4.3 answer shapes (one name per cluster id; tables from pass 1).
"""

STEP3_EXAMPLE_1 = """\
Clusters (entity R1, a car rental):
- R1#0 values: [[Main Street branch]], [[airport desk]], [[north depot]]  (in: "I'll pick it up at the [[airport desk]]")
- R1#1 values: [[airport desk]], [[Main Street branch]]  (in: "I'll drop it off at [[Main Street branch]] on Friday")
- R1#2 values: [[$39 a day]], [[$52 per day]], [[45 dollars daily]]
- R1#3 values: [[sure]], [[sounds good]], [[thanks]]
Answer:
{"R1#0": "pickup_branch", "R1#1": "return_branch", "R1#2": "daily_rate", "R1#3": "not_attribute"}
Why: R1#0 and R1#1 share values but play two roles (where the car is taken vs where it is brought back), so each role gets its own
name. R1#3 is chat, not data."""

STEP3_EXAMPLE_2 = """\
Clusters (entity C1, a car):
- C1#0 values: [[compact]], [[SUV]], [[minivan]]
- C1#1 values: [[Corolla]], [[Model 3]], [[Civic]]
- C1#2 values: [[automatic]], [[manual]], [[stick shift]]
Answer:
{"C1#0": "car_class", "C1#1": "car_model", "C1#2": "transmission"}
Why: each cluster is one kind of value, so each gets one short snake_case name. "stick shift" is another way to say "manual", so it
stays in transmission."""

STEP4_EXAMPLE = """\
Columns: customer_name, customer_phone, licence_number, car_model, car_class, plate_number, pickup_date, return_date, daily_rate
Pass 1, the main things (tables): ["customer", "car", "rental"]
Pass 2, each column to one table:
{"customer_name": "customer", "customer_phone": "customer", "licence_number": "customer", "car_model": "car", "car_class": "car",
 "plate_number": "car", "pickup_date": "rental", "return_date": "rental", "daily_rate": "rental"}
Links (one question per pair):
- customer and car: none (they meet only through a rental)
- customer and rental: customer -> rental (one customer has many rentals)
- car and rental: car -> rental (one car has many rentals)
Keys (one table at a time):
- customer: primary key licence_number
- car: primary key plate_number
- rental: new key rental_id; foreign keys licence_number -> customer, plate_number -> car"""

EXAMPLES = {"step3_1": STEP3_EXAMPLE_1, "step3_2": STEP3_EXAMPLE_2, "step4": STEP4_EXAMPLE}
BANNED = ("hotel", "train", "restaurant", "taxi", "attraction")    # MultiWOZ domain words the examples must not use


def est_tokens(text):
    """Rough token count (4 characters per token) used where the Llama tokenizer is not available."""
    return (len(text) + 3) // 4
