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

### 15/75: 16 pieces

**piece 1** (gold: train 2)
> User: Hello, I need to take a train to [Stansted airport](place=Train destination), arriving by [20:30](time=Train arrive by).
> System: The [TR7213](number) gets you there at [06:08](time). Need a ticket?

**piece 2** (gold: train 2)
> User: Maybe. I need to leave [Cambridge](place=Train departure) on [Friday](day=Train day). Will that train work?
> System: I recommend [TR1110](number). It will arrive in [Cambridge](place) at [20:08](time) on [Friday](day)

**piece 3** (gold: train 2)
> . I can book passage for you if you let me know how many tickets you need.
> User: What is the cost per ticket?
> System: The price for that ticket is 10.10 pounds

**piece 4** (gold: )
> . Would you like me to book it for you?

**piece 5** (gold: attraction 1)
> User: [No](name)

**piece 6** (gold: attraction 1)
> . Are there any swimming pools on the [east side of town](place=Attraction area)?
> System: Yes there is the [abbey pool](place) and [astroturf pitch](place=Attraction name)

**piece 7** (gold: )
> would you like their address?

**piece 8** (gold: attraction 1)
> User: Yes

**piece 9** (gold: )
> . May I have the address and postcode for the [Abbey Pool](place) please?

**piece 10** (gold: attraction 1)
> System: Yes, of course

**piece 11** (gold: )
> . They are located at [Pool Way](place), [Whitehill](place)

**piece 12** (gold: )
> Road, off [NewMarket Road](place)

**piece 13** (gold: )
> . [Their postcode](place) is [cb58nt](place)

**piece 14** (gold: )
> . Is there anything else I can do for [today](day)?

**piece 15** (gold: attraction 4)
> User: No, that is all I need. Thank you for your help.
> System: I am happy to help you with the booking, enjoy.
> User: Thanks! I appreciate your help. Bye.
> System: It's my pleasure

**piece 16** (gold: )
> . Thank you for using [Cambridge TownInfo centre](place). Goodbye.

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

### 15/75: 6 pieces

**piece 1** (gold: restaurant 1)
> User: I want to find an expensive restaurant in the [east part of town](place=Restaurant area).

**piece 2** (gold: restaurant 2)
> System: What is the food type you would prefer?
> User: I don't care

**piece 3** (gold: restaurant 1)
> . I just need to know the [address](place), [phone number](number), and [postcode](place) of the venue please.
> System: How about [Sitar Tandoori](place=Restaurant name), It's [address](place) is

**piece 4** (gold: )
> [43 High Street](place) [Cherry Hinton](place) [Cherry Hinton](place), their postcode is [C](number)

**piece 5** (gold: )
> .[B 1](number), 9 [H.X](name), and their phone number is [01223 249955](number).

**piece 6** (gold: restaurant 6)
> User: what is the food type of that [restaurant](place) ?
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

### 15/75: 16 pieces

**piece 1** (gold: attraction 3)
> User: I am looking for a college attraction to go to in [town](place).
> System: There are several colleges in either [the centre](place) or west part of [town](place). Which area do you prefer?
> User: The [centre](place) please.

**piece 2** (gold: attraction 1)
> System: There are [13 colleges](number) in the [center of town](place)

**piece 3** (gold: attraction 2)
> . Does entrance fee matter to you?
> User: Not really, but what is the fee?
> System: Most are free, but [Corpus Christi](place) has a [2 pound fee](price), [Saint John](place)'s has a [2.50 pound fee](price), and [Trinity](place) has a [1 pound fee](price=Train requested people).

**piece 4** (gold: train 4)
> User: I need a train that leaves at [20:45](time=Train leave at) from [stevenage](place=Train destination) to [cambridge](place=Train departure)
> System: What day would you like to travel by train?
> User: I would like to leave on [Wednesday](day=Train day).
> System: There are [10 trains](number), [TR9448](name) leaves at

**piece 5** (gold: )
> [5:54](number) would that work for you

**piece 6** (gold: )
> ?

