CREATE TABLE "train_booking" (
  "train_booking_id" INTEGER,
  "train_confirmed_reference" INTEGER,
  "train_trainid" INTEGER,
  "train_leave_at" TIME,
  "train_price" NUMERIC(10, 2),
  "train_requested_people" INTEGER,
  PRIMARY KEY ("train_booking_id")
);

CREATE TABLE "hotel_booking" (
  "hotel_booking_id" INTEGER,
  "hotel_address" TEXT,
  "hotel_area" TEXT,
  "hotel_confirmed_reference" INTEGER,
  "hotel_name" TEXT,
  "hotel_phone" INTEGER,
  "hotel_postcode" INTEGER,
  "hotel_price_range" TEXT,
  "hotel_requested_day" TEXT,
  "hotel_requested_people" INTEGER,
  "hotel_requested_stay" INTEGER,
  "hotel_stars" INTEGER,
  "hotel_type" TEXT,
  PRIMARY KEY ("hotel_booking_id")
);

CREATE TABLE "restaurant_booking" (
  "restaurant_booking_id" INTEGER,
  "restaurant_address" TEXT,
  "restaurant_area" TEXT,
  "restaurant_confirmed_reference" INTEGER,
  "restaurant_food" TEXT,
  "restaurant_name" TEXT,
  "restaurant_phone" INTEGER,
  "restaurant_postcode" INTEGER,
  "restaurant_price_range" TEXT,
  "restaurant_requested_day" TEXT,
  "restaurant_requested_people" INTEGER,
  "restaurant_requested_time" TIME,
  PRIMARY KEY ("restaurant_booking_id")
);
