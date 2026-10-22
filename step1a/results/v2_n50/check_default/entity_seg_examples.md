# Entity segmentation examples

## PMUL1270

### 50/400: 3 pieces

**piece 1** (gold: train 6, attraction 1)
> User: Hello, I need to take a train to [Stansted airport](place=Train destination), arriving by [20:30](time=Train arrive by).
> System: The [TR7213](number) gets you there at [06:08](time). Need a ticket?
> User: Maybe. I need to leave [Cambridge](place=Train departure) on [Friday](day=Train day). Will that train work?
> System: I recommend [TR1110](number). It will arrive in [Cambridge](place) at [20:08](time) on [Friday](day). I can book passage for you if you let me know how many tickets you need.
> User: What is the cost per ticket?
> System: The price for that ticket is [10.10 pounds](price). Would you like me to book it for you?
> User: No. Are there any swimming pools on the east side of town?

**piece 2** (gold: attraction 3)
> System: Yes there is the [abbey pool](place=Attraction name) and astroturf pitch would you like their address?
> User: Yes. May I have the address and postcode for the [Abbey Pool](place) please?
> System: Yes, of course. They are located at [Pool Way](place), [Whitehill Road](place), off [NewMarket Road](place). Their postcode is [cb58nt](place). Is there anything else I can do for [today](day)?

**piece 3** (gold: attraction 4)
> User: No, that is all I need. Thank you for your help.
> System: I am happy to help you with the booking, enjoy.
> User: Thanks! I appreciate your help. Bye.
> System: It's my pleasure. Thank you for using [Cambridge TownInfo centre](place). Goodbye.

### 25/200 +merge 0.45: 2 pieces

**piece 1** (gold: train 6)
> User: Hello, I need to take a train to [Stansted airport](place=Train destination), arriving by [20:30](time=Train arrive by).
> System: The [TR7213](number) gets you there at [06:08](time). Need a ticket?
> User: Maybe. I need to leave [Cambridge](place=Train departure) on [Friday](day=Train day). Will that train work?
> System: I recommend [TR1110](number). It will arrive in [Cambridge](place) at [20:08](time) on [Friday](day). I can book passage for you if you let me know how many tickets you need.
> User: What is the cost per ticket?
> System: The price for that ticket is [10.10 pounds](price). Would you like me to book it for you?

**piece 2** (gold: attraction 8)
> User: No. Are there any swimming pools on the east side of town?
> System: Yes there is the [abbey pool](place) and [astroturf pitch](place=Attraction name) would you like their address?
> User: Yes. May I have the address and postcode for the [Abbey Pool](place) please?
> System: Yes, of course. They are located at [Pool Way](place), [Whitehill Road](place), off [NewMarket Road](place). Their postcode is [cb58nt](place). Is there anything else I can do for today?
> User: No, that is all I need. Thank you for your help.
> System: I am happy to help you with the booking, enjoy.
> User: Thanks! I appreciate your help. Bye.
> System: It's my pleasure. Thank you for using Cambridge TownInfo centre. Goodbye.

### 25/200 +merge 0.50: 4 pieces

**piece 1** (gold: train 6)
> User: Hello, I need to take a train to [Stansted airport](place=Train destination), arriving by [20:30](time=Train arrive by).
> System: The [TR7213](number) gets you there at [06:08](time). Need a ticket?
> User: Maybe. I need to leave [Cambridge](place=Train departure) on [Friday](day=Train day). Will that train work?
> System: I recommend [TR1110](number). It will arrive in [Cambridge](place) at [20:08](time) on [Friday](day). I can book passage for you if you let me know how many tickets you need.
> User: What is the cost per ticket?
> System: The price for that ticket is [10.10 pounds](price). Would you like me to book it for you?

**piece 2** (gold: attraction 4)
> User: No. Are there any swimming pools on the east side of town?
> System: Yes there is the [abbey pool](place=Attraction name) and [astroturf pitch](place=Attraction name) would you like their address?
> User: Yes. May I have the address and postcode for the [Abbey Pool](place) please?
> System: Yes, of course. They are located at [Pool Way](place), [Whitehill Road](place), off [NewMarket Road](place)

**piece 3** (gold: )
> . Their postcode is [cb58nt](name). Is there anything else I can do for [today](day)?

**piece 4** (gold: attraction 4)
> User: No, that is all I need. Thank you for your help.
> System: I am happy to help you with the booking, enjoy.
> User: Thanks! I appreciate your help. Bye.
> System: It's my pleasure. Thank you for using [Cambridge TownInfo centre](place). Goodbye.

