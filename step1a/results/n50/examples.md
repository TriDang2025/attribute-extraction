# Step 1a, cluster examples (best configuration by B-cubed F1)

## chroma / segment: umap5 hdbscan mcs=10,eom,ms=5 (K 4, F1 0.613)

**cluster 2** (51 units; gold: restaurant 35, attraction 15, hotel 1)
- `attraction`: System: Yes there is the abbey pool and astroturf pitch would you like their address? User: Yes. May I have the address and postcode for the Abbey Pool please? 
- `restaurant`: User: I want to find an expensive restaurant in the east part of town
- `restaurant`: . System: What is the food type you would prefer? User: I don't care. I just need to know the address, phone number, and postcode of the venue please. System: H
- `attraction`: User: I am looking for a college attraction to go to in town. System: There are several colleges in either the centre or west part of town. Which area do you pr
- `attraction`: User: Yes. I am looking for places to go in the centre area. I am looking for college. System: There are 13 choices, how do you feel about Emmanuel College? Use
- `restaurant`: User: Hello! Can you give me some info on a restaurant please? System: Would love to! What kind of food do you like?
- `restaurant`: User: Actually I am specifically looking for the Cocum restaurant, I would like to book for 7 people at 15:00 on monday if possible. System: I have a table rese
- `restaurant`: User: I am looking for a place to dine. The restaurant should serve african food and should be in the centre

**cluster 1** (36 units; gold: restaurant 13, train 7, hotel 7)
- `attraction`: User: No, that is all I need. Thank you for your help. System: I am happy to help you with the booking, enjoy. User: Thanks! I appreciate your help. Bye. System
- `restaurant`: User: what is the food type of that restaurant ? System: They serve indian food. User: Thank you, goodbye System: Thank You User: goodbye System: Good day!
- `train`: System: I ha e booked your ticket. Your confirmation number is VBAEMG3Z. Can I assist you with anything else? User: No, that's all I need. Thank you. System: Th
- `train`: System: I hope you have a great day, goodbye!
- `hotel`: User: Can you please confirm that the hotel you've booked for us offers free wi-fi? I need to be able to work while I'm there. System: Yes it has free wifi. Is 
- `restaurant`: System: It was a pleasure. Thank you for using our service. Good night.
- `restaurant`: User: Thanks! That's all I needed today. Goodbye! System: Have a nice day and thank you for calling.
- `taxi`: User: No, that is all I need today. Thanks! System: Great, have a wonderful day and enjoy your taxi ride, thank you!

**cluster 0** (35 units; gold: train 34, restaurant 1)
- `train`: User: Hello, I need to take a train to Stansted airport, arriving by 20:30. System: The TR7213 gets you there at 06:08. Need a ticket? User: Maybe. I need to le
- `train`: User: I need a train that leaves at 20:45 from stevenage to cambridge System: What day would you like to travel by train? User: I would like to leave on Wednesd
- `train`: System: There are 10 trains, TR9448 leaves at 5:54 would that work for you? User: That works can I have the travel time for that please? System: TR9448 leaves a
- `train`: System: Certainly! It's a museum in the centre at 98 king street cb11ln with free entrance. Their phone number is 01223314960. May I help find anything else? Us
- `train`: User: While in Cambridge I want to get a train that leaves on Sunday and goes to stansted airport. System: There are 19 trains that day. What time do you need t
- `train`: User: I want to depart from Cambridge by train. System: I can help with that, what day are you looking to depart on? User: I would like to leave on Saturday. Sy
- `train`: User: Hi, I am looking for information on a train. System: You came to the right place! Where would you like to go? User: I'd like to go to Cambridge and will b
- `train`: System: Your booking was successful, the total fee is 66 GBP payable at the station . Your reference number is : P6G0S9IT. Is there anything else I can help you

**cluster 3** (33 units; gold: hotel 28, taxi 4, restaurant 1)
- `hotel`: User: Thank you. I'd also like a guesthouse in the cheaper price range. Can you help me with that? System: there are several in the area of the restaurant. woul
- `taxi`: User: I need to book a taxi to come pick me up by 10:30 to take me to Midsummer House Restaurant. System: Okay! What is your departure site? User: I'm coming fr
- `taxi`: User: i want to book a taxi. The taxi should depart from la Margarita and should go to riverboat Georgina. System: What time would you like to arrive? User: I w
- `taxi`: System: Booked car type red volkswagen Contact number 07633256482 User: Thank you! That is all that I need. System: Thank you for letting us assist you today! E
- `hotel`: User: I need a hotel in the west with free parking please. System: Do you care about the price range? I have one cheap and one expensive hotel that fits your cu
- `hotel`: System: There were no hotels that matched your criteria. Would you like to try a different criteria? User: how about the north? System: How about the Ashley Hot
- `hotel`: System: Yes, your booking was successful. Your reference number is RCJDH5J4 User: Thanks Can you help me find a hotel called the university aims no university a
- `hotel`: User: I would like a 4 star luxury place to stay. It must include free wifi. But I'm cheap as all get out, so nothing too pricey. System: I have a few that matc

**noise** (2 units; gold: attraction 2)
- `attraction`: User: I'm looking for information on Broughton house gallery.
- `attraction`: System: Sheep's Green and Lammas Land Park Fen Causeway is located at Fen Causeway, Newnham road, postal code cb322ad. User: Thanks! I'm also looking for a trai

## oracle_seg / segment: umap5 hdbscan mcs=10,leaf,ms=1 (K 4, F1 0.980)

**cluster 0** (29 units; gold: train 28, restaurant 1)
- `train`: User: Hello, I need to take a train to Stansted airport, arriving by 20:30. System: The TR7213 gets you there at 06:08. Need a ticket? User: Maybe. I need to le
- `train`: User: I need a train that leaves at 20:45 from stevenage to cambridge System: What day would you like to travel by train? User: I would like to leave on Wednesd
- `train`: User: Yes, I need a train going to cambridge. System: Okay, what day would you like to travel and where will you be leaving from? User: I'll be leaving Leiceste
- `train`: User: While in Cambridge I want to get a train that leaves on Sunday and goes to stansted airport. System: There are 19 trains that day. What time do you need t
- `train`: User: I want to depart from Cambridge by train. System: I can help with that, what day are you looking to depart on? User: I would like to leave on Saturday. Sy
- `train`: User: Hi, I am looking for information on a train. System: You came to the right place! Where would you like to go? User: I'd like to go to Cambridge and will b
- `train`: User: I need some help choosing a train to Leicester. System: I can help you with that. What is your departure site and day you would like to travel? User: I wi
- `train`: User: I am looking for a train departung after 8:30 from Ely. System: I have found several trains that you can use. What is your destination? User: The train sh

**cluster 3** (28 units; gold: restaurant 28)
- `restaurant`: User: I want to find an expensive restaurant in the east part of town. System: What is the food type you would prefer? User: I don't care. I just need to know t
- `restaurant`: User: Hello! Can you give me some info on a restaurant please? System: Would love to! What kind of food do you like? User: Actually I am specifically looking fo
- `restaurant`: User: I am looking for a place to dine. The restaurant should serve african food and should be in the centre System: There is one African restuarant in the Cent
- `restaurant`: User: Hello, I am looking for a restaurant on the south side of town that serves international food. System: I'm sorry, there are no international food restaura
- `restaurant`: User: Yes, I need to find a restaurant in the same area. System: I have 9 different restaurants in the south. Lets try to narrow it down. Do you have a preferen
- `restaurant`: User: Yes please. I need an expensive restaurant located in the centre. System: You have some great choices. Do you have a preferred cuisine? User: Not really, 
- `restaurant`: User: I want to visit a restaurant that would be popular with college students and located near the center of town; can you make a recommendation? System: What 
- `restaurant`: User: Yes, I need a place to eat in that area. I want Italian food. System: I would suggest pizza express. User: Can you check if they would have a table for 7 

**cluster 1** (19 units; gold: hotel 19)
- `hotel`: User: Thank you. I'd also like a guesthouse in the cheaper price range. Can you help me with that? System: there are several in the area of the restaurant. woul
- `hotel`: User: I need a hotel in the west with free parking please. System: Do you care about the price range? I have one cheap and one expensive hotel that fits your cu
- `hotel`: User: Thank you very much! Also, can you recommend a hotel in the South part of town? I don't need internet or free parking. System: There were no hotels that m
- `hotel`: User: Thanks Can you help me find a hotel called the university aims no university arms hotel. System: I have a hotel called university arms hotel located in th
- `hotel`: User: I am looking for information in Cambridge System: What kind of information were you looking for? User: I would like a 4 star luxury place to stay. It must
- `hotel`: User: Thank you! I am also looking for a 5 star hotel. System: There are no 5 star hotels, do you want to choose something else User: Yes, can you find a place 
- `hotel`: User: Find a budget hotel with free parking in Cambridge. System: There are 10 hotels that meet your needs. Would you like to narrow your search by area? User: 
- `hotel`: User: Hello. I'm hoping to find a guesthouse in the north part of Cambridge. Are there any? System: Indeed there are. In fact, there are 11. If you'd like an in

**cluster 2** (16 units; gold: attraction 16)
- `attraction`: User: No. Are there any swimming pools on the east side of town? System: Yes there is the abbey pool and astroturf pitch would you like their address? User: Yes
- `attraction`: User: I am looking for a college attraction to go to in town. System: There are several colleges in either the centre or west part of town. Which area do you pr
- `attraction`: User: I'm looking for information on Broughton house gallery. System: Certainly! It's a museum in the centre at 98 king street cb11ln with free entrance. Their 
- `attraction`: User: Yes. I am looking for places to go in the centre area. I am looking for college. System: There are 13 choices, how do you feel about Emmanuel College? Use
- `attraction`: User: I need a cinema to go to in the south. System: The cineworld cinema is the place! User: Can you tell me the address? System: The address is cambridge leis
- `attraction`: User: Actually, I want to visit a college. Somewhere in the centre. System: I would suggest downing college, would you like the address? User: Yes, that would b
- `attraction`: User: I'm looking for things to do in the west. Can you recommend anything? System: The Whale of a Time entertainment venue is a fun choice. We also have museum
- `attraction`: User: I am also looking for an attraction to go to. Is there any in town? System: We have nearly 80 different attractions in town. First off, is there a type of

