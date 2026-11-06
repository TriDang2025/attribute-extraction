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
