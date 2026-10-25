# Step 2 window examples

Best setting: k=2 lr, beta=0.5, alpha=0.2, t=0.35. Windows shown for k=2, lr (lr: left | right). Cluster = its majority gold class and size; before = reference (no window).

- "Cambridge" (Train departure) [still wrong]
  - window: `to leave <<[TEXT]>>` | `<<[TEXT]>> on [DAY].`
  - before: Train destination (size 47); after: Train destination (size 47)
- "Stansted airport" (Train destination) [still wrong]
  - window: `train to <<[TEXT]>>` | `<<[TEXT]>> , arriving`
  - before: Train departure (size 39); after: Train departure (size 39)
- "20:45" (Train leave at) [right both]
  - window: `leaves at <<[TIME]>>` | `<<[TIME]>> from [TEXT]`
  - before: Train leave at (size 34); after: Train leave at (size 34)
- "20:30" (Train arrive by) [still wrong]
  - window: `arriving by <<[TIME]>>` | `<<[TIME]>> .`
  - before: Train leave at (size 34); after: Train leave at (size 34)
- "3" (Hotel requested people) [FIXED]
  - window: `available for <<[NUMBER]>>` | `<<[NUMBER]>> people staying`
  - before: Hotel requested stay (size 16); after: Hotel requested people (size 11)
- "2" (Hotel requested stay) [BROKEN]
  - window: `moderately priced <<[NUMBER]>>` | `<<[NUMBER]>> -star hotel`
  - before: Hotel requested stay (size 11); after: Hotel stars (size 7)
- "3" (Hotel stars) [FIXED]
  - window: `about the <<[NUMBER]>>` | `<<[NUMBER]>> -star lodging`
  - before: Hotel requested stay (size 16); after: Hotel stars (size 7)
- "abbey pool and astroturf pitch" (Attraction name) [FIXED]
  - window: `is the <<[TEXT]>>` | `<<[TEXT]>> would you`
  - before: Attraction type (size 18); after: Attraction name (size 10)
- "east" (Attraction area) [right both]
  - window: `on the <<[TEXT]>>` | `<<[TEXT]>> side of`
  - before: Attraction area (size 10); after: Attraction area (size 13)
- "Cambridge" (Train departure) [still wrong]
  - window: `arrive in <<[TEXT]>>` | `<<[TEXT]>> at 20:08`
  - before: Train destination (size 47); after: Train destination (size 47)