**noise** (5 units; gold: taxi 5)
- `taxi`: User: I need to book a taxi to come pick me up by 10:30 to take me to Midsummer House Restaurant. System: Okay! What is your departure site? User: I'm coming fr
- `taxi`: User: i want to book a taxi. The taxi should depart from la Margarita and should go to riverboat Georgina. System: What time would you like to arrive? User: I w
- `taxi`: User: I'll need a taxi to get me from downing college to pizza express by 17:45. can you set that up for me? System: I can do that for you! I have your taxi boo
- `taxi`: User: I also need a taxi. System: Where would you like to go and what time would you like to travel? User: I want to leave the restaurant by 09:15. Please get m
- `taxi`: User: Yes please, I need to book a taxi to the restaurant from the hotel for the dinner reservation. System: Ok, a grey honda will pick you up at the hamilton l

## value / turn: raw agglo k=50 (K 50, F1 0.380)

**cluster 10** (115 units; gold: Train day 27, Train departure 25, Train destination 25)
- `Train departure`: Cambridge | User: Maybe. I need to leave Cambridge on Friday. Will that train work?
- `Train destination`: Stansted airport | User: Hello, I need to take a train to Stansted airport, arriving by 20:30.
- `Train day`: Friday | User: Maybe. I need to leave Cambridge on Friday. Will that train work?
- `Train arrive by`: 20:30 | User: Hello, I need to take a train to Stansted airport, arriving by 20:30.
- `Train departure`: cambridge | User: I need a train that leaves at 20:45 from stevenage to cambridge
- `Train destination`: stevenage | User: I need a train that leaves at 20:45 from stevenage to cambridge
- `Train day`: Wednesday | User: I would like to leave on Wednesday.
- `Train leave at`: 20:45 | User: I need a train that leaves at 20:45 from stevenage to cambridge

**cluster 3** (87 units; gold: Train requested people 14, Hotel requested people 13, Restaurant requested people 12)
- `Train day`: Sunday | User: Sunday,can you book it for me and I need a reference number,please
- `Train requested people`: 5 | User: 5, please. Include the reference number.
- `Hotel requested people`: 7 | User: Actually I am specifically looking for the Cocum restaurant, I would like to book for 7 people at 15:00 on monday if possible.
- `Hotel requested stay`: 3 | User: The same group of people and same day for 3 nights.
- `Restaurant name`: Cocum | User: Actually I am specifically looking for the Cocum restaurant, I would like to book for 7 people at 15:00 on monday if possible.
- `Restaurant requested day`: monday | User: Actually I am specifically looking for the Cocum restaurant, I would like to book for 7 people at 15:00 on monday if possible.
- `Restaurant requested people`: 7 | User: Actually I am specifically looking for the Cocum restaurant, I would like to book for 7 people at 15:00 on monday if possible.
- `Restaurant requested time`: 15:00 | User: Actually I am specifically looking for the Cocum restaurant, I would like to book for 7 people at 15:00 on monday if possible.

**cluster 2** (57 units; gold: Restaurant area 16, Restaurant price range 11, Attraction area 8)
- `Restaurant area`: east | User: I want to find an expensive restaurant in the east part of town.
- `Restaurant price range`: expensive | User: I want to find an expensive restaurant in the east part of town.
- `Attraction type`: college | User: I am looking for a college attraction to go to in town.
- `Attraction area`: centre | User: Yes. I am looking for places to go in the centre area. I am looking for college.
- `Attraction type`: college | User: Yes. I am looking for places to go in the centre area. I am looking for college.
- `Taxi departure`: city stop restaurant | User: I'm coming from city stop restaurant.
- `Restaurant area`: centre | User: I am looking for a place to dine. The restaurant should serve african food and should be in the centre
- `Restaurant food`: african | User: I am looking for a place to dine. The restaurant should serve african food and should be in the centre

**cluster 9** (31 units; gold: Hotel confirmed reference 14, Restaurant confirmed reference 10, Train confirmed reference 5)
- `Train confirmed reference`: VBAEMG3Z | System: I ha e booked your ticket. Your confirmation number is VBAEMG3Z. Can I assist you with anything else?
- `Train confirmed reference`: 69luuzq7 | System: You will arrive at 10:54 the reference number is 69luuzq7
- `Hotel confirmed reference`: CUL9VZ04 | System: I booked your restaurant table, and the reference number is CUL9VZ04. Is there anything else I can help you with?
- `Train confirmed reference`: TNU1H19G | System: Booking was successful Your reference number is TNU1H19G. Do you need assistance with anything else?
- `Restaurant confirmed reference`: HXSPEY9N | System: Yes, they had a table available and I went ahead and booked it for you. Your reference number is HXSPEY9N. What else can I do for you?
- `Hotel confirmed reference`: ZQ6OOE4Y | System: Booking was successful. Reference number is : ZQ6OOE4Y
- `Train confirmed reference`: RCJDH5J4 | System: Yes, your booking was successful. Your reference number is RCJDH5J4
- `Restaurant confirmed reference`: OAEJMYOI | System: The booking was successful. The table will be reserved for 15 minutes. Reference number is : OAEJMYOI.

**cluster 11** (14 units; gold: Hotel type 4, Hotel price range 3, Hotel stars 3)
- `Hotel type`: guesthouse | User: Thank you. I'd also like a guesthouse in the cheaper price range. Can you help me with that?
- `Hotel area`: west | User: I need a hotel in the west with free parking please.
- `Hotel type`: guesthouse | User: I actually need a guesthouse instead of a hotel, please.
- `Hotel price range`: cheap | User: I would like a 4 star luxury place to stay. It must include free wifi. But I'm cheap as all get out, so nothing too pricey.
- `Hotel stars`: 4 | User: I would like a 4 star luxury place to stay. It must include free wifi. But I'm cheap as all get out, so nothing too pricey.
- `Hotel requested stay`: 4 | User: I would like a 4 star luxury place to stay. It must include free wifi. But I'm cheap as all get out, so nothing too pricey.
- `Hotel price range`: moderate | User: Yes, can you find a place for me with free wifi in the moderate price range?
- `Hotel internet`: Yes | User: Yes, can you find a place for me with free wifi in the moderate price range?

**cluster 20** (12 units; gold: Train confirmed reference 12)
- `Train confirmed reference`: P6G0S9IT | System: Your booking was successful, the total fee is 66 GBP payable at the station . Your reference number is : P6G0S9IT. Is there anything else I can help you with?
- `Train confirmed reference`: LTQHUT3Y | System: Booking was successful, the total fee is 64.64 GBP payable at the station. Your reference number is: LTQHUT3Y. Can I assist with anything else today?
- `Train confirmed reference`: H4BIFD0U | System: Booking was successful, the total fee is 40.4 GBP payable at the station. Reference number is : H4BIFD0U. Will there be anything else today?
- `Train confirmed reference`: 698RE4W1 | System: Your booking was successful! The reference number is 698RE4W1. The total fee of 17.89 is payable at the station.
- `Train confirmed reference`: JI5O0VTT | System: I have booked your train. The reference number is JI5O0VTT. The fee is 7.84 GBP payable at the station.
- `Train confirmed reference`: MU3UYQCK | System: Booking was successful, the total fee is 66 GBP payable at the station . Reference number is : MU3UYQCK.
- `Train confirmed reference`: GJ3062PE | System: Done - your reference number is GJ3062PE. The total fee is 37.79 GPB which you can pay at the station.
- `Train confirmed reference`: TYGH2E4A | System: Great, your reference number is TYGH2E4A, and the total fee payable at the station is 450.6 GBP.

**cluster 36** (12 units; gold: Restaurant food 2, Hotel stars 2, Train destination 2)
- `Restaurant food`: french | User: I'm hoping to find a french restaurant in Cambridge.
- `Hotel area`: north | User: Hello. I'm hoping to find a guesthouse in the north part of Cambridge. Are there any?
- `Hotel stars`: 3 | User: I'm curious about the 3-star lodging options available in Cambridge.
- `Train destination`: Cambridge | User: I am traveling to Cambridge and would like to find a local restaurant. I want to arrive by train at noon.
- `Train arrive by`: noon | User: I am traveling to Cambridge and would like to find a local restaurant. I want to arrive by train at noon.
- `Restaurant area`: centre | User: I want to find a Chinese restaurant in the centre of Cambridge.
- `Restaurant food`: Chinese | User: I want to find a Chinese restaurant in the centre of Cambridge.
- `Hotel name`: Lensfield hotel | User: Hi, I'm looking for any information that you have on the Lensfield hotel in Cambridge.

**cluster 0** (11 units; gold: Restaurant food 8, Restaurant price range 1, Restaurant confirmed name 1)
- `Restaurant food`: Chinese | User: How about Chinese food?
- `Restaurant food`: indian | User: We eat Pizza Hut way to much. Can you try something with indian food? It is a special occasion so it can be expensive.
- `Restaurant price range`: expensive | User: We eat Pizza Hut way to much. Can you try something with indian food? It is a special occasion so it can be expensive.
- `Restaurant food`: Italian | User: Yes, I need a place to eat in that area. I want Italian food.
- `Restaurant confirmed name`: pizza express | System: I would suggest pizza express.
- `Restaurant food`: British | User: How about British food?
- `Restaurant food`: indian | User: Sure, how about one that serves indian food in that area.
- `Restaurant food`: Indian | User: Yes. I would like to eat Indian food.

**cluster 1** (8 units; gold: Hotel name 4, Hotel confirmed name 3, Hotel requested day 1)
- `Hotel name`: finches Bed and Breakfast | System: The finches Bed and Breakfast fits your needs. When would you like to stay?
- `Hotel requested day`: Monday | System: I was able to book you a room for seven people for three nights, starting Monday, at Finches Bed and Breakfast. Reference number is CUL9VZ04. Is there anything else?
- `Hotel confirmed name`: finches Bed and Breakfast | System: The finches Bed and Breakfast fits your needs. When would you like to stay?
- `Hotel name`: alexander bed and breakfast | System: alexander bed and breakfast would be perfect for you. Shall i book it ?
- `Hotel name`: Cambridge Belfry | System: The Cambridge Belfry fits your requirements, would you like to book a reservation there?
- `Hotel confirmed name`: The Cambridge Belfry | System: The Cambridge Belfry fits your requirements, would you like to book a reservation there?
- `Hotel name`: Alexander Bed and Breakfast | System: Alright, might I suggest the Alexander Bed and Breakfast then?
- `Hotel confirmed name`: Alexander Bed and Breakfast | System: Alright, might I suggest the Alexander Bed and Breakfast then?