### 25/100 +merge 0.45: 2 pieces

**piece 1** (gold: train 6)
> User: Hello, I need to take a train to [Stansted airport](place=Train destination), arriving by [20:30](time=Train arrive by).
> System: The [TR7213](number) gets you there at [06:08](time). Need a ticket?
> User: Maybe. I need to leave [Cambridge](place=Train departure) on [Friday](day=Train day). Will that train work?
> System: I recommend [TR1110](number). It will arrive in [Cambridge](place) at [20:08](time) on [Friday](day). I can book passage for you if you let me know how many tickets you need.
> User: What is the cost per ticket?
> System: The price for that ticket is [10.10 pounds](price). Would you like me to book it for you?

**piece 2** (gold: attraction 8)
> User: No. Are there any swimming pools on the east side of town?
> System: Yes there is the [abbey pool](place) and [astroturf pitch](place=Attraction name) would you like their address?
> User: Yes. May I have the address and postcode for the [Abbey Pool](place) please?
> System: Yes, of course. They are located at [Pool Way](place), [Whitehill Road](place), off [NewMarket Road](place). Their postcode is [cb58nt](place). Is there anything else I can do for today?
> User: No, that is all I need. Thank you for your help.
> System: I am happy to help you with the booking, enjoy.
> User: Thanks! I appreciate your help. Bye.
> System: It's my pleasure. Thank you for using Cambridge TownInfo centre. Goodbye.

## WOZ20405

### 50/400: 3 pieces

**piece 1** (gold: restaurant 1)
> User: I want to find an expensive restaurant in the [east part of town](place=Restaurant area)

**piece 2** (gold: restaurant 3)
> .
> System: What is the food type you would prefer?
> User: I don't care. I just need to know the address, [phone number](number), and postcode of the venue please.
> System: How about [Sitar Tandoori](place=Restaurant name), It's address is [43 High Street](place) [Cherry Hinton](place) [Cherry Hinton](place), their postcode is [C.B 1, 9 H.X](place), and their phone number is [01223 249955](number).

**piece 3** (gold: restaurant 6)
> User: what is the food type of that [restaurant](place) ?
> System: They serve indian food.
> User: Thank you, goodbye
> System: Thank You
> User: goodbye
> System: Good day!

### 25/200 +merge 0.45: 1 pieces

**piece 1** (gold: restaurant 10)
> User: I want to find an expensive restaurant in the east part of town.
> System: What is the food type you would prefer?
> User: I don't care. I just need to know the address, [phone number](number), and postcode of the venue please.
> System: How about [Sitar Tandoori](name=Restaurant name), It's address is [43 High Street](place) [Cherry Hinton](place) [Cherry Hinton](place), their postcode is [C.B 1](place), [9 H.X](place), and their phone number is [01223 249955](number).
> User: what is the food type of that restaurant ?
> System: They serve indian food.
> User: Thank you, goodbye
> System: Thank You
> User: goodbye
> System: Good day!

### 25/200 +merge 0.50: 1 pieces

**piece 1** (gold: restaurant 10)
> User: I want to find an expensive restaurant in the east part of town.
> System: What is the food type you would prefer?
> User: I don't care. I just need to know the address, [phone number](number), and postcode of the venue please.
> System: How about [Sitar Tandoori](name=Restaurant name), It's address is [43 High Street](place) [Cherry Hinton](place) [Cherry Hinton](place), their postcode is [C.B 1](place), [9 H.X](place), and their phone number is [01223 249955](number).
> User: what is the food type of that restaurant ?
> System: They serve indian food.
> User: Thank you, goodbye
> System: Thank You
> User: goodbye
> System: Good day!

### 25/100 +merge 0.45: 1 pieces

**piece 1** (gold: restaurant 10)
> User: I want to find an expensive restaurant in the east part of town.
> System: What is the food type you would prefer?
> User: I don't care. I just need to know the address, [phone number](number), and postcode of the venue please.
> System: How about [Sitar Tandoori](name=Restaurant name), It's address is [43 High Street](place) [Cherry Hinton](place) [Cherry Hinton](place), their postcode is [C.B 1](place), [9 H.X](place), and their phone number is [01223 249955](number).
> User: what is the food type of that restaurant ?
> System: They serve indian food.
> User: Thank you, goodbye
> System: Thank You
> User: goodbye
> System: Good day!

## MUL0589

### 50/400: 4 pieces

