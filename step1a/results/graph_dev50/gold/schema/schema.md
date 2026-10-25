## attraction
- identifier: attraction#0 (college, museum, whale of a time)
- #attraction#1 [column]: centre, south, east
- #attraction#2 [column]: ballare, cambridge art theatre, cherry hinton water play
- keep apart: attraction#0 / attraction#2 (cos 0.96, co 4)

## hotel
- identifier: hotel#5 (monday, wednesday, friday)
- #hotel#0 [column]: guesthouse, hotel, university arm hotel
- #hotel#1 [column]: alexander bed and breakfast, ashley hotel, acorn guest house
- #hotel#2 [column]: moderate, cheap, expensive
- #hotel#3 [column]: 2, 3
- #hotel#4 [column]: cul9vz04, e6uvd9ol, 72ycmlxx
- #hotel#6 [column]: north, west, avalon
- #hotel#7 [column]: 5, 3, 2
- #hotel#8 [column]: 4, 3
- keep apart: hotel#0 / hotel#1 (cos 0.97, co 7)
- keep apart: hotel#3 / hotel#7 (cos 0.97, co 6)
- sub-entity: hotel#2, hotel#6, hotel#7, hotel#8

## restaurant
- identifier: restaurant#4 (15:15, 11:15, 15:00)
- #restaurant#0 [column]: expensive, moderate, cheap
- #restaurant#1 [column]: centre, west, north
- #restaurant#2 [column]: nirala, graffiti, tandoori palace
- #restaurant#3 [column]: 5, 7, 4
- #restaurant#5 [column]: thursday, wednesday, sunday
- #restaurant#6 [column]: 42xedgdf, 64uq7m3g, bpe8lvha
- #restaurant#7 [column]: indian, chinese, turkish
- keep apart: restaurant#1 / restaurant#2 (cos 0.96, co 13)
- keep apart: restaurant#2 / restaurant#7 (cos 0.96, co 13)
- sub-entity: restaurant#0, restaurant#1, restaurant#7

## taxi
- identifier: taxi#0 (09:15, 10:00, 10:30)
- #taxi#1 [column]: midsummer house restaurant, pizza express, restaurant alimentum
- #taxi#2 [column]: downing college, city stop restaurant, hamilton lodge

## train
- identifier: train#1 (19:30, 12:00, 13:15)
- #train#0 [column]: stansted airport, leicester, ely
- #train#2 [column]: cambridge
- #train#3 [column]: saturday, tuesday, wednesday
- #train#4 [column]: 4, 5, 1
- #train#5 [column]: h4bifd0u, 1r61po9r, 698re4w1
- sub-entity: train#4, train#5