**cluster 42** (8 units; gold: Taxi destination 3, Taxi departure 2, Taxi arrive by 2)
- `Taxi destination`: Midsummer House Restaurant | User: I need to book a taxi to come pick me up by 10:30 to take me to Midsummer House Restaurant.
- `Taxi leave at`: 10:30 | User: I need to book a taxi to come pick me up by 10:30 to take me to Midsummer House Restaurant.
- `Taxi departure`: downing college | User: I'll need a taxi to get me from downing college to pizza express by 17:45. can you set that up for me?
- `Taxi destination`: pizza express | User: I'll need a taxi to get me from downing college to pizza express by 17:45. can you set that up for me?
- `Taxi arrive by`: 17:45 | User: I'll need a taxi to get me from downing college to pizza express by 17:45. can you set that up for me?
- `Taxi departure`: hamilton lodge | System: Ok, a grey honda will pick you up at the hamilton lodge in time to arrive at restaurant alimentum for your 10:00 reservations. Taxi contact number is 07242149665. Anything else?
- `Taxi destination`: restaurant alimentum | System: Ok, a grey honda will pick you up at the hamilton lodge in time to arrive at restaurant alimentum for your 10:00 reservations. Taxi contact number is 07242149665. Anything else?
- `Taxi arrive by`: 10:00 | System: Ok, a grey honda will pick you up at the hamilton lodge in time to arrive at restaurant alimentum for your 10:00 reservations. Taxi contact number is 07242149665. Anything else?

**cluster 7** (7 units; gold: Restaurant area 3, Hotel name 1, Hotel confirmed name 1)
- `Restaurant area`: north | System: There are two. Both are expensive. One is in the north and one is in the centre. Do you have a preference?
- `Restaurant area`: west | System: It is also in the west side area, located at 17 Magdalene Street City Centre. Would you like to make a reservation?
- `Hotel name`: city centre north b and b | System: I would suggest this one city centre north b and b.
- `Hotel confirmed name`: city centre north b and b | System: I would suggest this one city centre north b and b.
- `Hotel area`: centre | System: I'm sorry for the confusion. There are two expensive hotels with 3 stars and parking. Do you prefer the centre or the south?
- `Restaurant area`: centre | System: I have 5 of them. 4 in the centre area and one in the south. Would you like more information?
- `Restaurant requested people`: 4 | System: I have 5 of them. 4 in the centre area and one in the south. Would you like more information?

**cluster 41** (7 units; gold: Hotel name 2, Hotel confirmed name 2, Hotel requested people 1)
- `Hotel requested people`: 4 | System: Indeed there are. In fact, there are 11. If you'd like an inexpensive, 4 star guesthouse with free internet and free parking, Worth House is a good choice.
- `Hotel name`: Acorn Guest house | System: There are 8 moderately priced guesthouses in the north. May I suggest the 4 star Acorn Guest house?
- `Hotel requested stay`: 4 | System: There are 8 moderately priced guesthouses in the north. May I suggest the 4 star Acorn Guest house?
- `Hotel confirmed name`: Acorn Guest house | System: There are 8 moderately priced guesthouses in the north. May I suggest the 4 star Acorn Guest house?
- `Hotel name`: acorn guest house | System: The acorn guest house is available in your selected region. It's moderately priced and includes free internet and parking.
- `Hotel type`: guest house | System: The acorn guest house is available in your selected region. It's moderately priced and includes free internet and parking.
- `Hotel confirmed name`: acorn guest house | System: The acorn guest house is available in your selected region. It's moderately priced and includes free internet and parking.

**cluster 8** (6 units; gold: Hotel name 3, Hotel confirmed name 2, Hotel requested stay 1)
- `Hotel name`: Ashley Hotel | System: How about the Ashley Hotel? They have free internet and parking, though.
- `Hotel name`: university arms hotel | User: Thanks Can you help me find a hotel called the university aims no university arms hotel.
- `Hotel confirmed name`: university arms hotel | User: Thanks Can you help me find a hotel called the university aims no university arms hotel.
- `Hotel name`: Ashley Hotel | User: I'd like more information about the Ashley Hotel, can you help?
- `Hotel requested stay`: 2 | System: The ashley hotel is a moderately priced 2-star hotel in the north part of town. It offers free wifi and free parking.
- `Hotel confirmed name`: Ashley Hotel | User: I'd like more information about the Ashley Hotel, can you help?

**cluster 15** (6 units; gold: Hotel stars 2, Hotel parking 1, Hotel internet 1)
- `Hotel parking`: Yes | User: Yes please tell me their postcode and star rating.
- `Hotel internet`: Yes | User: Yes please tell me their postcode and star rating.
- `Hotel stars`: 4 | User: How about a 4 star rating?
- `Hotel area`: west | User: I would like it to have a four star rating and be located on the west side.
- `Hotel price range`: expensive | User: How about something with 4 stars and something expensive.
- `Hotel stars`: 4 | User: How about something with 4 stars and something expensive.

**cluster 6** (5 units; gold: Attraction area 2, Attraction type 1, Attraction name 1)
- `Attraction area`: centre | System: There are many in the centre of town,what type are you looking for a church,or swimming or a park ?
- `Attraction type`: museum | System: There are 44 great attractions to visit! Is there a certain type you were looking for? Perhaps a museum or theatre?
- `Attraction name`: Cambridge Arts Theatre | System: The Cambridge Arts Theatre is a popular attraction in the city centre. Does that sound good to you?
- `Attraction area`: centre | System: I have lots of attractions in the centre of town. Can you tell me what type of attraction you would be interested in?
- `Taxi destination`: Cambridge Arts Theatre | System: The Cambridge Arts Theatre is a popular attraction in the city centre. Does that sound good to you?

**cluster 17** (4 units; gold: Restaurant price range 2, Hotel internet 1, Hotel price range 1)
- `Hotel internet`: Yes | User: Yes that's find are the in the moderate price range?
- `Restaurant price range`: moderate | System: There are 3 Turkish restaurants in the centre. Would you prefer expensive or moderate price range?
- `Hotel price range`: moderate | User: Can you check for moderate price range instead?
- `Restaurant price range`: moderate | System: There are 10 choices and we have cheap, moderate and expensive options, any preference?

**cluster 4** (3 units; gold: Attraction name 1, Hotel name 1, Hotel confirmed name 1)
- `Attraction name`: cineworld cinema | System: The cineworld cinema is the place!
- `Hotel name`: cityroomz | System: There is one option available. It is cityroomz. Do you want to book?
- `Hotel confirmed name`: cityroomz | System: There is one option available. It is cityroomz. Do you want to book?

**cluster 12** (3 units; gold: Restaurant name 2, Restaurant confirmed name 1)
- `Restaurant name`: Thanh binh | System: Thanh binh is located in the west part of town and is in the cheap price range. Would you like their information?
- `Restaurant name`: Thanh Binh | System: I found Thanh Binh; would you like me to make you a reservation?
- `Restaurant confirmed name`: Thanh Binh | System: I found Thanh Binh; would you like me to make you a reservation?

**cluster 14** (3 units; gold: Restaurant confirmed name 1, Hotel internet 1, Restaurant area 1)
- `Restaurant confirmed name`: Restaurant Two Two | System: I'm sorry, Restaurant Two Two doesn't have availability then. Would you like to try a different day or time?
- `Hotel internet`: Yes | System: Yes, I tried Sunday but it isn't available. Can you shorten your stay at all?
- `Restaurant area`: centre | System: Neither of the restaurants in the centre are available at that time. Would you like to try a different time?

**cluster 18** (3 units; gold: Restaurant name 2, Restaurant confirmed name 1)
- `Restaurant name`: cambridge chop house | System: The cambridge chop house serves british food, it is in the centre of town and is in the expensive price range.
- `Restaurant name`: copper kettle | System: No, I'm sorry the ugly duckling is in the expensive price range. The copper kettle serves british food and is moderately priced. Would you like a reservation for it?
- `Restaurant confirmed name`: The copper kettle | System: No, I'm sorry the ugly duckling is in the expensive price range. The copper kettle serves british food and is moderately priced. Would you like a reservation for it?

**cluster 46** (3 units; gold: Restaurant name 2, Restaurant confirmed name 1)
- `Restaurant name`: tandoori palace | System: There are 5 results for restaurants serving indian food, the first is tandoori palace located at 68 Histon Road Chesterton. Would you like a reservation and for how many?
- `Restaurant confirmed name`: tandoori palace | System: There are 5 results for restaurants serving indian food, the first is tandoori palace located at 68 Histon Road Chesterton. Would you like a reservation and for how many?
- `Restaurant name`: tandoori palace | System: The tandoori palace meets your criteria. It is located at 68 Histon Road Chesterton.

**cluster 16** (2 units; gold: Attraction area 1, Attraction type 1)
- `Attraction area`: east | User: No. Are there any swimming pools on the east side of town?
- `Attraction type`: swimming pools | User: No. Are there any swimming pools on the east side of town?

**cluster 5** (2 units; gold: Attraction name 2)
- `Attraction name`: Broughton house gallery | User: I'm looking for information on Broughton house gallery.
- `Attraction name`: Cherry Hinton Water Play | User: I am looking for information about the the Cherry Hinton Water Play

**cluster 13** (2 units; gold: Hotel name 1, Hotel confirmed name 1)
- `Hotel name`: Avalon | System: I have begun a booking for you at Avalon. How many days will you be staying?
- `Hotel confirmed name`: Avalon | System: I have begun a booking for you at Avalon. How many days will you be staying?

**cluster 23** (2 units; gold: Hotel name 1, Hotel confirmed name 1)
- `Hotel name`: Gonville Hotel | System: All right, sir, that would be the Gonville Hotel on Gonville Place.
- `Hotel confirmed name`: Gonville Hotel | System: All right, sir, that would be the Gonville Hotel on Gonville Place.

