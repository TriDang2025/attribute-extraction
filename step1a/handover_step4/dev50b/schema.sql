CREATE TABLE "train_journey" (
  "train_journey_id" INTEGER,
  "arrival_station" TEXT,
  "departure_station" TEXT,
  "train_id" INTEGER,
  PRIMARY KEY ("train_journey_id")
);

CREATE TABLE "train_timing" (
  "train_timing_id" INTEGER,
  "arrival_time" TIME,
  "departure_time" TIME,
  "travel_time" INTERVAL,
  "train_journey_id" INTEGER,
  PRIMARY KEY ("train_timing_id"),
  FOREIGN KEY ("train_journey_id") REFERENCES "train_journey" ("train_journey_id")
);

CREATE TABLE "train_booking" (
  "train_booking_id" INTEGER,
  "departure_day" TEXT,
  "number_of_tickets" INTEGER,
  "reference_number" INTEGER,
  "total_fee" NUMERIC(10, 2),
  "train_journey_id" INTEGER,
  PRIMARY KEY ("train_booking_id"),
  FOREIGN KEY ("train_journey_id") REFERENCES "train_journey" ("train_journey_id")
);

CREATE TABLE "hotel_details" (
  "hotel_details_id" INTEGER,
  "hotel_name" TEXT,
  "accommodation_type" TEXT,
  "location" TEXT,
  "phone_number" INTEGER,
  "postcode" INTEGER,
  "reference_number" INTEGER,
  "stars" INTEGER,
  PRIMARY KEY ("hotel_details_id")
);

CREATE TABLE "hotel_booking" (
  "hotel_booking_id" INTEGER,
  "number_of_nights" INTEGER,
  "number_of_people" INTEGER,
  "specific_guesthouse" TEXT,
  "start_date" TEXT,
  "hotel_details_id" INTEGER,
  "restaurant name" TEXT,
  PRIMARY KEY ("hotel_booking_id"),
  FOREIGN KEY ("hotel_details_id") REFERENCES "hotel_details" ("hotel_details_id")
);

CREATE TABLE "restaurant_location" (
  "restaurant_location_id" INTEGER,
  "area" TEXT,
  "restaurant_address" TEXT,
  "restaurant_type" TEXT,
  PRIMARY KEY ("restaurant_location_id")
);

CREATE TABLE "restaurant_reservation" (
  "restaurant_reservation_id" INTEGER,
  "restaurant_name" TEXT,
  "restaurant_phone_number" INTEGER,
  "restaurant_reference_number" INTEGER,
  "restaurant_reservation_time" TIME,
  "restaurant_location_id" INTEGER,
  PRIMARY KEY ("restaurant_reservation_id"),
  FOREIGN KEY ("restaurant_location_id") REFERENCES "restaurant_location" ("restaurant_location_id")
);

CREATE TABLE "restaurant_booking" (
  "restaurant_booking_id" INTEGER,
  "day_of_week" TEXT,
  "number_of_people" INTEGER,
  "reference_number" INTEGER,
  "restaurant_location_id" INTEGER,
  PRIMARY KEY ("restaurant_booking_id"),
  FOREIGN KEY ("restaurant_location_id") REFERENCES "restaurant_location" ("restaurant_location_id")
);

CREATE TABLE "restaurant_cuisine" (
  "restaurant_cuisine_id" INTEGER,
  "food_type" TEXT,
  "price_range_confirmation" TEXT,
  "price_range_question" TEXT,
  "restaurant_location_id" INTEGER,
  PRIMARY KEY ("restaurant_cuisine_id"),
  FOREIGN KEY ("restaurant_location_id") REFERENCES "restaurant_location" ("restaurant_location_id")
);