**piece 1** (gold: attraction 6)
> User: I am looking for a college attraction to go to in [town](place).
> System: There are several colleges in either the [centre](place) or west part of [town](place). Which area do you prefer?
> User: The [centre](place) please.
> System: There are [13 colleges](number) in the [center](place) of [town](place). Does [entrance fee](price) matter to you?
> User: Not really, but what is the fee?
> System: Most are free, but [Corpus Christi](name) has a [2 pound fee](price), [Saint John](name)'s has a [2.50 pound fee](price), and [Trinity](name) has a [1 pound fee](price=Train requested people).

**piece 2** (gold: train 3)
> User: [I](name) need a train that leaves at [20:45](time=Train leave at) from [stevenage](place=Train destination) to [cambridge](place=Train departure)
> System: What day would you like to travel by train?
> User: [I](name) would like to leave on [Wednesday](day=Train day).

**piece 3** (gold: train 14)
> System: There are 10 trains, [TR9448](number) leaves at [5:54](time) would that work for you?
> User: That works can I have the travel time for that please?
> System: [TR9448](number) leaves at [05:54](time) and arrives at [06:43](time). The travel time is [49 minutes](duration).
> User: I've mixed up my locations. I actually need a train that departs from [Cambridge](place) and goes to [Stevenage](place).
> System: I only have two trains that leave from [Cambridge](place) [Wednesday](day). The [TR9016](number) departs at [21:21](time) and the [TR6387](number) departs [23:21](time).
> User: What is the price?
> System: Both options are [12.80 pounds](price). Would you like to book one of these options?
> User: Can you tell me the duration of travel time please?
> System: Yes travel is exactly [49 minutes](duration).
> User: What about the train ID?
> System: The train ID for the departure at [21:21](time) is [TR9016](number) and the trainID that departs at 2312 is [TR6387](name). Would you like me to book on of these for you?
> User: I need an earlier train.
> System: [TR9016](number) is the earliest departure after 20:45. Would you like to change your specified time?
> User: No, [TR9016](number) will do.

**piece 4** (gold: train 3)
> System: I ha e booked your ticket. Your confirmation number is [VBAEMG3Z](number=Train confirmed reference). Can I assist you with anything else?
> User: No, that's all I need. Thank you.
> System: Thank you let me know if you need anything else.

### 25/200 +merge 0.45: 2 pieces

**piece 1** (gold: attraction 6)
> User: I am looking for a college attraction to go to in [town](place).
> System: There are several colleges in either the [centre](place) or west part of [town](place). Which area do you prefer?
> User: The [centre](place) please.
> System: There are [13 colleges](number) in the [center](place) of [town](place). Does [entrance fee](price) matter to you?
> User: Not really, but what is the fee?
> System: Most are free, but [Corpus Christi](name) has a [2 pound fee](price), [Saint John](name)'s has a [2.50 pound fee](price), and [Trinity](name) has a [1 pound fee](price=Train requested people).

**piece 2** (gold: train 20)
> User: I need a train that leaves at [20:45](time=Train leave at) from [stevenage](place=Train destination) to [cambridge](place=Train departure)
> System: What day would you like to travel by train?
> User: I would like to leave on [Wednesday](day=Train day).
> System: There are 10 trains, [TR9448](number) leaves at [5:54](duration) would that work for you?
> User: That works can I have the travel time for that please?
> System: [TR9448](name) leaves at [05:54](duration) and arrives at [06:43](time). The travel time is [49 minutes](duration).
> User: I've mixed up my locations. I actually need a train that departs from [Cambridge](place) and goes to [Stevenage](place).
> System: I only have two trains that leave from [Cambridge](place) [Wednesday](day). The [TR9016](name) departs at [21:21](duration) and the [TR6387](name) departs [23:21](time).
> User: What is the price?
> System: Both options are [12.80 pounds](price). Would you like to book one of these options?
> User: Can you tell me the duration of travel time please?
> System: Yes travel is exactly [49 minutes](duration).
> User: What about the train ID?
> System: The train ID for the departure at [21:21](time) is [TR9016](name) and the trainID that departs at 2312 is [TR6387](name). Would you like me to book on of these for you?
> User: I need an earlier train.
> System: [TR9016](number) is the earliest departure after [20:45](time). Would you like to change your specified time?
> User: No, [TR9016](number) will do.
> System: I ha e booked your ticket. Your confirmation number is [VBAEMG3Z](number=Train confirmed reference). Can I assist you with anything else?
> User: No, that's all I need. Thank you.
> System: Thank you let me know if you need anything else.

### 25/200 +merge 0.50: 4 pieces