**cluster 24** (2 units; gold: Restaurant name 1, Restaurant confirmed name 1)
- `Restaurant name`: travellers rest | System: There's actually two expensive places, graffiti and travellers rest. Which would you prefer?
- `Restaurant confirmed name`: travellers rest | System: There's actually two expensive places, graffiti and travellers rest. Which would you prefer?

**cluster 19** (2 units; gold: Hotel type 1, Hotel requested day 1)
- `Hotel type`: guest house | User: I would also like to book at a guest house named Aylesbray Lodge, starting Monday.
- `Hotel requested day`: Monday | User: I would also like to book at a guest house named Aylesbray Lodge, starting Monday.

**cluster 22** (2 units; gold: Restaurant area 1, Restaurant food 1)
- `Restaurant area`: north | User: Can you recommend a good restaurant in the north part of town that serves Australasian food?
- `Restaurant food`: modern european | User: Yes, are there any modern european restaurants in that area?

**cluster 27** (2 units; gold: Restaurant name 1, Restaurant confirmed name 1)
- `Restaurant name`: Jinling Noodle Bar | System: I recommend Jinling Noodle Bar. It's located at 11 Peas Hill City Center. Would you like me to book a table for you?
- `Restaurant confirmed name`: Jinling Noodle Bar | System: I recommend Jinling Noodle Bar. It's located at 11 Peas Hill City Center. Would you like me to book a table for you?

**cluster 31** (2 units; gold: Restaurant name 1, Restaurant confirmed name 1)
- `Restaurant name`: don pasquale pizzeria | System: How about cafe uno or don pasquale pizzeria?
- `Restaurant confirmed name`: don pasquale pizzeria | System: How about cafe uno or don pasquale pizzeria?

**cluster 26** (2 units; gold: Hotel name 1, Hotel confirmed name 1)
- `Hotel name`: hamilton lodge | System: Yes, hamilton lodge is located on 156 chesterton road.
- `Hotel confirmed name`: hamilton lodge | System: Yes, hamilton lodge is located on 156 chesterton road.

**cluster 47** (1 units; gold: Attraction name 1)
- `Attraction name`: abbey pool and astroturf pitch | System: Yes there is the abbey pool and astroturf pitch would you like their address?

**cluster 33** (1 units; gold: Restaurant name 1)
- `Restaurant name`: Sitar Tandoori | System: How about Sitar Tandoori, It's address is 43 High Street Cherry Hinton Cherry Hinton, their postcode is C.B 1, 9 H.X, and their phone number is 01223 249955.

**cluster 39** (1 units; gold: Train requested people 1)
- `Train requested people`: 1 | System: Most are free, but Corpus Christi has a 2 pound fee, Saint John's has a 2.50 pound fee, and Trinity has a 1 pound fee.

**cluster 45** (1 units; gold: Hotel price range 1)
- `Hotel price range`: cheap | System: no it is cheap. will that do for you?

**cluster 28** (1 units; gold: Restaurant name 1)
- `Restaurant name`: the Lucky Star | System: There are the Peking Restaurant, which is expensive, the Good Luck Chinese Food Takeaway, which is also expensive, and the Lucky Star, which is cheap.

**cluster 32** (1 units; gold: Taxi destination 1)
- `Taxi destination`: riverboat Georgina | User: i want to book a taxi. The taxi should depart from la Margarita and should go to riverboat Georgina.

**cluster 40** (1 units; gold: Attraction name 1)
- `Attraction name`: Whale of a Time | System: The Whale of a Time entertainment venue is a fun choice. We also have museums and colleges to visit, if you'd like something quieter.

**cluster 44** (1 units; gold: Restaurant confirmed reference 1)
- `Restaurant confirmed reference`: TIYE4F1Y | System: Your table at Panahar has been reserved for 15 minutes starting at 15:15 on Sunday. Your reference number is TIYE4F1Y. Can I help you with anything else?

**cluster 43** (1 units; gold: Hotel requested people 1)
- `Hotel requested people`: 3 | User: The area doesn't matter as long as they have a room available for 3 people staying 4 nights.

**cluster 35** (1 units; gold: Restaurant name 1)
- `Restaurant name`: La Raza | User: Do you have information on La Raza?

**cluster 49** (1 units; gold: Restaurant confirmed reference 1)
- `Restaurant confirmed reference`: PDELCKQS | System: Great the reference is PDELCKQS. Thank you.

**cluster 25** (1 units; gold: Train requested people 1)
- `Train requested people`: one | User: Just one seat.

**cluster 48** (1 units; gold: Restaurant confirmed name 1)
- `Restaurant confirmed name`: anatolia | System: I have pulled up 3. How about anatolia, they are moderately priced.

**cluster 29** (1 units; gold: Attraction name 1)
- `Attraction name`: Mumford theatre | System: There is the Mumford theatre, it is located at Anglia Ruskin Enterprise, East Road in the Centre area.

**cluster 30** (1 units; gold: Taxi departure 1)
- `Taxi departure`: The oak bistro | System: The oak bistro is an excellent choice for british food. The address is 6 Lensfield Road.

**cluster 37** (1 units; gold: Attraction name 1)
- `Attraction name`: Ballare | System: There are 5 different nightclubs in that area. Might I suggest Ballare. Would you like more info?

**cluster 21** (1 units; gold: Restaurant name 1)
- `Restaurant name`: Nirala | System: The Nirala is located at 7 Milton Street Chesterton.

**cluster 38** (1 units; gold: Train departure 1)
- `Train departure`: Cambridge | System: There are 10 trains leaving from Cambridge to Ely. Is there a particular departure or arrival time you would prefer?

**cluster 34** (1 units; gold: Restaurant requested time 1)
- `Restaurant requested time`: 10:00 | User: How about 10:00 on the same day as before?

## value / value: raw agglo thr=0.4 (K 91, F1 0.520)

**cluster 10** (68 units; gold: Train requested people 17, Hotel requested people 15, Hotel requested stay 15)
- `Train requested people`: 1
- `Train requested people`: 5
- `Hotel requested people`: 7
- `Hotel requested stay`: 3
- `Restaurant requested people`: 7
- `Train requested people`: 1
- `Restaurant requested people`: 7
- `Restaurant requested people`: 5

**cluster 32** (56 units; gold: Train day 28, Hotel requested day 15, Restaurant requested day 13)
- `Train day`: Friday
- `Train day`: Wednesday
- `Train day`: Sunday
- `Train day`: Sunday
- `Hotel requested day`: Monday
- `Restaurant requested day`: monday
- `Train day`: Saturday
- `Restaurant requested day`: Sunday

**cluster 18** (44 units; gold: Train leave at 16, Restaurant requested time 13, Train arrive by 10)
- `Train arrive by`: 20:30
- `Train leave at`: 20:45
- `Train arrive by`: 11:30
- `Train leave at`: 13:15
- `Restaurant requested time`: 15:00
- `Taxi leave at`: 10:30
- `Train leave at`: 13:00
- `Taxi arrive by`: 17:15

**cluster 14** (31 units; gold: Train destination 15, Train departure 11, Restaurant name 1)
- `Train departure`: Cambridge
- `Train departure`: cambridge
- `Train destination`: cambridge
- `Train departure`: Cambridge
- `Train departure`: Cambridge
- `Train destination`: Cambridge
- `Train departure`: Cambridge
- `Train destination`: Cambridge

**cluster 15** (23 units; gold: Restaurant area 12, Hotel area 6, Attraction area 5)
- `Attraction area`: east
- `Restaurant area`: east
- `Restaurant area`: south
- `Attraction area`: south
- `Restaurant area`: south
- `Attraction area`: west
- `Restaurant area`: West
- `Hotel area`: west

**cluster 4** (22 units; gold: Restaurant area 10, Attraction area 6, Attraction type 3)
- `Attraction area`: centre
- `Restaurant area`: centre
- `Attraction type`: cinema
- `Restaurant area`: centre
- `Attraction area`: centre
- `Restaurant area`: centre
- `Restaurant area`: centre
- `Attraction area`: centre

**cluster 6** (18 units; gold: Hotel type 9, Hotel name 5, Hotel confirmed name 4)
- `Hotel type`: guesthouse
- `Hotel type`: guesthouse
- `Hotel name`: Ashley Hotel
- `Hotel type`: hotel
- `Hotel name`: university arms hotel
- `Hotel confirmed name`: university arms hotel
- `Hotel name`: Gonville Hotel
- `Hotel type`: hotel

**cluster 36** (14 units; gold: Restaurant price range 10, Hotel price range 4)
- `Restaurant price range`: expensive
- `Hotel price range`: cheap
- `Restaurant price range`: expensive
- `Restaurant price range`: expensive
- `Restaurant price range`: cheap
- `Restaurant price range`: expensive
- `Hotel price range`: cheap
- `Restaurant price range`: expensive

**cluster 31** (10 units; gold: Hotel internet 6, Hotel parking 4)
- `Hotel internet`: Yes
- `Hotel parking`: Yes
- `Hotel parking`: Yes
- `Hotel internet`: Yes
- `Hotel internet`: Yes
- `Hotel parking`: Yes
- `Hotel parking`: Yes
- `Hotel internet`: Yes

**cluster 8** (10 units; gold: Restaurant food 10)
- `Restaurant food`: Chinese
- `Restaurant food`: indian
- `Restaurant food`: Italian
- `Restaurant food`: British
- `Restaurant food`: indian
- `Restaurant food`: Indian
- `Restaurant food`: Indian
- `Restaurant food`: Chinese

**cluster 46** (7 units; gold: Train destination 5, Train departure 2)
- `Train destination`: Stansted airport
- `Train destination`: stansted airport
- `Train destination`: Stansted Airport
- `Train destination`: Stansted Airport
- `Train destination`: stansted airport
- `Train departure`: stansted airport
- `Train departure`: stansted airport

**cluster 72** (7 units; gold: Restaurant price range 4, Hotel price range 3)
- `Hotel price range`: moderate
- `Restaurant price range`: moderate
- `Hotel price range`: moderate
- `Restaurant price range`: moderate
- `Restaurant price range`: moderate
- `Hotel price range`: moderate
- `Restaurant price range`: moderate

