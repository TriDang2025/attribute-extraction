## attraction
- identifier: attraction#0 (college, centre, park)
- #attraction#1 [column]: east, west, north
- #attraction#2 [column]: ballare, camboat, milton country park
- keep apart: attraction#0 / attraction#2 (cos 0.97, co 4)

## hotel
- identifier: hotel#4 (0pp63274, 1cd4lz9r, 4r3bmwnk)
- #hotel#0 [column]: guesthouse, hotel, guest house
- #hotel#1 [column]: acorn guest house, finch bed and breakfast, warkworth house
- #hotel#2 [column]: tuesday, thursday, sunday
- #hotel#3 [column]: 4
- #hotel#7 [column]: cheap, moderate, expensive
- #hotel#8 [column]: north, west, east
- #hotel#9 [column]: allenbell, autumn house
- keep apart: hotel#0 / hotel#1 (cos 0.97, co 11)
- sub-entity: hotel#1, hotel#7, hotel#8, hotel#9

## restaurant
- identifier: restaurant#7 (0xfpi4ib, 1crco6ht, 3hzr0o30)
- #restaurant#0 [column]: european, chinese, indian
- #restaurant#1 [column]: centre, east, north
- #restaurant#2 [column]: expensive, moderate, cheap
- #restaurant#3 [column]: 2, 6, 5
- #restaurant#4 [column]: la tasca, j restaurant, pizza express
- #restaurant#5 [column]: monday, tuesday, thursday
- #restaurant#6 [column]: 12:00, 14:00, 14:45
- keep apart: restaurant#0 / restaurant#4 (cos 0.96, co 14)
- keep apart: restaurant#1 / restaurant#4 (cos 0.97, co 14)
- sub-entity: restaurant#0, restaurant#1, restaurant#2

## taxi
- identifier: taxi#1 (cherry hinton village centre, holy trinity church, rosa's bed and breakfast)
- #taxi#0 [column]: 08:00, 08:15, 11:45
- #taxi#2 [column]: ashley hotel

## train
- identifier: train#5 (0lyl0j3v, 1ejqjws2, 2i340ejn)
- #train#0 [column]: cambridge
- #train#1 [column]: birmingham new street, london king cross, bishop stortford
- #train#2 [column]: 15:30, 08:00, 18:45
- #train#3 [column]: monday, sunday, thursday
- #train#4 [column]: 1, 4, 8
- sub-entity: train#2, train#3

## relationships
| entities | node pairs | max npmi |
|---|---|---|
| attraction - restaurant | 5 | 0.26 |
