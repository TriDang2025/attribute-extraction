# Step 2 examples

## Top-10 merges at theta=0.6 (C6, most similar first)

Right = both clusters have the same majority gold class.

1. cos 0.974, WRONG
   - A (12): "stansted airport"x10, "stevenage"x2 | gold: Train destination 8; Train departure 4
   - B (25): "leicester"x8, "peterborough"x4, "ely"x4, "norwich"x4, "broxbourne"x2, "birmingham new street"x2, "bishops stortford"x1 | gold: Train departure 18; Train destination 7
2. cos 0.945, WRONG
   - A (24): "expensive"x14, "moderate"x5, "cheap"x2, "the copper kettle"x2, "the lucky star"x1 | gold: Restaurant price range 21; Restaurant name 3
   - B (7): "graffiti"x3, "la raza"x2, "anatolia"x2 | gold: Restaurant name 7
3. cos 0.928, WRONG
   - A (18): "centre"x18 | gold: Restaurant area 18
   - B (5): "thanh binh"x3, "panahar"x2 | gold: Restaurant name 5
4. cos 0.923, RIGHT
   - A (3): "cherry hinton water play"x2, "abbey pool and astroturf pitch"x1 | gold: Attraction name 3
   - B (5): "cambridge arts theatre"x2, "broughton house gallery"x1, "cinema"x1, "mumford theatre"x1 | gold: Attraction name 4; Attraction type 1
5. cos 0.896, RIGHT
   - A (10): "h4bifd0u"x2, "vbaemg3z"x1, "69luuzq7"x1, "tnu1h19g"x1, "rcjdh5j4"x1, "tygh2e4a"x1, "rjoua7e1"x1, "tjghmt3i"x1 | gold: Train confirmed reference 10
   - B (8): "p6g0s9it"x1, "ltqhut3y"x1, "698re4w1"x1, "ji5o0vtt"x1, "mu3uyqck"x1, "gj3062pe"x1, "gge66ki2"x1, "y3mavyrq"x1 | gold: Train confirmed reference 8
6. cos 0.885, WRONG
   - A (4): "nirala"x4 | gold: Restaurant name 4
   - B (27): "centre"x18, "tandoori palace"x3, "thanh binh"x3, "panahar"x2, "sitar tandoori"x1 | gold: Restaurant area 18; Restaurant name 9
7. cos 0.882, WRONG
   - A (4): "tandoori palace"x3, "sitar tandoori"x1 | gold: Restaurant name 4
   - B (23): "centre"x18, "thanh binh"x3, "panahar"x2 | gold: Restaurant area 18; Restaurant name 5
8. cos 0.859, WRONG
   - A (25): "west"x7, "north"x5, "south"x4, "turkish"x4, "modern european"x2, "east"x1, "cambridge chop house"x1, "jinling noodle bar"x1 | gold: Restaurant area 17; Restaurant food 6; Restaurant name 2
   - B (3): "don pasquale pizzeria"x2, "pizza express"x1 | gold: Restaurant name 3
9. cos 0.821, WRONG
   - A (37): "stansted airport"x10, "leicester"x8, "peterborough"x4, "ely"x4, "norwich"x4, "stevenage"x2, "broxbourne"x2, "birmingham new street"x2 | gold: Train departure 22; Train destination 15
   - B (2): "kings lynn"x2 | gold: Train destination 1; Train departure 1
10. cos 0.808, WRONG
   - A (5): "south"x3, "east"x1, "west"x1 | gold: Attraction area 5
   - B (2): "ballare"x2 | gold: Attraction name 2

## Masked contexts (first 8 mentions)

- "Stansted airport" (Train destination): User: Hello, I need to take a train to <<[TEXT]>>, arriving by [TIME].
- "20:30" (Train arrive by): User: Hello, I need to take a train to [TEXT], arriving by <<[TIME]>>.
- "Cambridge" (Train departure): System: The TR7213 gets you there at 06:08. Need a ticket? / User: Maybe. I need to leave <<[TEXT]>> on [DAY]. Will that train work?
- "Friday" (Train day): System: The TR7213 gets you there at 06:08. Need a ticket? / User: Maybe. I need to leave [TEXT] on <<[DAY]>>. Will that train work?
- "Cambridge" (Train departure): User: Maybe. I need to leave [TEXT] on [DAY]. Will that train work? / System: I recommend TR1110. It will arrive in <<[TEXT]>> at 20:08 on [DAY]. I can book passage for you if you let me know how many tickets you need.
- "Friday" (Train day): User: Maybe. I need to leave [TEXT] on [DAY]. Will that train work? / System: I recommend TR1110. It will arrive in [TEXT] at 20:08 on <<[DAY]>>. I can book passage for you if you let me know how many tickets you need.
- "swimming pools" (Attraction type): System: The price for that ticket is 10.10 pounds. Would you like me to book it for you? / User: No. Are there any <<[TEXT]>> on the [TEXT] side of town?
- "east" (Attraction area): System: The price for that ticket is 10.10 pounds. Would you like me to book it for you? / User: No. Are there any [TEXT] on the <<[TEXT]>> side of town?
