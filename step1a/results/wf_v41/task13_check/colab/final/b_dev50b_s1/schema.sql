CREATE TABLE "train_journey" (
  "train_journey_id" INTEGER,
  "arrival_station" TEXT,
  "departure_station" TEXT,
  "departure_time" TIME,
  "reference_number" INTEGER,
  "total_fee" NUMERIC(10, 2),
  "train_id" INTEGER,
  "travel_time" INTERVAL,
  PRIMARY KEY ("train_journey_id")
);

CREATE TABLE "hotel_booking" (
  "hotel_booking_id" INTEGER,
  "accommodation_type" TEXT,
  "address" TEXT,
  "amenities" TEXT,
  "hotel_name" TEXT,
  "location" TEXT,
  "number_of_nights" INTEGER,
  "number_of_people" INTEGER,
  "phone_number" TEXT,
  "postcode" INTEGER,
  "price_adjective" TEXT,
  "reference_number" INTEGER,
  "restaurant_name" TEXT,
  "specific_guesthouse" TEXT,
  "stars" INTEGER,
  "start_date" TEXT,
  PRIMARY KEY ("hotel_booking_id")
);

CREATE TABLE "restaurant_reservation" (
  "restaurant_reservation_id" INTEGER,
  "area" TEXT,
  "day_of_week" TEXT,
  "food_type" TEXT,
  "price_range_confirmation" TEXT,
  "reference_number" INTEGER,
  "restaurant_name" TEXT,
  "restaurant_phone_number" TEXT,
  "restaurant_postcode" TEXT,
  "restaurant_reference_number" INTEGER,
  "restaurant_reservation_time" TIME,
  "restaurant_type" TEXT,
  PRIMARY KEY ("restaurant_reservation_id")
);
