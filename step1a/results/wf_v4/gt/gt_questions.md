# GT questions for the user

- Column 'Hotel internet' (hotel) has type 'unknown'. Which type is right? It is not scored now.
- Column 'Hotel parking' (hotel) has type 'unknown'. Which type is right? It is not scored now.
- Column 'Hotel confirmed name' (hotel_booking) has type 'unknown'. Which type is right? It is not scored now.
- Column 'Restaurant confirmed name' (restaurant_booking) has type 'unknown'. Which type is right? It is not scored now.
- Table 'taxi' (taxi) has no Step-3 handover, so none of its 7 columns can be found. Keep it in the full GT only?
- Column 'Attraction openhours' (attraction) has type 'unknown'. Which type is right? It is not scored now.
- Table 'attraction' (attraction) has no Step-3 handover, so none of its 8 columns can be found. Keep it in the full GT only?
- Link column 'Hotel confirmed name' (hotel_booking) is a real attribute with 0 mentions and no MultiWOZ slot. Should it count as a GT attribute, and should it be dropped when the booking columns move into the place table (done now)?
- Link column 'Restaurant confirmed name' (restaurant_booking) is a real attribute with 0 mentions and no MultiWOZ slot. Should it count as a GT attribute, and should it be dropped when the booking columns move into the place table (done now)?
- Column 'Hotel internet' (hotel) has 0 mentions in dev50 and dev50b, so it can never be found. Keep it in the GT?
- Column 'Hotel parking' (hotel) has 0 mentions in dev50 and dev50b, so it can never be found. Keep it in the GT?
- Column 'Attraction openhours' (attraction) has 0 mentions in dev50 and dev50b, so it can never be found. Keep it in the GT?
- Soft link taxi.Taxi departure -> hotel.Hotel name, restaurant.Restaurant name, attraction.Attraction name: a predicted link here is counted correct, a missing one is not counted. Right?
- Soft link taxi.Taxi destination -> hotel.Hotel name, restaurant.Restaurant name, attraction.Attraction name: a predicted link here is counted correct, a missing one is not counted. Right?
- Shared value sets (area, price range, day) are not scored; an extra lookup table in the output counts as an unmatched table. Right?
- When the booking columns sit in the place table, the booking id and link columns are dropped from the GT; the scorer takes the best of the 8 designs (best grouping F1, then table F1). Right?
