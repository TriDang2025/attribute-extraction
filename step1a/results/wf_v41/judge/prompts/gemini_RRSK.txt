You are grading a database schema against a reference schema.

Compare the CANDIDATE with the REFERENCE given below, and only with it. Do not use anything you know about where the data comes from, and do not reward or punish designs that the reference does not cover, except under score 5 (design quality).

Rules for comparing:
- Names do not need to match. A candidate column is right if it means the same as a reference column and sits in a table about the same thing.
- The right meaning in a table about something else is wrong.
- The reference allows these alternatives: booking columns may be in the place table instead of a separate booking table (train, hotel, restaurant); then the booking id and link columns are not needed. Grade against whichever alternative is closest to the candidate.
- Soft links and shared value lists in the reference are optional: a matching one counts as right, a missing one is not counted against the candidate.

Give a score from 1 to 5 for each item, with a one-line reason that names the concrete tables or columns.

1. grouping: are the columns put together into tables the way the reference groups them?
2. names: do the table names, and what one row stands for, fit the reference tables?
3. relationships: are the right tables linked, in the right direction, with the right one-to-many or many-to-many?
4. keys: are the primary keys and the foreign keys right?
5. design_quality: no table mixes two different things, no column mixes two roles, and there are no repeated groups of columns.
6. answerability: for each question below, can one SQL query on the CANDIDATE answer it? Answer "yes", "partly" or "no".
7. overall: how close is the candidate to the reference overall?

Score meanings (items 1-5 and 7):
5 = matches the reference, or differs only in names or in an allowed alternative.
4 = one small error (one column in a wrong table, one missing or wrong key, one wrong link direction).
3 = several small errors, or one big error (two reference tables merged into one, a whole table missing, a main link missing).
2 = several big errors; the main structure is only partly recognisable.
1 = little or nothing matches the reference.

Questions for item 6:
1. Which train did the user book, and for how many people?
2. When does that train leave and arrive, and from where to where?
3. Which hotel did the user book, for which day, for how many nights and for how many people?
4. Which hotels in a given area have free parking, and how many stars do they have?
5. What is the reference number of a restaurant booking, and what is that restaurant's phone number?
6. Which cheap restaurants in the centre serve a given food?
7. Where does a booked taxi go from and to, and what is its phone number and car type?
8. What is the address and entrance fee of an attraction?

REFERENCE (SQL):
CREATE TABLE "train" (
  "Train arrive by" TIME,
  "Train day" TEXT,
  "Train departure" TEXT,
  "Train destination" TEXT,
  "Train leave at" TIME,
  "Train duration" TEXT,
  "Train price" REAL,
  "Train trainid" TEXT,
  PRIMARY KEY ("Train trainid")
);

CREATE TABLE "train_booking" (
  "Train booking id" TEXT,
  "Train booking trainid" TEXT,
  "Train confirmed reference" TEXT,
  "Train requested people" INTEGER,
  PRIMARY KEY ("Train booking id"),
  FOREIGN KEY ("Train booking trainid") REFERENCES "train" ("Train trainid")
);

CREATE TABLE "hotel" (
  "Hotel area" TEXT,
  "Hotel internet" TEXT,
  "Hotel name" TEXT,
  "Hotel parking" TEXT,
  "Hotel price range" TEXT,
  "Hotel stars" INTEGER,
  "Hotel type" TEXT,
  "Hotel address" TEXT,
  "Hotel phone" INTEGER,
  "Hotel postcode" TEXT,
  PRIMARY KEY ("Hotel name")
);

CREATE TABLE "hotel_booking" (
  "Hotel booking id" TEXT,
  "Hotel confirmed name" TEXT,
  "Hotel confirmed reference" TEXT,
  "Hotel requested day" TEXT,
  "Hotel requested people" INTEGER,
  "Hotel requested stay" INTEGER,
  PRIMARY KEY ("Hotel booking id"),
  FOREIGN KEY ("Hotel confirmed name") REFERENCES "hotel" ("Hotel name")
);

CREATE TABLE "restaurant" (
  "Restaurant area" TEXT,
  "Restaurant food" TEXT,
  "Restaurant name" TEXT,
  "Restaurant price range" TEXT,
  "Restaurant address" TEXT,
  "Restaurant phone" INTEGER,
  "Restaurant postcode" TEXT,
  PRIMARY KEY ("Restaurant name")
);

CREATE TABLE "restaurant_booking" (
  "Restaurant booking id" TEXT,
  "Restaurant confirmed name" TEXT,
  "Restaurant confirmed reference" TEXT,
  "Restaurant requested day" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant requested time" TIME,
  PRIMARY KEY ("Restaurant booking id"),
  FOREIGN KEY ("Restaurant confirmed name") REFERENCES "restaurant" ("Restaurant name")
);