**piece 7** (gold: train 3)
> User: That works can I have the travel time for that please?
> System: [TR9448](number) leaves at [05:54](duration) and arrives at [06:43](duration). The [travel time](duration) is [49 minutes](duration).
> User: I've mixed up my locations

**piece 8** (gold: )
> . I actually need a train that departs from [Cambridge](place) and goes to

**piece 9** (gold: )
> [Stevenage](place)

**piece 10** (gold: train 1)
> .
> System: I only have two trains that leave from [Cambridge](place) [Wednesday](day). The [TR9016](number) departs at [21:21](time) and the [TR6387](number) departs [23:21](time).

**piece 11** (gold: train 4)
> User: What is the price?
> System: Both options are [12.80 pounds](price). Would you like to book one of these options?
> User: Can you tell me the duration of travel time please?
> System: Yes travel is exactly [49 minutes](duration).

**piece 12** (gold: train 2)
> User: What about the train ID?
> System: The train ID for the departure at [21](time):21 is [TR9016](number) and the trainID that departs at [2312](time) is

**piece 13** (gold: )
> [TR6387](name)

**piece 14** (gold: )
> . Would you like me to book on of these for you?

**piece 15** (gold: train 3)
> User: I need an earlier train.
> System: [TR9016](name) is the earliest departure after [20:45](time). Would you like to change your specified time?
> User: No, [TR9016](name) will do.

**piece 16** (gold: train 3)
> System: I ha e booked your ticket. Your confirmation number is [VBAEMG3Z](number=Train confirmed reference). Can I assist you with anything else?
> User: No, that's all I need. Thank you.
> System: Thank you let me know if you need anything else.

## Unmatched GLiNER spans, 50/400 (most frequent)

place: "cambridge" 7, number: "tr9016" 4, place: "town" 3, name: "emmanuel college" 3, place: "cherry hinton" 2, place: "centre" 2, name: "i" 2, number: "tr9448" 2, duration: "49 minutes" 2, time: "21:21" 2, place: "cb11ln" 2, number: "tr7213" 1, time: "06:08" 1, number: "tr1110" 1, time: "20:08" 1, day: "friday" 1, price: "10.10 pounds" 1, place: "abbey pool" 1, place: "pool way" 1, place: "whitehill road" 1, place: "newmarket road" 1, place: "cb58nt" 1, day: "today" 1, place: "cambridge towninfo centre" 1, number: "phone number" 1, place: "43 high street" 1, place: "c.b 1, 9 h.x" 1, number: "01223 249955" 1, place: "restaurant" 1, number: "13 colleges" 1, place: "center" 1, price: "entrance fee" 1, name: "corpus christi" 1, price: "2 pound fee" 1, name: "saint john" 1, price: "2.50 pound fee" 1, name: "trinity" 1, time: "5:54" 1, time: "05:54" 1, time: "06:43" 1

## Unmatched GLiNER spans, 15/75 (most frequent)

place: "cambridge" 7, name: "i" 5, number: "reference number" 3, place: "emmanuel college" 3, place: "abbey pool" 2, day: "today" 2, place: "address" 2, place: "postcode" 2, place: "cherry hinton" 2, place: "town" 2, duration: "49 minutes" 2, number: "tr9016" 2, name: "tr9016" 2, day: "day" 2, number: "tr7213" 1, time: "06:08" 1, number: "tr1110" 1, time: "20:08" 1, day: "friday" 1, name: "no" 1, place: "pool way" 1, place: "whitehill" 1, place: "newmarket road" 1, place: "their postcode" 1, place: "cb58nt" 1, place: "cambridge towninfo centre" 1, number: "phone number" 1, place: "43 high street" 1, number: "c" 1, number: "b 1" 1, name: "h.x" 1, number: "01223 249955" 1, place: "restaurant" 1, place: "the centre" 1, place: "centre" 1, number: "13 colleges" 1, place: "center of town" 1, place: "corpus christi" 1, price: "2 pound fee" 1, place: "saint john" 1

