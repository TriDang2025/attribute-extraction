# Step 1b dry run check

**DRY RUN, not a result.** Answers come from a Gemini dry run (prompt and code test only).

## dev50
- model Gemini 3.1 Pro (gemini.google.com web app, Syracuse Edu account, mode 'Pro', temporary chat, default settings) (Gemini web app, by hand), guided JSON False, tokens in/out 8588/4326
- schema and rule errors: 0
- loop-2 labels kept: 25

| heading | keep | rename | merge | flag | new |
|---|---|---|---|---|---|
| train | 12 | 0 | 1 | 3 | 9 |
| hotel | 10 | 2 | 5 | 2 | 8 |
| restaurant | 11 | 1 | 3 | 5 | 8 |

New attributes (name / label / type):
- train: ticket class / ticket class / text
- train: seating preference / seating preference / text
- train: train operator / train operator / text
- train: return date / return date / date
- train: return time / return time / time
- train: ticket type / ticket type / text
- train: passenger type / passenger type / text
- train: discount card / discount card / boolean
- train: route type / route type / text
- hotel: room type / room type / text
- hotel: bed type / bed type / text
- hotel: internet access / internet access / boolean
- hotel: parking available / parking available / boolean
- hotel: breakfast included / breakfast included / boolean
- hotel: pet friendly / pet friendly / boolean
- hotel: wheelchair accessible / wheelchair accessible / boolean
- hotel: smoking allowed / smoking allowed / boolean
- restaurant: dietary restriction / dietary restriction / text
- restaurant: outdoor seating / outdoor seating / boolean
- restaurant: alcohol served / alcohol served / boolean
- restaurant: dress code / dress code / text
- restaurant: wheelchair accessible / wheelchair accessible / boolean
- restaurant: kid friendly / kid friendly / boolean
- restaurant: takeout available / takeout available / boolean
- restaurant: accepted payment / accepted payment / text

## dev50b
- model Gemini 3.1 Pro (gemini.google.com web app, Syracuse Edu account, mode 'Pro', temporary chat, default settings) (Gemini web app, by hand), guided JSON False, tokens in/out 7618/2492
- schema and rule errors: 0
- loop-2 labels kept: 5

| heading | keep | rename | merge | flag | new |
|---|---|---|---|---|---|
| train | 7 | 3 | 0 | 2 | 2 |
| hotel | 9 | 3 | 2 | 3 | 2 |
| restaurant | 4 | 7 | 3 | 4 | 1 |

New attributes (name / label / type):
- train: ticket class / ticket class / text
- train: round trip / return ticket / boolean
- hotel: has parking / free parking / boolean
- hotel: has wifi / free wifi / boolean
- restaurant: vegetarian options / vegetarian options / boolean

