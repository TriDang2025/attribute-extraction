# GLiNER label set examples (threshold 0.5)

## generic

### Values recovered (missed by generic 0.5)

(baseline)

### Spans that matched nothing

- PMUL1270: "TR7213" label number score 0.63
- MUL0589: "TR9016" label number score 0.52
- PMUL0468: "I" label name score 0.69
- PMUL0767: "cb12as" label place score 0.80
- PMUL4578: "reference number" label number score 0.77
- MUL2478: "today" label day score 0.82
- PMUL0388: "I" label name score 0.70
- PMUL3589: "Bishops Stafford" label place score 0.95
- SNG01551: "5 stars" label number score 0.52
- PMUL0890: "city centre" label place score 0.94
- PMUL4197: "I" label name score 0.72
- MUL0470: "12:15" label time score 0.84
- PMUL0598: "cheap" label price score 0.83
- SNG0840: "fewer nights" label duration score 0.55
- PMUL4647: "table" label place score 0.61
(633 of 1124 spans)

## hand

### Values recovered (missed by generic 0.5)

- MUL0117: "expensive" (Restaurant price range) <- span "expensive restaurant" label cuisine
- MUL0204: "5" (Restaurant requested people) <- span "5" label number
- MUL0233: "indian" (Restaurant food) <- span "indian food" label cuisine
- MUL0620: "4" (Hotel stars) <- span "4 star hotel" label hotel type
- MUL1335: "modern european" (Restaurant food) <- span "modern european restaurants" label cuisine
- MUL2164: "2" (Hotel requested stay) <- span "2 nights" label duration
- MUL2408: "indian" (Restaurant food) <- span "indian food" label cuisine
- MUL2478: "french" (Restaurant food) <- span "french restaurant" label cuisine
- PMUL0767: "expensive" (Restaurant price range) <- span "expensive restaurant" label cuisine
- PMUL0797: "indian" (Restaurant food) <- span "indian type food" label cuisine
- PMUL0890: "british" (Restaurant food) <- span "British food" label cuisine
- PMUL0890: "west" (Restaurant area) <- span "west" label area
- PMUL1780: "0" (Hotel stars) <- span "0 star hotel" label hotel type
- PMUL2050: "italian" (Restaurant food) <- span "Italian food" label cuisine
- PMUL2628: "2" (Hotel requested people) <- span "2 people" label number
(25 recovered in total)

### Spans that matched nothing

- PMUL1270: "The TR7213" label departure station score 0.91
- MUL0589: "TR9448" label departure station score 0.89
- MUL0404: "stansted" label departure station score 0.54
- MUL2408: "Italian" label cuisine score 0.86
- WOZ20631: "different type of cuisine" label cuisine score 0.62
- MUL2478: "expensive" label price score 0.58
- MUL1603: "12:54" label arrival time score 0.85
- PMUL3589: "21:29" label departure time score 0.62
- MUL0585: "19:58" label arrival time score 0.83
- MUL1440: "TR1755" label departure station score 0.78
- PMUL2628: "Aylesbray Lodge" label name score 0.90
- MUL0233: "area" label area score 0.54
- MUL0117: "four people" label number of guests score 0.80
- MUL0656: "01223355017" label number score 0.81
- PMUL0797: "The TR0017 train" label departure station score 0.74
(461 of 913 spans)

## gold

### Values recovered (missed by generic 0.5)

- MUL0117: "expensive" (Restaurant price range) <- span "expensive restaurant" label food
- MUL0233: "indian" (Restaurant food) <- span "indian food" label food
- MUL1335: "modern european" (Restaurant food) <- span "modern european restaurants" label food
- MUL2164: "2" (Hotel requested stay) <- span "2 nights" label duration
- MUL2408: "indian" (Restaurant food) <- span "indian food" label food
- MUL2478: "french" (Restaurant food) <- span "french restaurant" label food
- PMUL0767: "expensive" (Restaurant price range) <- span "expensive restaurant" label food
- PMUL0890: "british" (Restaurant food) <- span "British food" label food
- PMUL0890: "west" (Restaurant area) <- span "west" label area
- PMUL2050: "italian" (Restaurant food) <- span "Italian food" label food
- PMUL4504: "moderate" (Hotel price range) <- span "moderate price range" label price range
- PMUL4578: "4" (Train requested people) <- span "4 people" label requested people
- PMUL4722: "5" (Restaurant requested people) <- span "5 people" label requested people
- SNG01922: "african" (Restaurant food) <- span "african food" label food
- WOZ20405: "expensive" (Restaurant price range) <- span "expensive restaurant" label food
(17 recovered in total)

### Spans that matched nothing

- PMUL1270: "06:08" label time score 0.69
- MUL0589: "49 minutes" label duration score 0.72
- PMUL0468: "I" label confirmed name score 0.51
- MUL2408: "01223412299" label number score 0.89
- WOZ20631: "La Margherita" label destination score 0.62
- MUL2478: "Both" label number score 0.63
- MUL1603: "01223464550" label number score 0.77
- PMUL3589: "free parking" label parking score 0.98
- SNG01551: "free parking" label parking score 0.93
- PMUL0890: "European food" label food score 0.66
- PMUL4197: "Downing Street" label place score 0.68
- MUL2332: "type of food" label food score 0.61
- WOZ20584: "moderately price" label price score 0.58
- MUL0656: "how many people will be staying" label requested stay score 0.54
- PMUL0797: "Any type of food" label food score 0.72
(505 of 873 spans)

