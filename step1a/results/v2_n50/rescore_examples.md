# Gold mentions, examples

labels = classes after merge; raw = attributes; amb = no attribute of the turn's entity (all attributes with the value kept); verbatim = found in the text (turn -1 otherwise).

## PMUL1270

| Value | Text | Turn | Domain | Labels | Raw | Amb | Verbatim | Hidden L1/L2/L3 |
|---|---|---|---|---|---|---|---|---|
| stansted airport | Stansted airport | 0 | train | Train destination | Train destination |  | y | -/-/- |
| 20:30 | 20:30 | 0 | train | Train arrive by | Train arrive by |  | y | -/-/y |
| cambridge | Cambridge | 2 | train | Train departure | Train departure |  | y | -/-/- |
| friday | Friday | 2 | train | Train day | Train day |  | y | -/-/- |
| cambridge | Cambridge | 3 | train | Train departure | Train departure |  | y | -/-/- |
| friday | Friday | 3 | train | Train day | Train day |  | y | -/-/- |
| swimming pools | swimming pools | 6 | attraction | Attraction type | Attraction type |  | y | -/-/y |
| east | east | 6 | attraction | Attraction area | Attraction area |  | y | -/-/y |
| abbey pool and astroturf pitch | abbey pool and astroturf pitch | 7 | attraction | Attraction name | Attraction name |  | y | -/-/y |
| cambridge | Cambridge | 13 | attraction | Train departure | Train departure | y | y | -/-/- |

Dialogue:

> 0: User: Hello, I need to take a train to Stansted airport, arriving by 20:30.
> 1: System: The TR7213 gets you there at 06:08. Need a ticket?
> 2: User: Maybe. I need to leave Cambridge on Friday. Will that train work?
> 3: System: I recommend TR1110. It will arrive in Cambridge at 20:08 on Friday. I can book passage for you if you let me know how many tickets you need.
> 4: User: What is the cost per ticket?
> 5: System: The price for that ticket is 10.10 pounds. Would you like me to book it for you?
> 6: User: No. Are there any swimming pools on the east side of town?
> 7: System: Yes there is the abbey pool and astroturf pitch would you like their address?
> 8: User: Yes. May I have the address and postcode for the Abbey Pool please?
> 9: System: Yes, of course. They are located at Pool Way, Whitehill Road, off NewMarket Road. Their postcode is cb58nt. Is there anything else I can do for today?
> 10: User: No, that is all I need. Thank you for your help.
> 11: System: I am happy to help you with the booking, enjoy.
> 12: User: Thanks! I appreciate your help. Bye.
> 13: System: It's my pleasure. Thank you for using Cambridge TownInfo centre. Goodbye.

## WOZ20405

| Value | Text | Turn | Domain | Labels | Raw | Amb | Verbatim | Hidden L1/L2/L3 |
|---|---|---|---|---|---|---|---|---|
| expensive | expensive | 0 | restaurant | Restaurant price range | Restaurant price range |  | y | -/-/- |
| east | east | 0 | restaurant | Restaurant area | Restaurant area |  | y | -/-/- |
| sitar tandoori | Sitar Tandoori | 3 | restaurant | Restaurant name | Restaurant name |  | y | -/-/- |

Dialogue:

> 0: User: I want to find an expensive restaurant in the east part of town.
> 1: System: What is the food type you would prefer?
> 2: User: I don't care. I just need to know the address, phone number, and postcode of the venue please.
> 3: System: How about Sitar Tandoori, It's address is 43 High Street Cherry Hinton Cherry Hinton, their postcode is C.B 1, 9 H.X, and their phone number is 01223 249955.
> 4: User: what is the food type of that restaurant ?
> 5: System: They serve indian food.
> 6: User: Thank you, goodbye
> 7: System: Thank You
> 8: User: goodbye
> 9: System: Good day!

## MUL0589

| Value | Text | Turn | Domain | Labels | Raw | Amb | Verbatim | Hidden L1/L2/L3 |
|---|---|---|---|---|---|---|---|---|
| college | college | 0 | attraction | Attraction type | Attraction type |  | y | -/-/y |
| 1 | 1 | 5 | attraction | Train requested people | Train requested people | y | y | -/y/y |
| 20:45 | 20:45 | 6 | train | Train leave at | Train leave at |  | y | y/y/y |
| stevenage | stevenage | 6 | train | Train destination | Train destination |  | y | -/-/- |
| cambridge | cambridge | 6 | train | Train departure | Train departure |  | y | -/-/- |
| wednesday | Wednesday | 8 | train | Train day | Train day |  | y | -/-/- |
| cambridge | Cambridge | 12 | train | Train departure | Train departure |  | y | -/-/- |
| stevenage | Stevenage | 12 | train | Train destination | Train destination |  | y | -/-/- |
| cambridge | Cambridge | 13 | train | Train departure | Train departure |  | y | -/-/- |
| wednesday | Wednesday | 13 | train | Train day | Train day |  | y | -/-/- |
| 20:45 | 20:45 | 21 | train | Train leave at | Train leave at |  | y | y/y/y |
| vbaemg3z | VBAEMG3Z | 23 | train | Train confirmed reference | Train confirmed reference |  | y | -/y/y |

Dialogue:

> 0: User: I am looking for a college attraction to go to in town.
> 1: System: There are several colleges in either the centre or west part of town. Which area do you prefer?
> 2: User: The centre please.
> 3: System: There are 13 colleges in the center of town. Does entrance fee matter to you?
> 4: User: Not really, but what is the fee?
> 5: System: Most are free, but Corpus Christi has a 2 pound fee, Saint John's has a 2.50 pound fee, and Trinity has a 1 pound fee.
> 6: User: I need a train that leaves at 20:45 from stevenage to cambridge
> 7: System: What day would you like to travel by train?
> 8: User: I would like to leave on Wednesday.
> 9: System: There are 10 trains, TR9448 leaves at 5:54 would that work for you?
> 10: User: That works can I have the travel time for that please?
> 11: System: TR9448 leaves at 05:54 and arrives at 06:43. The travel time is 49 minutes.
> 12: User: I've mixed up my locations. I actually need a train that departs from Cambridge and goes to Stevenage.
> 13: System: I only have two trains that leave from Cambridge Wednesday. The TR9016 departs at 21:21 and the TR6387 departs 23:21.
> 14: User: What is the price?
> 15: System: Both options are 12.80 pounds. Would you like to book one of these options?
> 16: User: Can you tell me the duration of travel time please?
> 17: System: Yes travel is exactly 49 minutes.
> 18: User: What about the train ID?
> 19: System: The train ID for the departure at 21:21 is TR9016 and the trainID that departs at 2312 is TR6387. Would you like me to book on of these for you?
> 20: User: I need an earlier train.
> 21: System: TR9016 is the earliest departure after 20:45. Would you like to change your specified time?
> 22: User: No, TR9016 will do.
> 23: System: I ha e booked your ticket. Your confirmation number is VBAEMG3Z. Can I assist you with anything else?
> 24: User: No, that's all I need. Thank you.
> 25: System: Thank you let me know if you need anything else.