**cluster 23** (5 units; gold: Train departure 3, Train destination 2)
- `Train departure`: Leicester
- `Train destination`: Leicester
- `Train departure`: leicester
- `Train destination`: Leicester
- `Train departure`: leicester

**cluster 0** (5 units; gold: Hotel confirmed reference 2, Train confirmed reference 2, Restaurant confirmed reference 1)
- `Hotel confirmed reference`: YQBMMCJ6
- `Train confirmed reference`: MU3UYQCK
- `Restaurant confirmed reference`: R3VOQJMB
- `Train confirmed reference`: Y3MAVYRQ
- `Hotel confirmed reference`: R1E3QVGT

**cluster 38** (4 units; gold: Attraction type 3, Taxi departure 1)
- `Attraction type`: college
- `Attraction type`: college
- `Attraction type`: college
- `Taxi departure`: downing college

**cluster 16** (4 units; gold: Restaurant confirmed name 2, Taxi destination 1, Restaurant name 1)
- `Restaurant confirmed name`: pizza express
- `Taxi destination`: pizza express
- `Restaurant name`: don pasquale pizzeria
- `Restaurant confirmed name`: don pasquale pizzeria

**cluster 42** (4 units; gold: Hotel name 2, Hotel confirmed name 2)
- `Hotel name`: Acorn Guest house
- `Hotel confirmed name`: Acorn Guest house
- `Hotel name`: acorn guest house
- `Hotel confirmed name`: acorn guest house

**cluster 25** (3 units; gold: Restaurant name 2, Restaurant confirmed name 1)
- `Restaurant name`: Thanh binh
- `Restaurant name`: Thanh Binh
- `Restaurant confirmed name`: Thanh Binh

**cluster 43** (3 units; gold: Train departure 3)
- `Train departure`: Peterborough
- `Train departure`: peterborough
- `Train departure`: Peterborough

**cluster 3** (3 units; gold: Hotel confirmed reference 2, Train confirmed reference 1)
- `Train confirmed reference`: P6G0S9IT
- `Hotel confirmed reference`: ZQ6OOE4Y
- `Hotel confirmed reference`: E6UVD9OL

**cluster 22** (3 units; gold: Hotel name 2, Hotel confirmed name 1)
- `Hotel name`: alexander bed and breakfast
- `Hotel name`: Alexander Bed and Breakfast
- `Hotel confirmed name`: Alexander Bed and Breakfast

**cluster 20** (3 units; gold: Train departure 2, Train destination 1)
- `Train departure`: Norwich
- `Train destination`: norwich
- `Train departure`: Norwich

**cluster 48** (3 units; gold: Restaurant name 2, Restaurant confirmed name 1)
- `Restaurant name`: tandoori palace
- `Restaurant confirmed name`: tandoori palace
- `Restaurant name`: tandoori palace

**cluster 60** (3 units; gold: Hotel name 1, Hotel confirmed name 1, Taxi departure 1)
- `Hotel name`: hamilton lodge
- `Hotel confirmed name`: hamilton lodge
- `Taxi departure`: hamilton lodge

**cluster 90** (2 units; gold: Hotel name 1, Hotel confirmed name 1)
- `Hotel name`: finches Bed and Breakfast
- `Hotel confirmed name`: finches Bed and Breakfast

**cluster 65** (2 units; gold: Restaurant name 1, Restaurant confirmed name 1)
- `Restaurant name`: Cocum
- `Restaurant confirmed name`: Cocum

**cluster 21** (2 units; gold: Restaurant food 2)
- `Restaurant food`: african
- `Restaurant food`: french

**cluster 1** (2 units; gold: Restaurant name 1, Taxi departure 1)
- `Restaurant name`: the Lucky Star
- `Taxi departure`: The oak bistro

**cluster 26** (2 units; gold: Restaurant confirmed reference 1, Hotel confirmed reference 1)
- `Restaurant confirmed reference`: HXSPEY9N
- `Hotel confirmed reference`: IHGCTXH9

**cluster 68** (2 units; gold: Restaurant name 1, Restaurant confirmed name 1)
- `Restaurant name`: panahar
- `Restaurant confirmed name`: panahar

**cluster 12** (2 units; gold: Restaurant confirmed reference 1, Train confirmed reference 1)
- `Restaurant confirmed reference`: TIYE4F1Y
- `Train confirmed reference`: TYGH2E4A

**cluster 33** (2 units; gold: Train departure 1, Train destination 1)
- `Train departure`: Ely
- `Train destination`: ely

**cluster 17** (2 units; gold: Restaurant confirmed name 1, Hotel requested stay 1)
- `Restaurant confirmed name`: Restaurant Two Two
- `Hotel requested stay`: two

**cluster 41** (2 units; gold: Hotel name 1, Hotel confirmed name 1)
- `Hotel name`: Avalon
- `Hotel confirmed name`: Avalon

**cluster 19** (2 units; gold: Restaurant food 2)
- `Restaurant food`: turkish
- `Restaurant food`: Turkish

**cluster 9** (2 units; gold: Train confirmed reference 2)
- `Train confirmed reference`: LTQHUT3Y
- `Train confirmed reference`: TJGHMT3I

**cluster 40** (2 units; gold: Train departure 1, Train destination 1)
- `Train departure`: Broxbourne
- `Train destination`: Broxbourne

**cluster 35** (2 units; gold: Train destination 1, Train departure 1)
- `Train destination`: Kings Lynn
- `Train departure`: Kings Lynn

**cluster 7** (2 units; gold: Restaurant confirmed reference 2)
- `Restaurant confirmed reference`: G7THDK3O
- `Restaurant confirmed reference`: 64UQ7M3G

**cluster 52** (2 units; gold: Restaurant name 1, Restaurant confirmed name 1)
- `Restaurant name`: travellers rest
- `Restaurant confirmed name`: travellers rest

**cluster 37** (2 units; gold: Restaurant name 1, Restaurant confirmed name 1)
- `Restaurant name`: copper kettle
- `Restaurant confirmed name`: The copper kettle

**cluster 5** (2 units; gold: Hotel confirmed reference 1, Train confirmed reference 1)
- `Hotel confirmed reference`: G2YMGI0L
- `Train confirmed reference`: GGE66KI2

**cluster 2** (2 units; gold: Hotel confirmed reference 2)
- `Hotel confirmed reference`: FCQZW2OT
- `Hotel confirmed reference`: FC2BDIC9

**cluster 11** (2 units; gold: Restaurant confirmed reference 1, Hotel confirmed reference 1)
- `Restaurant confirmed reference`: O9WM39XJ
- `Hotel confirmed reference`: RWZ39FBX

**cluster 44** (2 units; gold: Restaurant name 2)
- `Restaurant name`: Nirala
- `Restaurant name`: nirala

**cluster 29** (2 units; gold: Restaurant name 1, Restaurant confirmed name 1)
- `Restaurant name`: Jinling Noodle Bar
- `Restaurant confirmed name`: Jinling Noodle Bar

**cluster 13** (2 units; gold: Hotel name 1, Hotel confirmed name 1)
- `Hotel name`: cityroomz
- `Hotel confirmed name`: cityroomz

**cluster 34** (2 units; gold: Restaurant confirmed name 1, Taxi destination 1)
- `Restaurant confirmed name`: restaurant alimentum
- `Taxi destination`: restaurant alimentum

**cluster 82** (1 units; gold: Attraction name 1)
- `Attraction name`: abbey pool and astroturf pitch

**cluster 81** (1 units; gold: Attraction type 1)
- `Attraction type`: swimming pools

**cluster 70** (1 units; gold: Restaurant name 1)
- `Restaurant name`: Sitar Tandoori

**cluster 49** (1 units; gold: Train destination 1)
- `Train destination`: stevenage

**cluster 75** (1 units; gold: Train confirmed reference 1)
- `Train confirmed reference`: VBAEMG3Z

**cluster 67** (1 units; gold: Attraction name 1)
- `Attraction name`: Broughton house gallery

**cluster 73** (1 units; gold: Train confirmed reference 1)
- `Train confirmed reference`: 69luuzq7

**cluster 53** (1 units; gold: Hotel confirmed reference 1)
- `Hotel confirmed reference`: CUL9VZ04

**cluster 63** (1 units; gold: Restaurant confirmed reference 1)
- `Restaurant confirmed reference`: BPE8LVHA

**cluster 88** (1 units; gold: Taxi departure 1)
- `Taxi departure`: city stop restaurant

**cluster 66** (1 units; gold: Taxi destination 1)
- `Taxi destination`: Midsummer House Restaurant

**cluster 62** (1 units; gold: Attraction name 1)
- `Attraction name`: cineworld cinema

**cluster 47** (1 units; gold: Train confirmed reference 1)
- `Train confirmed reference`: TNU1H19G

**cluster 79** (1 units; gold: Taxi destination 1)
- `Taxi destination`: riverboat Georgina

**cluster 83** (1 units; gold: Attraction name 1)
- `Attraction name`: Whale of a Time

**cluster 56** (1 units; gold: Train confirmed reference 1)
- `Train confirmed reference`: RCJDH5J4

**cluster 85** (1 units; gold: Restaurant confirmed reference 1)
- `Restaurant confirmed reference`: OAEJMYOI

**cluster 59** (1 units; gold: Restaurant name 1)
- `Restaurant name`: La Raza

**cluster 76** (1 units; gold: Hotel confirmed reference 1)
- `Hotel confirmed reference`: 72YCMLXX

**cluster 89** (1 units; gold: Restaurant food 1)
- `Restaurant food`: vietnamese

**cluster 57** (1 units; gold: Restaurant confirmed reference 1)
- `Restaurant confirmed reference`: PDELCKQS

**cluster 74** (1 units; gold: Train departure 1)
- `Train departure`: bishops stortford

**cluster 86** (1 units; gold: Train confirmed reference 1)
- `Train confirmed reference`: H4BIFD0U

**cluster 77** (1 units; gold: Attraction name 1)
- `Attraction name`: Cherry Hinton Water Play

**cluster 84** (1 units; gold: Train confirmed reference 1)
- `Train confirmed reference`: 698RE4W1

**cluster 80** (1 units; gold: Train confirmed reference 1)
- `Train confirmed reference`: JI5O0VTT

**cluster 50** (1 units; gold: Hotel confirmed reference 1)
- `Hotel confirmed reference`: PU74EXCQ