CREATE TABLE "taxi" (
  "Taxi ride id" TEXT,
  "Taxi arrive by" TIME,
  "Taxi departure" TEXT,
  "Taxi destination" TEXT,
  "Taxi leave at" TIME,
  "Taxi phone" INTEGER,
  "Taxi type" TEXT,
  PRIMARY KEY ("Taxi ride id")
);

CREATE TABLE "attraction" (
  "Attraction area" TEXT,
  "Attraction name" TEXT,
  "Attraction type" TEXT,
  "Attraction address" TEXT,
  "Attraction entrancefee" TEXT,
  "Attraction openhours" TEXT,
  "Attraction phone" INTEGER,
  "Attraction postcode" TEXT,
  PRIMARY KEY ("Attraction name")
);

CANDIDATE "Schema RRSK" (SQL):
CREATE TABLE "train_time_details" (
  "time_id" INTEGER,
  "arrival_time" TIME,
  "departure_time" TIME,
  "time_query" TEXT,
  "travel_time" INTERVAL,
  PRIMARY KEY ("time_id"),
  FOREIGN KEY ("time_id") REFERENCES "train_booking_details" ("booking_id")
);

CREATE TABLE "train_booking_details" (
  "booking_id" INTEGER,
  "number_of_tickets" INTEGER,
  "price_per_ticket" NUMERIC(10, 2),
  "reference_number" INTEGER,
  "total_fee" NUMERIC(10, 2),
  "train_id" INTEGER,
  "journey_id" INTEGER,
  "time_id" INTEGER,
  PRIMARY KEY ("booking_id"),
  FOREIGN KEY ("journey_id") REFERENCES "train_journey" ("journey_id"),
  FOREIGN KEY ("time_id") REFERENCES "train_time_details" ("time_id")
);

CREATE TABLE "train_journey" (
  "journey_id" INTEGER,
  "arrival_location" TEXT,
  "departure_location" TEXT,
  "destination_city" TEXT,
  "travel_date" TEXT,
  PRIMARY KEY ("journey_id"),
  FOREIGN KEY ("journey_id") REFERENCES "train_booking_details" ("booking_id")
);

CREATE TABLE "hotel_location_price" (
  "location_id" INTEGER,
  "hotel_location" TEXT,
  "price_range" TEXT,
  "star_rating" INTEGER,
  "booking_id" INTEGER,
  PRIMARY KEY ("location_id"),
  FOREIGN KEY ("booking_id") REFERENCES "hotel_booking" ("booking_id")
);

CREATE TABLE "hotel_booking" (
  "booking_id" INTEGER,
  "hotel_name" TEXT,
  "hotel_number_of_guests" INTEGER,
  "hotel_number_of_nights" INTEGER,
  "reference_number" INTEGER,
  "start_date" TEXT,
  PRIMARY KEY ("booking_id"),
  FOREIGN KEY ("booking_id") REFERENCES "hotel_location_price" ("location_id")
);

CREATE TABLE "reservation_details" (
  "reservation_id" INTEGER,
  "reservation_date" TEXT,
  "reservation_time" TIME,
  "taxi_phone_numbers" TEXT,
  "restaurant_id" INTEGER,
  PRIMARY KEY ("reservation_id"),
  FOREIGN KEY ("restaurant_id") REFERENCES "restaurant_details" ("restaurant_id")
);

CREATE TABLE "restaurant_price_food" (
  "price_food_id" INTEGER,
  "price_range" TEXT,
  "restaurant_food_type" TEXT,
  "restaurant_id" INTEGER,
  PRIMARY KEY ("price_food_id"),
  FOREIGN KEY ("restaurant_id") REFERENCES "restaurant_details" ("restaurant_id")
);

CREATE TABLE "restaurant_details" (
  "restaurant_id" INTEGER,
  "restaurant_name" TEXT,
  "restaurant_location" TEXT,
  "restaurant_address" TEXT,
  "restaurant_area" TEXT,
  "restaurant_phone_number" TEXT,
  PRIMARY KEY ("restaurant_id"),
  FOREIGN KEY ("restaurant_id") REFERENCES "reservation_details" ("reservation_id"),
  FOREIGN KEY ("restaurant_id") REFERENCES "restaurant_price_food" ("price_food_id")
);

Answer only with JSON in this shape:
{"code": "RRSK",
 "grouping": {"score": 1-5, "reason": "..."},
 "names": {"score": 1-5, "reason": "..."},
 "relationships": {"score": 1-5, "reason": "..."},
 "keys": {"score": 1-5, "reason": "..."},
 "design_quality": {"score": 1-5, "reason": "..."},
 "answerability": [{"q": 1, "answer": "yes|partly|no", "reason": "..."}, ... 8 items],
 "overall": {"score": 1-5, "reason": "..."}}