**piece 1** (gold: attraction 6)
> User: I am looking for a college attraction to go to in [town](place).
> System: There are several colleges in either the [centre](place) or west part of [town](place). Which area do you prefer?
> User: The [centre](place) please.
> System: There are [13 colleges](number) in the [center](place) of [town](place). Does [entrance fee](price) matter to you?
> User: Not really, but what is the fee?
> System: Most are free, but [Corpus Christi](name) has a [2 pound fee](price), [Saint John](name)'s has a [2.50 pound fee](price), and [Trinity](name) has a [1 pound fee](price=Train requested people).

**piece 2** (gold: train 14)
> User: I need a train that leaves at [20:45](time=Train leave at) from [stevenage](place=Train destination) to [cambridge](place=Train departure)
> System: What day would you like to travel by train?
> User: I would like to leave on [Wednesday](day=Train day).
> System: There are 10 trains, [TR9448](name) leaves at [5:54](duration) would that work for you?
> User: That works can I have the travel time for that please?
> System: [TR9448](name) leaves at [05:54](duration) and arrives at [06:43](time). The travel time is [49 minutes](duration).
> User: I've mixed up my locations. I actually need a train that departs from [Cambridge](place) and goes to [Stevenage](place).
> System: I only have two trains that leave from [Cambridge](place) [Wednesday](day). The [TR9016](name) departs at [21:21](duration) and the [TR6387](name) departs [23:21](time).
> User: What is the price?
> System: Both options are [12.80 pounds](price). Would you like to book one of these options?
> User: Can you tell me the duration of travel time please?
> System: Yes travel is exactly [49 minutes](duration).
> User: What about the train ID?
> System: The train ID for the departure at [21:21](time) is [TR9016](name) and the trainID that departs

**piece 3** (gold: )
> at [2312](number) is [TR6387](name)

**piece 4** (gold: train 6)
> . Would you like me to book on of these for you?
> User: I need an earlier train.
> System: [TR9016](number) is the earliest departure after [20:45](time). Would you like to change your specified time?
> User: No, [TR9016](number) will do.
> System: I ha e booked your ticket. Your confirmation number is [VBAEMG3Z](number=Train confirmed reference). Can I assist you with anything else?
> User: No, that's all I need. Thank you.
> System: Thank you let me know if you need anything else.

### 25/100 +merge 0.45: 6 pieces

**piece 1** (gold: attraction 6)
> User: I am looking for a college attraction to go to in [town](place).
> System: There are several colleges in either the [centre](place) or west part of [town](place). Which area do you prefer?
> User: The [centre](place) please.
> System: There are [13 colleges](number) in the [center](place) of [town](place). Does [entrance fee](price) matter to you?
> User: Not really, but what is the fee?
> System: Most are free, but [Corpus Christi](name) has a [2 pound fee](price), [Saint John](name)'s has a [2.50 pound fee](price), and [Trinity](name) has a [1 pound fee](price=Train requested people).

**piece 2** (gold: train 6)
> User: I need a train that leaves at [20:45](duration=Train leave at) from [stevenage](place=Train destination) to [cambridge](place=Train departure)
> System: What day would you like to travel by train?
> User: I would like to leave on [Wednesday](day=Train day).
> System: There are 10 trains, [TR9448](name) leaves at [5:54](duration) would that work for you?
> User: That works can I have the travel time for that please?
> System: [TR9448](name) leaves at [05:54](duration) and arrives at [06:43](time). The [travel time](duration) is [49 minutes](duration).

**piece 3** (gold: train 1)
> User: [I](name)'ve mixed up my locations

**piece 4** (gold: train 7)
> . I actually need a train that departs from [Cambridge](place) and goes to [Stevenage](place).
> System: I only have two trains that leave from [Cambridge](place) [Wednesday](day). The [TR9016](number) departs at [21:21](time) and the [TR6387](name) departs [23:21](time).
> User: What is the price?
> System: Both options are [12.80 pounds](price). Would you like to book one of these options?
> User: Can you tell me the duration of travel time please?
> System: Yes travel is exactly [49 minutes](duration).
> User: What about the train ID?
> System: The train ID for the departure at [21:21](time) is [TR9016](name) and the trainID that departs at 2312 is [TR6387](name)

**piece 5** (gold: )
> . Would you like me to book on of these for you?

**piece 6** (gold: train 6)
> User: I need an earlier train.
> System: [TR9016](number) is the earliest departure after [20:45](time). Would you like to change your specified time?
> User: No, [TR9016](number) will do.
> System: I ha e booked your ticket. Your confirmation number is [VBAEMG3Z](number=Train confirmed reference). Can I assist you with anything else?
> User: No, that's all I need. Thank you.
> System: Thank you let me know if you need anything else.