**cluster 55** (1 units; gold: Restaurant name 1)
- `Restaurant name`: graffiti

**cluster 61** (1 units; gold: Restaurant confirmed name 1)
- `Restaurant confirmed name`: anatolia

**cluster 71** (1 units; gold: Train confirmed reference 1)
- `Train confirmed reference`: GJ3062PE

**cluster 64** (1 units; gold: Restaurant confirmed reference 1)
- `Restaurant confirmed reference`: OY2LNXFW

**cluster 58** (1 units; gold: Attraction name 1)
- `Attraction name`: Mumford theatre

**cluster 27** (1 units; gold: Hotel confirmed reference 1)
- `Hotel confirmed reference`: WYO54VCI

**cluster 45** (1 units; gold: Train departure 1)
- `Train departure`: birmingham new street

**cluster 87** (1 units; gold: Attraction name 1)
- `Attraction name`: Ballare

**cluster 39** (1 units; gold: Attraction type 1)
- `Attraction type`: nightclub

**cluster 30** (1 units; gold: Train confirmed reference 1)
- `Train confirmed reference`: RJOUA7E1

**cluster 54** (1 units; gold: Restaurant confirmed reference 1)
- `Restaurant confirmed reference`: 42XEDGDF

**cluster 24** (1 units; gold: Train confirmed reference 1)
- `Train confirmed reference`: 1R61PO9r

**cluster 28** (1 units; gold: Hotel confirmed reference 1)
- `Hotel confirmed reference`: NWPEWP4X

**cluster 51** (1 units; gold: Restaurant confirmed reference 1)
- `Restaurant confirmed reference`: DDLKGEVP

**cluster 69** (1 units; gold: Restaurant food 1)
- `Restaurant food`: modern european

**cluster 78** (1 units; gold: Restaurant confirmed reference 1)
- `Restaurant confirmed reference`: HCY10A2Z

## value / window: raw agglo k=50 (K 50, F1 0.365)

**cluster 1** (109 units; gold: Train day 28, Train departure 26, Train destination 25)
- `Train departure`: 06:08. Need a ticket? User: Maybe. I need to leave [Cambridge] on Friday. Will that train work? System: I recommend TR1110.
- `Train destination`: User: Hello, I need to take a train to [Stansted airport] , arriving by 20:30. System: The TR7213 gets you there
- `Train day`: a ticket? User: Maybe. I need to leave Cambridge on [Friday] . Will that train work? System: I recommend TR1110. It
- `Train arrive by`: need to take a train to Stansted airport, arriving by [20:30] . System: The TR7213 gets you there at 06:08. Need
- `Train departure`: need a train that leaves at 20:45 from stevenage to [cambridge] System: What day would you like to travel by train?
- `Train destination`: User: I need a train that leaves at 20:45 from [stevenage] to cambridge System: What day would you like to travel
- `Train day`: travel by train? User: I would like to leave on [Wednesday] . System: There are 10 trains, TR9448 leaves at 5:54
- `Train leave at`: pound fee. User: I need a train that leaves at [20:45] from stevenage to cambridge System: What day would you like

**cluster 0** (71 units; gold: Hotel requested people 14, Hotel requested day 12, Hotel requested stay 10)
- `Hotel requested day`: you a room for seven people for three nights, starting [Monday] , at Finches Bed and Breakfast. Reference number is CUL9VZ04.
- `Hotel requested people`: for the Cocum restaurant, I would like to book for [7] people at 15:00 on monday if possible. System: I have
- `Hotel requested stay`: User: The same group of people and same day for [3] nights. System: I booked your restaurant table, and the reference
- `Restaurant name`: you like? User: Actually I am specifically looking for the [Cocum] restaurant, I would like to book for 7 people at
- `Restaurant requested day`: would like to book for 7 people at 15:00 on [monday] if possible. System: I have a table reserved for you
- `Restaurant requested people`: for the Cocum restaurant, I would like to book for [7] people at 15:00 on monday if possible. System: I have
- `Restaurant requested time`: restaurant, I would like to book for 7 people at [15:00] on monday if possible. System: I have a table reserved
- `Restaurant confirmed name`: you like? User: Actually I am specifically looking for the [Cocum] restaurant, I would like to book for 7 people at

**cluster 20** (35 units; gold: Hotel confirmed reference 11, Train requested people 9, Restaurant confirmed reference 8)
- `Train confirmed reference`: I ha e booked your ticket. Your confirmation number is [VBAEMG3Z] . Can I assist you with anything else? User: No,
- `Train requested people`: Just to confirm, how many seats will you need? User: [5] , please. Include the reference number. System: You will arrive
- `Train confirmed reference`: System: You will arrive at 10:54 the reference number is [69luuzq7] User: Thanks so much, that's all I need today. System:
- `Hotel confirmed reference`: I booked your restaurant table, and the reference number is [CUL9VZ04] . Is there anything else I can help you with?
- `Train requested people`: you like to book passage? User: Yes please. I need [1] ticket. System: Booking was successful Your reference number is TNU1H19G.
- `Train confirmed reference`: 1 ticket. System: Booking was successful Your reference number is [TNU1H19G] . Do you need assistance with anything else? User: Yes
- `Restaurant confirmed reference`: ahead and booked it for you. Your reference number is [HXSPEY9N] . What else can I do for you? User: I'll
- `Train requested people`: tickets you need. User: I need to book seats for [4] people please, and can I get the reference number for

**cluster 6** (34 units; gold: Restaurant area 14, Restaurant food 8, Restaurant price range 7)
- `Restaurant area`: User: I want to find an expensive restaurant in the [east] part of town. System: What is the food type you
- `Restaurant price range`: User: I want to find an [expensive] restaurant in the east part of town. System: What is
- `Restaurant area`: restaurant should serve african food and should be in the [centre] System: There is one African restuarant in the Center. It
- `Restaurant food`: looking for a place to dine. The restaurant should serve [african] food and should be in the centre System: There is
- `Restaurant area`: User: Hello, I am looking for a restaurant on the [south] side of town that serves international food. System: I'm sorry,
- `Restaurant food`: Would you like another type of food? User: How about [Chinese] food? System: There are the Peking Restaurant, which is expensive,
- `Restaurant area`: same area. System: I have 9 different restaurants in the [south] . Lets try to narrow it down. Do you have
- `Restaurant area`: Yes please. I need an expensive restaurant located in the [centre] . System: You have some great choices. Do you have

**cluster 8** (16 units; gold: Hotel type 4, Hotel name 3, Hotel confirmed name 3)
- `Hotel type`: number is BPE8LVHA. User: Thank you. I'd also like a [guesthouse] in the cheaper price range. Can you help me with
- `Hotel type`: that fits your current criteria. User: I actually need a [guesthouse] instead of a hotel, please. System: I have two guesthouses.
- `Restaurant area`: in the expensive price range and should be in the [south] , i do not have a particular food preference. System:
- `Hotel name`: located in the north. System: I would suggest this one [city centre north b and b] . User: Sure, I need a reservation for 4 people
- `Hotel price range`: User: I'm looking for a place to stay that is [cheap] located in the north. System: I would suggest this one
- `Hotel confirmed name`: located in the north. System: I would suggest this one [city centre north b and b] . User: Sure, I need a reservation for 4 people
- `Hotel name`: guesthouses in the north. May I suggest the 4 star [Acorn Guest house] ? User: Are there any expensive hotels in the north?
- `Hotel area`: would prefer? User: I'm looking for something expensive in the [north] . System: There are no expensive guesthouses in the north

**cluster 36** (16 units; gold: Hotel stars 4, Hotel area 2, Hotel name 2)
- `Hotel area`: help you with? User: I need a hotel in the [west] with free parking please. System: Do you care about the
- `Hotel name`: criteria? User: how about the north? System: How about the [Ashley Hotel] ? They have free internet and parking, though. User: Yes
- `Hotel area`: like to try a different criteria? User: how about the [north] ? System: How about the Ashley Hotel? They have free
- `Hotel parking`: Ashley Hotel? They have free internet and parking, though. User: [Yes] please tell me their postcode and star rating. System: The
- `Hotel internet`: Ashley Hotel? They have free internet and parking, though. User: [Yes] please tell me their postcode and star rating. System: The
- `Hotel internet`: star hotels, do you want to choose something else User: [Yes] , can you find a place for me with free
- `Hotel stars`: star option would you like ? User: How about a [4] star rating? System: I don't have a 4 star in
- `Hotel type`: else? User: I want to stay at a 3 star [hotel] with free parking. System: I'm sorry for the confusion. There

**cluster 3** (14 units; gold: Train confirmed reference 11, Train requested people 3)
- `Train confirmed reference`: payable at the station . Your reference number is : [P6G0S9IT] . Is there anything else I can help you with?
- `Train requested people`: you like reservations? User: Yes. I will need it for [eight] people. System: Booking was successful, the total fee is 64.64
- `Train confirmed reference`: 64.64 GBP payable at the station. Your reference number is: [LTQHUT3Y] . Can I assist with anything else today? User: Yeah,
- `Train requested people`: that for you? User: Yes, please. Can you book me [4] tickets? System: Booking was successful, the total fee is 40.4
- `Train confirmed reference`: 40.4 GBP payable at the station. Reference number is : [H4BIFD0U] . Will there be anything else today? User: I will
- `Train confirmed reference`: seat. System: Your booking was successful! The reference number is [698RE4W1] . The total fee of 17.89 is payable at the
- `Train confirmed reference`: System: I have booked your train. The reference number is [JI5O0VTT] . The fee is 7.84 GBP payable at the station.
- `Train confirmed reference`: GBP payable at the station . Reference number is : [MU3UYQCK] . User: I'm also looking to eat at a restaurant

**cluster 18** (13 units; gold: Restaurant area 4, Restaurant food 3, Restaurant price range 3)
- `Restaurant area`: There are two. Both are expensive. One is in the [north] and one is in the centre. Do you have a
- `Restaurant food`: User: I'm hoping to find a [french] restaurant in Cambridge. System: There are two. Both are expensive.
- `Restaurant name`: an expensive restaurant in the centre of town. System: The [cambridge chop house] serves british food, it is in the centre of town
- `Restaurant area`: User: I want to find an expensive restaurant in the [centre] of town. System: The cambridge chop house serves british food,
- `Restaurant price range`: User: I want to find an [expensive] restaurant in the centre of town. System: The cambridge chop
- `Train destination`: User: I am traveling to [Cambridge] and would like to find a local restaurant. I want
- `Restaurant area`: User: I want to find a Chinese restaurant in the [centre] of Cambridge. System: There are 10 choices and we have
- `Restaurant food`: User: I want to find a [Chinese] restaurant in the centre of Cambridge. System: There are 10

