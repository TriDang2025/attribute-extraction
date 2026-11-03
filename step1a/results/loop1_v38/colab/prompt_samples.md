# wf_v3.8 prompt samples (verbatim)

## dupcheck_dev50_split_train

```text
Below is a list of columns proposed for one table. Each column has an id, a name, a description and example values.
Some columns are the same attribute listed twice (the same kind of value, with the same role, under two names or in two parts).
Find them: list every group of two or more columns that are the same attribute with the same role. Do not join columns that
are different attributes, and do not join columns whose values play different roles (for example where something starts
and where it ends). Leave a column out when it has no twin.

Columns (20):
1. name: arrival location | description: the location where the train arrives | examples: stansted airport; leicester; broxbourne
2. name: arrival time | examples: 19:30; 18:15; 18:24
3. name: day query | examples: what day
4. name: departure location | description: the location from which the train departs | examples: ely; norwich; peterborough
5. name: departure time | description: the time at which the train departs | examples: 12:00; 13:15; 15:45
6. name: destination city | examples: cambridge
7. name: local information center | examples: cambridge towninfo centre
8. name: number of people | examples: 1 child; 2 adult; 3 people
9. name: number of tickets | description: the number of tickets booked | examples: how many ticket; 16; 10
10. name: number of trains | examples: 1 train; 12; 19 train
11. name: origin city | examples: cambridge; cambidge
12. name: price per ticket | description: the cost of a single train ticket | examples: 10.10 pound; 12.80 pound; 14.08 pound
13. name: reference number | description: the reference number for the booking | examples: 1r61po9r; 64uq7m3g; 698re4w1
14. name: stay duration days | examples: 2 day
15. name: time query | examples: what time
16. name: total fee | examples: 66 gbp; 10.56 gbp; 40.4 gbp
17. name: train id | description: the unique identifier for the train | examples: tr9016; tr5713; tr5921
18. name: travel date | description: the date of the train journey | examples: saturday; friday; wednesday
19. name: travel time | description: the duration of the train journey | examples: 28-minute
20. name: travel time minutes | examples: 105 minute; 49 minute; 38 minute

Return ONLY one JSON object, nothing before or after it, in this shape (other ids): {"joins": [{"columns": [3, 7], "reason": "same value, same role"}]}. Use [] when nothing is joined.
```

## example_dev50_train_c01

```text
Below are examples taken from conversations. In each example one value is marked with [[ ]].
For each example, answer whether the marked value fits the attribute named at the end of this text.
Answer "yes" or "no" for every example.

Examples:
- 1 [user] previous turn, system: And where will you be heading to? | turn: I am going to [[Stansted Airport]].
- 2 [user] previous turn, system: Okay, what day would you like to travel and where will you be leaving from? | turn: I'll be leaving [[Leicester]] and I want to be in Cambridge by 11:30, please.
- 3 [user] previous turn, system: Your table was booked. Your reference number is 42XEDGDF. Is there anything else I can help you with? | turn: I also need a Friday train to [[Broxbourne]].
- 4 [user] previous turn, system: Sheep's Green and Lammas Land Park Fen Causeway is located at Fen Causeway, Newnham road, postal code cb322ad. | turn: Thanks! I'm also looking for a train from Cambridge to [[Kings Lynn]].
- 5 [user] previous turn, system: The earliest leaves at 13:40 and the trains depart every hour through 23:40. If you'd like to choose one I can book it for you. | turn: That would be great. How much would it cost to travel to [[stansted]] from Cambridge?
- 6 [user] previous turn, system: My personal favorite is the Museum of Archaeology and Anthropology at University of Cambridge, Downing Street. It even has free admission! | turn: I'll check that out. Can you also find me a train for Monday I'm leaving [[leicester]]?
- 7 [user] previous turn, system: OK, what are your departure and arrival stations, and what time do you want to travel? | turn: I'd like to go to Cambridge via [[Broxbourne]]. I'd like to leave on Thursday and arrive no later than 12:00.
- 8 [user] previous turn, system: Booking was successful. Reference number is : FC2BDIC9. | turn: I also need a train on Wednesday, leaving from [[Kings Lynn]].
- 9 [user] turn: Hello, I need to take a train to [[Stansted airport]], arriving by 20:30.
- 10 [system] previous turn, user: I need to go from leicester to cambridge. | turn: It looks like train TR6210 will be leaving [[Leicester]] at 11:09 on Saturday and will arrive to Cambridge at 12:54. Can I help you with anything else?

Question for each example: Does the marked value fit the attribute arrival location (the location where the train arrives)?

Return ONLY one JSON object, nothing before or after it, one answer per example: {"answers": [{"id": 1, "fits": "yes"}, {"id": 2, "fits": "no"}]}
```
