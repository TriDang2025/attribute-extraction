CREATE TABLE "train_booking" (
  "booking_id" INTEGER,
  "total_fee" NUMERIC(10, 2),
  "price_per_ticket" NUMERIC(10, 2),
  "train_id" INTEGER,
  "reference_number" INTEGER,
  "travel_date" TEXT,
  "travel_time" INTERVAL,
  PRIMARY KEY ("booking_id")
);

CREATE TABLE "hotel_booking" (
  "booking_id" INTEGER,
  "hotel_name" TEXT,
  "price_extreme" TEXT,
  "specific_hotel_name" TEXT,
  "star_rating" INTEGER,
  "hotel_number_of_nights" INTEGER,
  "price_range" TEXT,
  "start_date" TEXT,
  "reference_number" INTEGER,
  PRIMARY KEY ("booking_id")
);

CREATE TABLE "restaurant_booking" (
  "booking_id" INTEGER,
  "restaurant_name" TEXT,
  "restaurant_food_type" TEXT,
  "restaurant_location" TEXT,
  "restaurant_address" TEXT,
  "restaurant_phone_number" TEXT,
  "reference_number" INTEGER,
  "reservation_date" TEXT,
  "reservation_time" TIME,
  PRIMARY KEY ("booking_id")
);