**cluster 2** (12 units; gold: Attraction area 6, Attraction type 4, Restaurant area 1)
- `Attraction type`: User: I am looking for a [college] attraction to go to in town. System: There are several
- `Attraction area`: Yes. I am looking for places to go in the [centre] area. I am looking for college. System: There are 13
- `Attraction type`: to go in the centre area. I am looking for [college] . System: There are 13 choices, how do you feel
- `Attraction area`: Actually, I want to visit a college. Somewhere in the [centre] . System: I would suggest downing college, would you like
- `Attraction type`: be interested in? User: Actually, I want to visit a [college] . Somewhere in the centre. System: I would suggest downing
- `Restaurant area`: Actually, I want to visit a college. Somewhere in the [centre] . System: I would suggest downing college, would you like
- `Attraction area`: attraction near the hotel? System: There are many in the [centre] of town,what type are you looking for a church,or swimming
- `Attraction area`: User: I am looking for places in the [centre] to go to. System: There are 44 great attractions to

**cluster 40** (9 units; gold: Hotel price range 3, Hotel name 1, Hotel confirmed name 1)
- `Hotel name`: User: As long as it has free wifi System: The [finches Bed and Breakfast] fits your needs. When would you like to stay? User:
- `Hotel confirmed name`: User: As long as it has free wifi System: The [finches Bed and Breakfast] fits your needs. When would you like to stay? User:
- `Hotel price range`: place to stay. It must include free wifi. But I'm [cheap] as all get out, so nothing too pricey. System: I
- `Hotel stars`: information were you looking for? User: I would like a [4] star luxury place to stay. It must include free wifi.
- `Hotel requested stay`: information were you looking for? User: I would like a [4] star luxury place to stay. It must include free wifi.
- `Hotel price range`: find a place for me with free wifi in the [moderate] price range? System: What other star option would you like
- `Hotel requested people`: In fact, there are 11. If you'd like an inexpensive, [4] star guesthouse with free internet and free parking, Worth House
- `Hotel type`: the moment. However, I would also like to find a [hotel] to stay with free wifi and a moderate price range.

**cluster 19** (9 units; gold: Restaurant requested day 3, Restaurant requested people 3, Restaurant requested time 2)
- `Restaurant requested day`: they would have a table for 7 at 17:45 on [Sunday] ? System: Yes, they had a table available and I
- `Restaurant requested people`: Can you check if they would have a table for [7] at 17:45 on Sunday? System: Yes, they had a table
- `Restaurant requested time`: check if they would have a table for 7 at [17:45] on Sunday? System: Yes, they had a table available and
- `Restaurant requested day`: How about the North? Can I get a table there [Thursday] at 16:30 for 7? System: I'm sorry, Restaurant Two Two
- `Restaurant requested people`: Can I get a table there Thursday at 16:30 for [7] ? System: I'm sorry, Restaurant Two Two doesn't have availability
- `Restaurant confirmed name`: table there Thursday at 16:30 for 7? System: I'm sorry, [Restaurant Two Two] doesn't have availability then. Would you like to try a
- `Restaurant requested day`: those expensive? If so, book me a table there for [Thursday] for 8 people at 13:30 please. System: There's actually two
- `Restaurant requested people`: If so, book me a table there for Thursday for [8] people at 13:30 please. System: There's actually two expensive places,

**cluster 14** (9 units; gold: Hotel area 2, Hotel stars 2, Hotel name 1)
- `Hotel name`: rating and be located on the west side. System: The [Cambridge Belfry] fits your requirements, would you like to book a reservation
- `Hotel area`: have a four star rating and be located on the [west] side. System: The Cambridge Belfry fits your requirements, would you
- `Hotel confirmed name`: star rating and be located on the west side. System: [The Cambridge Belfry] fits your requirements, would you like to book a reservation
- `Hotel area`: User: Hello. I'm hoping to find a guesthouse in the [north] part of Cambridge. Are there any? System: Indeed there are.
- `Attraction area`: User: I am looking for places to on the [south] side of town. System: Alright. What type of places? Cambridge
- `Hotel stars`: User: I'm curious about the [3] -star lodging options available in Cambridge. System: There are no
- `Hotel type`: need a 3 star hotel in Cambridge, that offers a [guesthouse] , can you book it for me ? System: Yes,
- `Hotel stars`: User: I need a [3] star hotel in Cambridge, that offers a guesthouse, can you

**cluster 11** (9 units; gold: Hotel confirmed name 4, Hotel name 3, Hotel confirmed reference 1)
- `Hotel name`: Thank you. System: All right, sir, that would be the [Gonville Hotel] on Gonville Place. User: Ok, could you book it for
- `Hotel confirmed name`: Thank you. System: All right, sir, that would be the [Gonville Hotel] on Gonville Place. User: Ok, could you book it for
- `Hotel confirmed name`: System: Sure. I was able to book you for the [Huntingdon Marriott Hotel] . Reference #IHGCTXH9. Anything else I can help with? User:
- `Hotel confirmed reference`: to book you for the Huntingdon Marriott Hotel. Reference # [IHGCTXH9] . Anything else I can help with? User: Whew, thanks,
- `Hotel name`: star hotel. System: There is one option available. It is [cityroomz] . Do you want to book? User: Yes, please book
- `Hotel internet`: available. It is cityroomz. Do you want to book? User: [Yes] , please book it for the same day for a
- `Hotel confirmed name`: star hotel. System: There is one option available. It is [cityroomz] . Do you want to book? User: Yes, please book
- `Hotel name`: guesthouse, can you book it for me ? System: Yes, [hamilton lodge] is located on 156 chesterton road. User: If this guesthouse

**cluster 17** (8 units; gold: Taxi leave at 2, Taxi departure 1, Taxi destination 1)
- `Taxi departure`: Okay! What is your departure site? User: I'm coming from [city stop restaurant] . System: Okay, I've got you a black bmw with
- `Taxi destination`: come pick me up by 10:30 to take me to [Midsummer House Restaurant] . System: Okay! What is your departure site? User: I'm
- `Taxi leave at`: to book a taxi to come pick me up by [10:30] to take me to Midsummer House Restaurant. System: Okay! What
- `Taxi arrive by`: like to arrive? User: I would like to arrive by [17:15] . System: I have a white tesla booked. The contact
- `Hotel parking`: TR1719 will have you at your destination around 10:09. User: [Yes] , that sounds perfect. I'll need 4 seats. System: Your
- `Train requested people`: to book you seats? User: Great can you get me [7] tickets for that? System: TR7610 we have booked your train
- `Train arrive by`: a local restaurant. I want to arrive by train at [noon] . System: Hi there, let's start with the train arrival,
- `Taxi leave at`: to travel? User: I want to leave the restaurant by [09:15] . Please get me the contact number and car type.

**cluster 7** (8 units; gold: Attraction area 3, Attraction type 3, Attraction name 2)
- `Attraction name`: a cinema to go to in the south. System: The [cineworld cinema] is the place! User: Can you tell me the address?
- `Attraction area`: User: I need a cinema to go to in the [south] . System: The cineworld cinema is the place! User: Can
- `Attraction type`: User: I need a [cinema] to go to in the south. System: The cineworld cinema
- `Attraction name`: do in the west. Can you recommend anything? System: The [Whale of a Time] entertainment venue is a fun choice. We also have museums
- `Attraction area`: else? User: I'm looking for things to do in the [west] . Can you recommend anything? System: The Whale of a
- `Attraction area`: town to search in? User: Please recommend something in the [South] . System: How about a cinema or museum? There's also
- `Attraction type`: city you were looking at? User: I'm looking for a [theatre] in any part of the city. Can you recommend one?
- `Attraction type`: there a certain type you were looking for? Perhaps a [museum] or theatre? User: A museum sounds nice. Do you have

**cluster 9** (7 units; gold: Restaurant confirmed name 2, Restaurant food 1, Taxi departure 1)
- `Restaurant food`: need a place to eat in that area. I want [Italian] food. System: I would suggest pizza express. User: Can you
- `Restaurant confirmed name`: that area. I want Italian food. System: I would suggest [pizza express] . User: Can you check if they would have a
- `Taxi departure`: you? User: I'll need a taxi to get me from [downing college] to pizza express by 17:45. can you set that up
- `Taxi destination`: need a taxi to get me from downing college to [pizza express] by 17:45. can you set that up for me? System:
- `Taxi arrive by`: to get me from downing college to pizza express by [17:45] . can you set that up for me? System: I
- `Restaurant name`: What are my choices? System: How about cafe uno or [don pasquale pizzeria] ? User: I love pizza that will work can I
- `Restaurant confirmed name`: What are my choices? System: How about cafe uno or [don pasquale pizzeria] ? User: I love pizza that will work can I

**cluster 5** (6 units; gold: Restaurant price range 2, Hotel price range 1, Hotel internet 1)
- `Hotel price range`: the in the moderate price range? System: no it is [cheap] . will that do for you? User: Can you book
- `Hotel internet`: fits your needs. When would you like to stay? User: [Yes] that's find are the in the moderate price range? System:
- `Restaurant price range`: Turkish restaurants in the centre. Would you prefer expensive or [moderate] price range? User: Moderate price range would be fine. Could
- `Restaurant name`: the same price range as the hotel. System: I found [Thanh Binh] ; would you like me to make you a reservation?
- `Restaurant confirmed name`: the same price range as the hotel. System: I found [Thanh Binh] ; would you like me to make you a reservation?
- `Restaurant price range`: the Northern part of town and it is in the [moderate] price range User: Great can you book that for 1

