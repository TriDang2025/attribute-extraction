CREATE TABLE "train_journey_details" (
  "train_journey_id" INTEGER,
  "arrival_location" TEXT,
  "departure_location" TEXT,
  "destination_city" TEXT,
  "travel_date" TEXT,
  "star rating" INTEGER,
  "reservation time" TIME,
  "number of tickets" INTEGER,
  "number of trains" INTEGER,
  "train id" INTEGER,
  PRIMARY KEY ("train_journey_id")
);

CREATE TABLE "train_journey_times" (
  "train_journey_time_id" INTEGER,
  "arrival_time" TIME,
  "departure_time" TIME,
  "time_query" TEXT,
  "travel_time" INTERVAL,
  "train_journey_id" INTEGER,
  PRIMARY KEY ("train_journey_time_id"),
  FOREIGN KEY ("train_journey_id") REFERENCES "train_journey_details" ("train_journey_id")
);

CREATE TABLE "train_ticket_pricing" (
  "train_ticket_pricing_id" INTEGER,
  "price_per_ticket" NUMERIC(10, 2),
  "total_fee" NUMERIC(10, 2),
  "train_journey_id" INTEGER,
  PRIMARY KEY ("train_ticket_pricing_id"),
  FOREIGN KEY ("train_journey_id") REFERENCES "train_journey_details" ("train_journey_id")
);

CREATE TABLE "hotel_booking_details" (
  "hotel_booking_id" INTEGER,
  "hotel_location" TEXT,
  "hotel_name" TEXT,
  "location" TEXT,
  "location_description" TEXT,
  "price_range" TEXT,
  "reference_number" INTEGER,
  "specific_hotel_name" TEXT,
  "start_date" TEXT,
  PRIMARY KEY ("hotel_booking_id")
);

CREATE TABLE "hotel_booking_duration" (
  "hotel_booking_duration_id" INTEGER,
  "hotel_number_of_guests" INTEGER,
  "hotel_number_of_nights" INTEGER,
  "hotel_booking_id" INTEGER,
  PRIMARY KEY ("hotel_booking_duration_id"),
  FOREIGN KEY ("hotel_booking_id") REFERENCES "hotel_booking_details" ("hotel_booking_id")
);

CREATE TABLE "restaurant_reservation_details" (
  "restaurant_reservation_id" INTEGER,
  "number_of_options" INTEGER,
  "number_of_people" INTEGER,
  "number_of_results" INTEGER,
  "reference_number" INTEGER,
  "reservation_date" TEXT,
  "restaurant_address" TEXT,
  "restaurant_area" TEXT,
  "restaurant_food_type" TEXT,
  "restaurant_location" TEXT,
  "restaurant_name" TEXT,
  "restaurant_phone_number" TEXT,
  PRIMARY KEY ("restaurant_reservation_id")
);

CREATE TABLE "postal_codes_and_taxi_numbers" (
  "postal_code_taxi_number_id" INTEGER,
  "postcode" INTEGER,
  "taxi_phone_numbers" TEXT,
  "restaurant_reservation_id" INTEGER,
  PRIMARY KEY ("postal_code_taxi_number_id"),
  FOREIGN KEY ("restaurant_reservation_id") REFERENCES "restaurant_reservation_details" ("restaurant_reservation_id")
);
