# Span comparison examples

## Largest clusters made only of non-gold spans

### GLiNER 0.3

1. size 25: "tr9016" x4, "tr8167" x3, "tr6387" x2, "tr7610" x2, "tr5713" x2, "tr7213" x1, "tr1110" x1, "tr6193" x1
2. size 20: "01223367660" x2, "01223 249955" x1, "01223314960" x1, "07083984796" x1, "01223 244277" x1, "01223412299" x1, "01223311911" x1, "07633256482" x1
3. size 10: "station" x8, "local restaurant" x1, "restaurant" x1
4. size 8: "tr9448" x2, "train tr5921" x2, "tr2912" x1, "tr6838" x1, "tr7935" x1, "tr5921" x1
5. size 8: "cb11ln" x2, "cb17aa" x1, "cb12as" x1, "cb21dq" x1, "cb21sj" x1, "cb11pt" x1, "cb23pj" x1
6. size 8: "hotel" x3, "nightclub" x1, "theatre" x1, "church" x1, "museum" x1, "nightclubs" x1
7. size 7: "49 minutes" x2, "105 minutes" x2, "28-minute" x1, "105 minute" x1, "38 minute" x1
8. size 7: "reference number" x6, "confirmation number" x1
9. size 7: "same day" x3, "what day" x2, "day" x1, "today" x1
10. size 7: "total fee" x7

### GLiNER 0.5

1. size 20: "01223367660" x2, "01223 249955" x1, "01223314960" x1, "07083984796" x1, "01223 244277" x1, "01223412299" x1, "01223311911" x1, "07633256482" x1
2. size 12: "tr9016" x4, "train tr5921" x2, "tr7213" x1, "tr1110" x1, "tr7610" x1, "tr7935" x1, "tr5713" x1, "tr5921" x1
3. size 12: "10.10 pounds" x3, "66 gbp" x2, "12.80 pounds" x1, "8.08 pounds" x1, "8.08gbp" x1, "7.84 gbp" x1, "14.08 pounds" x1, "10.56 gbp" x1
4. size 6: "49 minutes" x2, "105 minutes" x2, "28-minute" x1, "38 minute" x1
5. size 6: "tr6387" x2, "tr6193" x1, "tr4669" x1, "tr3677" x1, "tr4679" x1
6. size 5: "reference number" x5
7. size 5: "same day" x3, "what day" x2
8. size 4: "cb11ln" x2, "cb17aa" x1, "cb12as" x1
9. size 4: "station" x3, "restaurant" x1
10. size 3: "15 minutes" x2, "5 pounds" x1

### spaCy

1. size 92: "address" x26, "postcode" x17, "phone number" x16, "reference number" x8, "their phone number" x6, "their address" x5, "your reference number" x3, "their postcode" x2
2. size 48: "today" x8, "a great day" x7, "day" x4, "what time" x4, "what day" x3, "time" x3, "great day" x3, "duration" x2
3. size 31: "your criteria" x3, "confusion" x3, "your party" x3, "your needs" x2, "information" x2, "your stay" x2, "your search" x2, "your requirements" x2
4. size 30: "your help" x4, "information" x4, "any information" x2, "your request" x2, "your criteria" x2, "some info" x1, "recommendation" x1, "your visit" x1
5. size 28: "reference number" x16, "your reference number" x4, "contact number" x2, "your confirmation number" x1, "reservation number" x1, "confirmation code" x1, "number" x1, "your contact number" x1
6. size 28: "free wifi" x10, "free parking" x9, "free internet" x3, "parking" x3, "wifi" x2, "free wi" x1
7. size 22: "tr9016" x4, "tr5921" x3, "tr9448" x2, "tr5713" x2, "tr7213" x1, "tr6193" x1, "tr4669" x1, "tr2912" x1
8. size 22: "all" x12, "one" x7, "first" x1, "all the information" x1, "any" x1
9. size 20: "one" x13, "first" x4, "1" x1, "unit" x1, "how about cafe uno" x1
10. size 20: "01223367660" x2, "01223 249955" x1, "01223314960" x1, "07083984796" x1, "01223" x1, "01223412299" x1, "01223311911" x1, "07633256482" x1

### union(GLiNER 0.5, spaCy)

1. size 92: "address" x26, "postcode" x17, "phone number" x16, "reference number" x8, "their phone number" x6, "their address" x5, "your reference number" x3, "their postcode" x2
2. size 48: "today" x8, "a great day" x7, "day" x4, "what time" x4, "what day" x3, "time" x3, "great day" x3, "duration" x2
3. size 31: "your criteria" x3, "confusion" x3, "your party" x3, "your needs" x2, "information" x2, "your stay" x2, "your search" x2, "your requirements" x2
4. size 30: "your help" x4, "information" x4, "any information" x2, "your request" x2, "your criteria" x2, "some info" x1, "recommendation" x1, "your visit" x1
5. size 28: "reference number" x16, "your reference number" x4, "contact number" x2, "your confirmation number" x1, "reservation number" x1, "confirmation code" x1, "number" x1, "your contact number" x1
6. size 28: "free wifi" x10, "free parking" x9, "free internet" x3, "parking" x3, "wifi" x2, "free wi" x1
7. size 22: "all" x12, "one" x7, "first" x1, "all the information" x1, "any" x1
8. size 20: "01223367660" x2, "01223 249955" x1, "01223314960" x1, "07083984796" x1, "01223 244277" x1, "01223412299" x1, "01223311911" x1, "07633256482" x1
9. size 20: "what type" x9, "type" x4, "what kind" x2, "another type" x2, "different type" x1, "specific type" x1, "certain type" x1
10. size 19: "today" x4, "thanks" x4, "a nice day" x2, "great day" x2, "great help" x1, "good night" x1, "no, thanks" x1, "a great day" x1

## Gold values still missed by the union

- MUL2408: "expensive" (Restaurant price range)
- PMUL3589: "cheap" (Hotel price range)
- PMUL4733: "cheap" (Hotel price range)