**cluster 12** (5 units; gold: Restaurant confirmed name 1, Restaurant confirmed reference 1, Taxi departure 1)
- `Restaurant confirmed name`: same day as before? System: I was able to book [restaurant alimentum] reference number is HCY10A2Z User: thank you for booking that
- `Restaurant confirmed reference`: I was able to book restaurant alimentum reference number is [HCY10A2Z] User: thank you for booking that and the reference number
- `Taxi departure`: Ok, a grey honda will pick you up at the [hamilton lodge] in time to arrive at restaurant alimentum for your 10:00
- `Taxi destination`: up at the hamilton lodge in time to arrive at [restaurant alimentum] for your 10:00 reservations. Taxi contact number is 07242149665. Anything
- `Taxi arrive by`: lodge in time to arrive at restaurant alimentum for your [10:00] reservations. Taxi contact number is 07242149665. Anything else? User: That

**cluster 48** (4 units; gold: Hotel name 2, Hotel requested day 1, Hotel confirmed name 1)
- `Hotel name`: you like to begin your stay? User: from Thursday. System: [alexander bed and breakfast] would be perfect for you. Shall i book it ?
- `Hotel requested day`: day would you like to begin your stay? User: from [Thursday] . System: alexander bed and breakfast would be perfect for
- `Hotel name`: stars and free parking. System: Alright, might I suggest the [Alexander Bed and Breakfast] then? User: That sounds great - I want to book
- `Hotel confirmed name`: stars and free parking. System: Alright, might I suggest the [Alexander Bed and Breakfast] then? User: That sounds great - I want to book

**cluster 13** (4 units; gold: Restaurant name 2, Restaurant confirmed name 1, Restaurant food 1)
- `Restaurant name`: 5 results for restaurants serving indian food, the first is [tandoori palace] located at 68 Histon Road Chesterton. Would you like a
- `Restaurant confirmed name`: 5 results for restaurants serving indian food, the first is [tandoori palace] located at 68 Histon Road Chesterton. Would you like a
- `Restaurant name`: Yes. I would like to eat Indian food. System: The [tandoori palace] meets your criteria. It is located at 68 Histon Road
- `Restaurant food`: have another preference? User: Yes. I would like to eat [Indian] food. System: The tandoori palace meets your criteria. It is

**cluster 41** (3 units; gold: Attraction name 1, Attraction area 1, Attraction type 1)
- `Attraction name`: the east side of town? System: Yes there is the [abbey pool and astroturf pitch] would you like their address? User: Yes. May I have
- `Attraction area`: you? User: No. Are there any swimming pools on the [east] side of town? System: Yes there is the abbey pool
- `Attraction type`: to book it for you? User: No. Are there any [swimming pools] on the east side of town? System: Yes there is

**cluster 38** (3 units; gold: Restaurant confirmed reference 3)
- `Restaurant confirmed reference`: minutes starting at 15:15 on Sunday. Your reference number is [TIYE4F1Y] . Can I help you with anything else? User: I'm
- `Restaurant confirmed reference`: will be reserved for 15 minutes. Reference number is : [OAEJMYOI] . User: I am also looking for an attraction to
- `Restaurant confirmed reference`: will be reserved for 15 minutes. Reference number is : [DDLKGEVP] . User: can you suggest any attractions in the same

**cluster 4** (3 units; gold: Restaurant food 2, Restaurant price range 1)
- `Restaurant food`: don't have anything that meets those requirements. User: How about [British] food? System: Yes I have three. When would you like
- `Restaurant price range`: like a restaurant that serves eritrean food and in the [expensive] price range. System: Would you like European food? User: No.
- `Restaurant food`: you would like to consider? User: Yes, are there any [modern european] restaurants in that area? System: There are no modern European

**cluster 15** (3 units; gold: Attraction name 2, Taxi destination 1)
- `Attraction name`: the city. Can you recommend one? System: There is the [Mumford theatre] , it is located at Anglia Ruskin Enterprise, East Road
- `Attraction name`: do. And can you get me the address? System: The [Cambridge Arts Theatre] is a popular attraction in the city centre. Does that
- `Taxi destination`: do. And can you get me the address? System: The [Cambridge Arts Theatre] is a popular attraction in the city centre. Does that

**cluster 23** (2 units; gold: Restaurant name 1, Restaurant area 1)
- `Restaurant name`: Margherita? They serve Italian. User: Is there anything else? System: [Thanh binh] is located in the west part of town and is
- `Restaurant area`: hotel this restaurant is. System: It is also in the [west] side area, located at 17 Magdalene Street City Centre. Would

**cluster 21** (2 units; gold: Hotel name 1, Hotel confirmed name 1)
- `Hotel name`: help me find a hotel called the university aims no [university arms hotel] . System: I have a hotel called university arms hotel
- `Hotel confirmed name`: help me find a hotel called the university aims no [university arms hotel] . System: I have a hotel called university arms hotel

**cluster 35** (2 units; gold: Restaurant name 1, Restaurant confirmed name 1)
- `Restaurant name`: 13:30 please. System: There's actually two expensive places, graffiti and [travellers rest] . Which would you prefer? User: Travellers Rest sounds good.
- `Restaurant confirmed name`: 13:30 please. System: There's actually two expensive places, graffiti and [travellers rest] . Which would you prefer? User: Travellers Rest sounds good.

**cluster 32** (2 units; gold: Restaurant name 1, Restaurant confirmed name 1)
- `Restaurant name`: the ugly duckling is in the expensive price range. The [copper kettle] serves british food and is moderately priced. Would you like
- `Restaurant confirmed name`: sorry the ugly duckling is in the expensive price range. [The copper kettle] serves british food and is moderately priced. Would you like

**cluster 22** (2 units; gold: Hotel type 1, Hotel requested day 1)
- `Hotel type`: cb11pt User: I would also like to book at a [guest house] named Aylesbray Lodge, starting Monday. System: I'm starting to book
- `Hotel requested day`: to book at a guest house named Aylesbray Lodge, starting [Monday] . System: I'm starting to book your reservation at Aylesbray

**cluster 46** (2 units; gold: Restaurant name 1, Restaurant confirmed name 1)
- `Restaurant name`: suggestion of a moderately priced Chinese place. System: I recommend [Jinling Noodle Bar] . It's located at 11 Peas Hill City Center. Would
- `Restaurant confirmed name`: suggestion of a moderately priced Chinese place. System: I recommend [Jinling Noodle Bar] . It's located at 11 Peas Hill City Center. Would

**cluster 10** (2 units; gold: Hotel name 1, Train destination 1)
- `Hotel name`: I'm looking for any information that you have on the [Lensfield hotel] in Cambridge. System: The Lensfield Hotel is an expensive, 3-star
- `Train destination`: any information that you have on the Lensfield hotel in [Cambridge] . System: The Lensfield Hotel is an expensive, 3-star hotel

**cluster 24** (2 units; gold: Hotel internet 1, Restaurant requested time 1)
- `Hotel internet`: different arrival day? User: Will you try Sunday arrival? System: [Yes] , I tried Sunday but it isn't available. Can you
- `Restaurant requested time`: you like to try a different time? User: How about [10:00] on the same day as before? System: I was able

**cluster 31** (1 units; gold: Restaurant name 1)
- `Restaurant name`: number, and postcode of the venue please. System: How about [Sitar Tandoori] , It's address is 43 High Street Cherry Hinton Cherry

**cluster 33** (1 units; gold: Train requested people 1)
- `Train requested people`: John's has a 2.50 pound fee, and Trinity has a [1] pound fee. User: I need a train that leaves at

**cluster 37** (1 units; gold: Attraction name 1)
- `Attraction name`: User: I'm looking for information on [Broughton house gallery] . System: Certainly! It's a museum in the centre at

**cluster 47** (1 units; gold: Restaurant name 1)
- `Restaurant name`: Good Luck Chinese Food Takeaway, which is also expensive, and [the Lucky Star] , which is cheap. User: Can I have the address

**cluster 29** (1 units; gold: Restaurant food 1)
- `Restaurant food`: Pizza Hut way to much. Can you try something with [indian] food? It is a special occasion so it can be

**cluster 42** (1 units; gold: Restaurant price range 1)
- `Restaurant price range`: food? It is a special occasion so it can be [expensive] . System: There is Taj Tandoori which is located on

**cluster 43** (1 units; gold: Taxi destination 1)
- `Taxi destination`: taxi should depart from la Margarita and should go to [riverboat Georgina] . System: What time would you like to arrive? User:

**cluster 45** (1 units; gold: Hotel type 1)
- `Hotel type`: User: Thank you very much! Also, can you recommend a [hotel] in the South part of town? I don't need internet

**cluster 30** (1 units; gold: Restaurant name 1)
- `Restaurant name`: User: Do you have information on [La Raza] ? System: La raza is a spanish restaurant in the

**cluster 26** (1 units; gold: Attraction name 1)
- `Attraction name`: User: I am looking for information about the the [Cherry Hinton Water Play] System: That is a free park on the east side

**cluster 39** (1 units; gold: Hotel area 1)
- `Hotel area`: hotels with 3 stars and parking. Do you prefer the [centre] or the south? User: The centre will be fine. Thank

**cluster 49** (1 units; gold: Hotel requested stay 1)
- `Hotel requested stay`: I couldn't find anything with 5 stars. User: try out [1] night then System: I do not have 4 or 5

**cluster 34** (1 units; gold: Hotel confirmed reference 1)
- `Hotel confirmed reference`: party booked at the Alexander. The reference number is : [G2YMGI0L] . Is there anything else I can do for you

**cluster 28** (1 units; gold: Taxi departure 1)
- `Taxi departure`: type of food and give me the restaurant's address. System: [The oak bistro] is an excellent choice for british food. The address is

**cluster 27** (1 units; gold: Restaurant name 1)
- `Restaurant name`: me the address of the moderately priced one. System: The [Nirala] is located at 7 Milton Street Chesterton. User: What is

**cluster 25** (1 units; gold: Hotel requested stay 1)
- `Hotel requested stay`: how many people will be staying? User: I'm staying for [2] days and it's just myself. What train can I take

**cluster 16** (1 units; gold: Train requested people 1)
- `Train requested people`: need to find a train that leaves at 19:30 for [5] people System: Unfortunately there are no trains that leave at

**cluster 44** (1 units; gold: Restaurant area 1)
- `Restaurant area`: day as before. System: Neither of the restaurants in the [centre] are available at that time. Would you like to try

