# wf_v3.3 noise jury rubric (fixed; do not change between runs)

Data: MultiWOZ booking dialogues in Cambridge (hotels, restaurants, trains, taxis, attractions, police, hospital).
Each row is one cluster of text spans. `examples` holds up to 6 example sentences joined by " || "; the span is in [[double brackets]].

Question: if this cluster became one database column, would its cells hold real data?

For each example, decide if the bracketed span is a VALUE: something a booking or venue database would store in a cell.
- VALUE: a name of a specific venue or station, a time, a day, a price or price range, an area (north, centre, ...),
  a food type, a star rating, a hotel type, a number of people / nights / tickets, a phone number, postcode, address,
  reference number, train id, car type, duration, fee.
- NOT A VALUE:
  1. generic words for a thing: "hotel", "the restaurant", "a train", "the place";
  2. a question or request about an attribute: "what day", "how many days", "which area", "their phone number";
  3. a label word without its value: "phone number", "postcode", "reference number";
  4. a constant that would be the same in every row: the city "Cambridge" used as "in Cambridge"
     (but "from Cambridge" / "to Cambridge" for a train or taxi is a VALUE: a departure or destination);
  5. the help desk itself or chit-chat: "Cambridge TownInfo Centre", "thank you", "anything else";
  6. a count of search results: "we have 11 options", "there are 3 Turkish restaurants".
Judge by the sentence, not the word alone ("4" in "party of 4" is a VALUE; "4" in "4 options" is not).
Which domain a value belongs to does not matter (a taxi phone number in a restaurant dialogue is still a VALUE).

Label the cluster:
- `real`: more than half of the examples are VALUES, and they are of the same kind (all phone numbers, all days).
- `noise`: half or fewer of the examples are VALUES.
- `mixed`: more than half are VALUES, but of two or more different kinds (hotel names and star ratings together).
With 1 example: VALUE -> real, else noise. With 2: both VALUES of one kind -> real, neither -> noise, otherwise mixed.

Output one CSV row per cluster: `cluster_id,label,values,reason` where values = how many examples are VALUES
(e.g. "2/6") and reason is at most 12 words.
