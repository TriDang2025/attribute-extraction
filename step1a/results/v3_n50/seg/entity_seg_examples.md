# Entity segmentation examples

## PMUL1270

### 50/400: 3 pieces

**piece 1** (gold: train 6, attraction 1)
> User: Hello, I need to take a train to Stansted airport, arriving by 20:30.
> System: The TR7213 gets you there at 06:08. Need a ticket?
> User: Maybe. I need to leave Cambridge on Friday. Will that train work?
> System: I recommend TR1110. It will arrive in Cambridge at 20:08 on Friday. I can book passage for you if you let me know how many tickets you need.
> User: What is the cost per ticket?
> System: The price for that ticket is 10.10 pounds. Would you like me to book it for you?
> User: No. Are there any swimming pools on the east side of town?

**piece 2** (gold: attraction 3)
> System: Yes there is the abbey pool and astroturf pitch would you like their address?
> User: Yes. May I have the address and postcode for the Abbey Pool please?
> System: Yes, of course. They are located at Pool Way, Whitehill Road, off NewMarket Road. Their postcode is cb58nt. Is there anything else I can do for today?

**piece 3** (gold: attraction 4)
> User: No, that is all I need. Thank you for your help.
> System: I am happy to help you with the booking, enjoy.
> User: Thanks! I appreciate your help. Bye.
> System: It's my pleasure. Thank you for using Cambridge TownInfo centre. Goodbye.

## WOZ20405

### 50/400: 3 pieces

**piece 1** (gold: restaurant 1)
> User: I want to find an expensive restaurant in the east part of town

**piece 2** (gold: restaurant 3)
> .
> System: What is the food type you would prefer?
> User: I don't care. I just need to know the address, phone number, and postcode of the venue please.
> System: How about Sitar Tandoori, It's address is 43 High Street Cherry Hinton Cherry Hinton, their postcode is C.B 1, 9 H.X, and their phone number is 01223 249955.

**piece 3** (gold: restaurant 6)
> User: what is the food type of that restaurant ?
> System: They serve indian food.
> User: Thank you, goodbye
> System: Thank You
> User: goodbye
> System: Good day!

## MUL0589

### 50/400: 4 pieces

**piece 1** (gold: attraction 6)
> User: I am looking for a college attraction to go to in town.
> System: There are several colleges in either the centre or west part of town. Which area do you prefer?
> User: The centre please.
> System: There are 13 colleges in the center of town. Does entrance fee matter to you?
> User: Not really, but what is the fee?
> System: Most are free, but Corpus Christi has a 2 pound fee, Saint John's has a 2.50 pound fee, and Trinity has a 1 pound fee.

**piece 2** (gold: train 3)
> User: I need a train that leaves at 20:45 from stevenage to cambridge
> System: What day would you like to travel by train?
> User: I would like to leave on Wednesday.

**piece 3** (gold: train 14)
> System: There are 10 trains, TR9448 leaves at 5:54 would that work for you?
> User: That works can I have the travel time for that please?
> System: TR9448 leaves at 05:54 and arrives at 06:43. The travel time is 49 minutes.
> User: I've mixed up my locations. I actually need a train that departs from Cambridge and goes to Stevenage.
> System: I only have two trains that leave from Cambridge Wednesday. The TR9016 departs at 21:21 and the TR6387 departs 23:21.
> User: What is the price?
> System: Both options are 12.80 pounds. Would you like to book one of these options?
> User: Can you tell me the duration of travel time please?
> System: Yes travel is exactly 49 minutes.
> User: What about the train ID?
> System: The train ID for the departure at 21:21 is TR9016 and the trainID that departs at 2312 is TR6387. Would you like me to book on of these for you?
> User: I need an earlier train.
> System: TR9016 is the earliest departure after 20:45. Would you like to change your specified time?
> User: No, TR9016 will do.

**piece 4** (gold: train 3)
> System: I ha e booked your ticket. Your confirmation number is VBAEMG3Z. Can I assist you with anything else?
> User: No, that's all I need. Thank you.
> System: Thank you let me know if you need anything else.