## Unmatched GLiNER spans, 50/400 (most frequent)

place: "cambridge" 31, number: "reference number" 15, day: "today" 11, place: "hotel" 11, place: "city centre" 9, place: "station" 9, price: "entrance fee" 8, price: "expensive" 7, day: "saturday" 7, price: "moderately priced" 7, place: "cambridge towninfo centre" 6, duration: "4 nights" 6, place: "centre" 5, day: "same day" 5, price: "cheap" 5, place: "guesthouse" 5, place: "cherry hinton" 4, place: "restaurant" 4, day: "wednesday" 4, number: "tr9016" 4, price: "moderate price range" 4, price: "price range" 4, duration: "15 minutes" 4, day: "sunday" 4, place: "north" 4, day: "friday" 3, price: "10.10 pounds" 3, place: "town" 3, time: "21:21" 3, name: "emmanuel college" 3, day: "monday" 3, place: "postcode" 3, price: "total fee" 3, place: "leicester" 3, number: "two" 3, day: "thursday" 3, price: "expensive price range" 3, place: "stansted airport" 3, duration: "105 minutes" 3, number: "tr8167" 3

## Unmatched GLiNER spans, 25/100 +merge 0.45 (most frequent)

place: "cambridge" 30, day: "today" 17, number: "reference number" 16, place: "hotel" 10, price: "entrance fee" 8, price: "expensive" 8, place: "station" 8, place: "city centre" 7, price: "total fee" 7, day: "saturday" 7, price: "moderately priced" 7, duration: "4 nights" 6, name: "i" 5, day: "same day" 5, price: "cheap" 5, place: "emmanuel college" 4, price: "moderate price range" 4, duration: "15 minutes" 4, day: "sunday" 4, price: "expensive price range" 4, day: "friday" 3, price: "10.10 pounds" 3, place: "cherry hinton" 3, place: "town" 3, place: "centre" 3, day: "wednesday" 3, number: "tr9016" 3, time: "21:21" 3, day: "monday" 3, place: "leicester" 3, day: "thursday" 3, place: "cambridge towninfo centre" 3, place: "stansted airport" 3, duration: "105 minutes" 3, time: "12:15" 3, place: "table" 3, place: "chesterton" 3, place: "north" 3, duration: "3 nights" 3, time: "18:24" 3

## Unmatched GLiNER spans, 25/200 +merge 0.50 (most frequent)

place: "cambridge" 30, number: "reference number" 20, day: "today" 17, name: "i" 11, place: "station" 9, price: "entrance fee" 8, price: "expensive" 8, place: "city centre" 8, place: "postcode" 7, place: "hotel" 7, price: "total fee" 7, day: "saturday" 7, price: "moderately priced" 7, day: "same day" 6, duration: "4 nights" 6, place: "cambridge towninfo centre" 5, price: "cheap" 5, day: "wednesday" 4, name: "emmanuel college" 4, price: "moderate price range" 4, price: "price range" 4, duration: "15 minutes" 4, day: "sunday" 4, price: "expensive price range" 4, place: "north" 4, day: "friday" 3, price: "10.10 pounds" 3, place: "cherry hinton" 3, place: "town" 3, place: "centre" 3, day: "monday" 3, place: "leicester" 3, day: "thursday" 3, place: "stansted airport" 3, duration: "105 minutes" 3, time: "12:15" 3, number: "5" 3, place: "table" 3, place: "chesterton" 3, duration: "3 nights" 3

## Unmatched GLiNER spans, 25/200 +merge 0.45 (most frequent)

place: "cambridge" 30, number: "reference number" 17, day: "today" 15, place: "station" 9, price: "entrance fee" 8, price: "expensive" 8, name: "i" 7, place: "city centre" 7, price: "total fee" 7, day: "saturday" 7, price: "moderately priced" 7, day: "same day" 6, place: "hotel" 6, duration: "4 nights" 6, price: "cheap" 5, day: "wednesday" 4, name: "emmanuel college" 4, price: "moderate price range" 4, duration: "15 minutes" 4, day: "sunday" 4, place: "cambridge towninfo centre" 4, price: "expensive price range" 4, place: "north" 4, day: "friday" 3, price: "10.10 pounds" 3, place: "cherry hinton" 3, place: "town" 3, place: "centre" 3, day: "monday" 3, place: "leicester" 3, day: "thursday" 3, place: "stansted airport" 3, duration: "105 minutes" 3, time: "12:15" 3, place: "table" 3, place: "chesterton" 3, duration: "3 nights" 3, time: "18:24" 3, time: "06:08" 2, place: "abbey pool" 2

